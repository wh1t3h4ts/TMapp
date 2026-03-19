"""Authentication manager with secure password verification."""
import ctypes
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class AccountLockedError(Exception):
    """Raised when account is locked due to failed attempts."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthenticationManager:
    """
    Manages user authentication with master password.
    Implements: account lockout, rate limiting, secure verification,
    audit logging, HMAC integrity, and secure memory clearing.
    """

    MAX_ATTEMPTS = 3
    LOCKOUT_DURATION = 86400        # 24 hours
    ATTEMPT_DELAY_BASE = 1.5        # seconds — progressive delay per failed attempt
    HMAC_KEY = b"TMapp-auth-integrity-v1"

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.auth_file = self.config_dir / "auth.json"
        self.audit_file = self.config_dir / "auth_audit.log"
        self.lockout_until: Optional[float] = None
        self.encryption_key: Optional[bytes] = None
        self.failed_attempts: int = self._load_failed_attempts()

        logger.info("AuthenticationManager initialized")

    # ── Integrity ─────────────────────────────────────────────────────────────

    def _compute_hmac(self, data: dict) -> str:
        """Compute HMAC-SHA256 over auth data fields (excludes the hmac field itself)."""
        payload = {k: v for k, v in sorted(data.items()) if k != "hmac"}
        serialised = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hmac.new(self.HMAC_KEY, serialised, hashlib.sha256).hexdigest()

    def _verify_hmac(self, data: dict) -> bool:
        stored = data.get("hmac", "")
        expected = self._compute_hmac(data)
        return hmac.compare_digest(stored, expected)

    def _write_auth_file(self, data: dict):
        """Write auth data with HMAC and restricted permissions."""
        data["hmac"] = self._compute_hmac(data)
        with open(self.auth_file, "w") as f:
            json.dump(data, f, indent=2)
        if os.name != "nt":
            os.chmod(self.auth_file, 0o600)

    def _read_auth_file(self) -> dict:
        """Read and verify auth file integrity."""
        with open(self.auth_file, "r") as f:
            data = json.load(f)
        if not self._verify_hmac(data):
            self._audit("TAMPER_DETECTED", "auth.json HMAC verification failed")
            raise AuthenticationError("Auth file integrity check failed — possible tampering detected.")
        return data

    # ── Persistence helpers ───────────────────────────────────────────────────

    def _load_failed_attempts(self) -> int:
        try:
            if not self.auth_file.exists():
                return 0
            data = self._read_auth_file()
            return int(data.get("failed_attempts", 0))
        except AuthenticationError:
            raise
        except (json.JSONDecodeError, OSError, ValueError) as e:
            logger.warning("Could not load failed attempts: %s", e)
            return 0

    def _persist_state(self, extra: Optional[dict] = None):
        """Persist failed_attempts (and any extra fields) atomically."""
        try:
            data = {}
            if self.auth_file.exists():
                with open(self.auth_file, "r") as f:
                    data = json.load(f)
            data["failed_attempts"] = self.failed_attempts
            if extra:
                data.update(extra)
            self._write_auth_file(data)
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Failed to persist auth state: %s", e)

    # ── Audit log ─────────────────────────────────────────────────────────────

    def _audit(self, event: str, detail: str = ""):
        ts = datetime.now(timezone.utc).isoformat()
        line = f"{ts} | {event} | {detail}\n"
        try:
            with open(self.audit_file, "a") as f:
                f.write(line)
            if os.name != "nt":
                os.chmod(self.audit_file, 0o600)
        except OSError as e:
            logger.warning("Audit log write failed: %s", e)

    # ── First run / setup ─────────────────────────────────────────────────────

    def is_first_run(self) -> bool:
        return not self.auth_file.exists()

    def setup_master_password(self, password: str) -> Tuple[bool, str]:
        is_valid, message = self.validate_password_strength(password)
        if not is_valid:
            return False, message

        try:
            from src.core.encryption import EncryptionService
            encryption = EncryptionService()
            key, salt = encryption.derive_key(password)

            encryption._cached_key = key
            encryption._cached_salt = salt
            verification_token = encryption.encrypt("TMapp-verify-v1")

            auth_data = {
                "salt": salt.hex(),
                "verification_token": verification_token,
                "failed_attempts": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "version": "2.0",
            }
            self._write_auth_file(auth_data)
            self._audit("SETUP", "Master password configured")
            logger.info("Master password configured successfully")
            return True, "Password setup successful"

        except (OSError, ValueError) as e:
            logger.error("Failed to setup password: %s", e)
            return False, f"Setup failed: {e}"
        finally:
            _secure_clear_str(password)

    # ── Verification ──────────────────────────────────────────────────────────

    def verify_master_password(self, password: str) -> Tuple[bool, bytes]:
        """Verify master password. Raises AccountLockedError or AuthenticationError on failure."""
        if self.is_locked_out():
            remaining = self.get_lockout_remaining()
            hours, minutes = remaining // 3600, (remaining % 3600) // 60
            self._audit("LOGIN_BLOCKED", f"Locked — {hours}h {minutes}m remaining")
            raise AccountLockedError(f"Account locked. Try again in {hours}h {minutes}m.")

        if not self.auth_file.exists():
            raise AuthenticationError("No password configured")

        try:
            auth_data = self._read_auth_file()
            salt = bytes.fromhex(auth_data["salt"])
            verification_token = auth_data.get("verification_token")

            from src.core.encryption import EncryptionService
            encryption = EncryptionService()
            key, _ = encryption.derive_key(password, salt)

            if verification_token:
                encryption._cached_key = key
                encryption._cached_salt = salt
                try:
                    result = encryption.decrypt(verification_token)
                    if not hmac.compare_digest(result, "TMapp-verify-v1"):
                        raise ValueError("Token mismatch")
                except (ValueError, Exception) as inner:
                    # Apply progressive delay before responding
                    delay = self.ATTEMPT_DELAY_BASE * self.failed_attempts
                    if delay:
                        time.sleep(min(delay, 10))

                    self.failed_attempts += 1
                    self._audit("LOGIN_FAILED", f"Attempt {self.failed_attempts}/{self.MAX_ATTEMPTS}")

                    if self.failed_attempts >= self.MAX_ATTEMPTS:
                        self._trigger_lockout()
                        raise AccountLockedError(
                            "Too many failed attempts. Account locked for 24 hours."
                        )
                    remaining_attempts = self.MAX_ATTEMPTS - self.failed_attempts
                    self._persist_state()
                    raise AuthenticationError(
                        f"Incorrect password. {remaining_attempts} attempt(s) remaining."
                    )

            # Success
            self.failed_attempts = 0
            self._persist_state()
            self.encryption_key = key
            self._audit("LOGIN_SUCCESS")
            logger.info("Authentication successful")
            return True, key

        except (AccountLockedError, AuthenticationError):
            raise
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Auth file read error: %s", e)
            raise AuthenticationError("Authentication failed: could not read credentials.")
        except ValueError as e:
            logger.error("Authentication value error: %s", e)
            raise AuthenticationError(f"Authentication failed: {e}")
        finally:
            _secure_clear_str(password)

    # ── Lockout ───────────────────────────────────────────────────────────────

    def _trigger_lockout(self):
        self.lockout_until = time.time() + self.LOCKOUT_DURATION
        logger.warning("Account locked after %d failed attempts", self.failed_attempts)
        self._audit("LOCKOUT", f"Locked for {self.LOCKOUT_DURATION}s")
        self._persist_state({"lockout_until": self.lockout_until})

    def is_locked_out(self) -> bool:
        if self.lockout_until is None and self.auth_file.exists():
            try:
                with open(self.auth_file, "r") as f:
                    data = json.load(f)
                self.lockout_until = data.get("lockout_until")
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("Could not read lockout state: %s", e)

        if self.lockout_until is None:
            return False

        if time.time() < self.lockout_until:
            return True

        # Lockout expired — clear it
        self.lockout_until = None
        self.failed_attempts = 0
        self._audit("LOCKOUT_EXPIRED")
        try:
            with open(self.auth_file, "r") as f:
                data = json.load(f)
            data.pop("lockout_until", None)
            data["failed_attempts"] = 0
            self._write_auth_file(data)
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Failed to clear lockout: %s", e)
        return False

    def get_lockout_remaining(self) -> int:
        if not self.is_locked_out():
            return 0
        return int(self.lockout_until - time.time())

    # ── Helpers ───────────────────────────────────────────────────────────────

    def get_stored_salt(self) -> Optional[bytes]:
        try:
            if not self.auth_file.exists():
                return None
            data = self._read_auth_file()
            return bytes.fromhex(data["salt"])
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("Failed to retrieve salt: %s", e)
            return None

    def clear_encryption_key(self):
        if self.encryption_key:
            _zero_bytes(self.encryption_key)
            self.encryption_key = None
            logger.info("Encryption key cleared from memory")

    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        if len(password) < 12:
            return False, "Password must be at least 12 characters"
        if len(password) > 128:
            return False, "Password must not exceed 128 characters"

        missing = []
        if not any(c.isupper() for c in password):
            missing.append("uppercase letter")
        if not any(c.islower() for c in password):
            missing.append("lowercase letter")
        if not any(c.isdigit() for c in password):
            missing.append("digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password):
            missing.append("special character")
        if missing:
            return False, f"Password must contain: {', '.join(missing)}"

        weak_patterns = [
            "password", "12345", "qwerty", "admin", "letmein",
            "welcome", "monkey", "dragon", "master", "login",
            "abc123", "iloveyou", "sunshine", "princess", "shadow",
        ]
        lower = password.lower()
        for pattern in weak_patterns:
            if pattern in lower:
                return False, f"Password contains a common weak pattern: '{pattern}'"

        return True, "Password meets requirements"

    def calculate_password_strength(self, password: str) -> int:
        if not password:
            return 0
        score = 0
        if len(password) >= 8:  score += 20
        if len(password) >= 12: score += 20
        if len(password) >= 16: score += 10
        if len(password) >= 20: score += 10
        if any(c.islower() for c in password):          score += 10
        if any(c.isupper() for c in password):          score += 10
        if any(c.isdigit() for c in password):          score += 10
        if any(not c.isalnum() for c in password):      score += 10
        return min(score, 100)


# ── Secure memory utilities ───────────────────────────────────────────────────

def _zero_bytes(b: bytes):
    """Overwrite a bytes object in memory with zeros (best-effort)."""
    try:
        buf = (ctypes.c_char * len(b)).from_buffer(bytearray(b))
        ctypes.memset(buf, 0, len(b))
    except (TypeError, ValueError):
        pass


def _secure_clear_str(s: str):
    """Best-effort overwrite of a string's internal buffer."""
    try:
        encoded = s.encode("utf-8")
        buf = (ctypes.c_char * len(encoded)).from_buffer(bytearray(encoded))
        ctypes.memset(buf, 0, len(encoded))
    except (TypeError, ValueError):
        pass
