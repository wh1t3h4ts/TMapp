"""
Credential-specific cryptography.

Uses a SEPARATE passphrase from the vault master key so credential data
is independently protected.  All crypto is AES-256-GCM + Argon2id —
the same primitives already in the project, zero new crypto deps.

TOTP requires `pyotp` (added to requirements.txt).
"""
import secrets
import string
import logging
from typing import Optional, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

logger = logging.getLogger(__name__)

# ── Argon2id params (lighter than vault — credentials unlock frequently) ──────
_TIME_COST   = 2
_MEMORY_COST = 65536   # 64 MB
_LANES       = 2
_KEY_SIZE    = 32
_SALT_SIZE   = 16
_NONCE_SIZE  = 12


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = Argon2id(
        salt=salt,
        length=_KEY_SIZE,
        iterations=_TIME_COST,
        lanes=_LANES,
        memory_cost=_MEMORY_COST,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_field(plaintext: str, passphrase: str) -> bytes:
    """Encrypt a single string field.  Returns salt+nonce+ciphertext bytes."""
    if not plaintext:
        return b""
    salt  = secrets.token_bytes(_SALT_SIZE)
    nonce = secrets.token_bytes(_NONCE_SIZE)
    key   = _derive_key(passphrase, salt)
    ct    = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    # zero key immediately
    key = b"\x00" * len(key)
    return salt + nonce + ct


def decrypt_field(blob: bytes, passphrase: str) -> str:
    """Decrypt a blob produced by encrypt_field.  Returns plaintext string."""
    if not blob:
        return ""
    if len(blob) < _SALT_SIZE + _NONCE_SIZE + 16:
        raise ValueError("Credential blob too short — corrupted?")
    salt      = blob[:_SALT_SIZE]
    nonce     = blob[_SALT_SIZE:_SALT_SIZE + _NONCE_SIZE]
    ciphertext = blob[_SALT_SIZE + _NONCE_SIZE:]
    key = _derive_key(passphrase, salt)
    try:
        pt = AESGCM(key).decrypt(nonce, ciphertext, None).decode("utf-8")
    finally:
        key = b"\x00" * len(key)
    return pt


# ── TOTP ──────────────────────────────────────────────────────────────────────
def generate_totp(secret: str) -> Tuple[str, int]:
    """
    Return (current_code, seconds_remaining).
    Requires pyotp.  If not installed returns ("N/A", 0).
    """
    try:
        import pyotp, time
        totp = pyotp.TOTP(secret.strip().upper().replace(" ", ""))
        code = totp.now()
        remaining = 30 - (int(time.time()) % 30)
        return code, remaining
    except ImportError:
        logger.warning("pyotp not installed — TOTP unavailable")
        return "N/A", 0
    except Exception as e:
        logger.error(f"TOTP generation failed: {e}")
        return "ERR", 0


# ── Password generator ────────────────────────────────────────────────────────
_LOWER   = string.ascii_lowercase
_UPPER   = string.ascii_uppercase
_DIGITS  = string.digits
_SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?"


def generate_password(length: int = 20, use_symbols: bool = True) -> str:
    """Generate a cryptographically secure random password."""
    pool = _LOWER + _UPPER + _DIGITS
    if use_symbols:
        pool += _SYMBOLS
    # Guarantee at least one of each required class
    required = [
        secrets.choice(_LOWER),
        secrets.choice(_UPPER),
        secrets.choice(_DIGITS),
    ]
    if use_symbols:
        required.append(secrets.choice(_SYMBOLS))
    rest = [secrets.choice(pool) for _ in range(length - len(required))]
    combined = required + rest
    secrets.SystemRandom().shuffle(combined)
    return "".join(combined)


# ── Password strength ─────────────────────────────────────────────────────────
def password_strength(pw: str) -> Tuple[int, str]:
    """
    Returns (score 0-4, label).
    0=Very Weak, 1=Weak, 2=Fair, 3=Strong, 4=Very Strong
    """
    if not pw:
        return 0, "Empty"
    score = 0
    if len(pw) >= 8:  score += 1
    if len(pw) >= 14: score += 1
    if any(c in _SYMBOLS for c in pw): score += 1
    classes = sum([
        any(c.islower() for c in pw),
        any(c.isupper() for c in pw),
        any(c.isdigit() for c in pw),
    ])
    if classes >= 3: score += 1
    score = min(score, 4)
    labels = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]
    return score, labels[score]
