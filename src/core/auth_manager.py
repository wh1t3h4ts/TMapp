"""Authentication manager with secure password verification."""
import logging
import time
import json
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

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
    Implements security controls: account lockout, rate limiting, secure verification.
    """
    
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 300  # 5 minutes in seconds
    
    def __init__(self, config_dir: Path):
        """Initialize authentication manager."""
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.auth_file = self.config_dir / "auth.json"
        self.failed_attempts = 0
        self.lockout_until = None
        self.encryption_key: Optional[bytes] = None
        
        logger.info("AuthenticationManager initialized")
    
    def is_first_run(self) -> bool:
        """Check if this is first time setup."""
        return not self.auth_file.exists()
    
    def setup_master_password(self, password: str) -> Tuple[bool, str]:
        """
        Setup master password on first run.
        
        Args:
            password: Master password to set
            
        Returns:
            Tuple of (success, message)
        """
        # Validate password strength
        is_valid, message = self.validate_password_strength(password)
        if not is_valid:
            return False, message
        
        try:
            # Use encryption service to derive and store
            from src.core.encryption import EncryptionService
            encryption = EncryptionService()
            
            # Derive key and get salt
            key, salt = encryption.derive_key(password)
            
            # Store authentication data
            auth_data = {
                "salt": salt.hex(),
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(self.auth_file, 'w') as f:
                json.dump(auth_data, f, indent=2)
            
            # Secure file permissions (Unix-like systems)
            import os
            if os.name != 'nt':
                os.chmod(self.auth_file, 0o600)
            
            logger.info("Master password configured successfully")
            return True, "Password setup successful"
        
        except Exception as e:
            logger.error(f"Failed to setup password: {e}")
            return False, f"Setup failed: {str(e)}"
    
    def verify_master_password(self, password: str) -> Tuple[bool, bytes]:
        """
        Verify master password and derive encryption key.
        
        Args:
            password: Password to verify
            
        Returns:
            Tuple of (success, encryption_key or None)
            
        Raises:
            AccountLockedError: If account is locked
            AuthenticationError: If password is incorrect
        """
        # Check lockout status
        if self.is_locked_out():
            remaining = self.get_lockout_remaining()
            raise AccountLockedError(
                f"Account locked due to failed attempts. Try again in {remaining} seconds."
            )
        
        if not self.auth_file.exists():
            raise AuthenticationError("No password configured")
        
        try:
            # Load auth data
            with open(self.auth_file, 'r') as f:
                auth_data = json.load(f)
            
            salt = bytes.fromhex(auth_data["salt"])
            
            # Derive key using same salt
            from src.core.encryption import EncryptionService
            encryption = EncryptionService()
            
            try:
                key, _ = encryption.derive_key(password, salt)
                
                # Success - clear failed attempts
                self.failed_attempts = 0
                self.encryption_key = key
                
                logger.info("Authentication successful")
                return True, key
            
            except Exception as e:
                # Failed attempt
                self.failed_attempts += 1
                
                if self.failed_attempts >= self.MAX_ATTEMPTS:
                    self.trigger_lockout()
                    raise AccountLockedError(
                        f"Too many failed attempts. Account locked for {self.LOCKOUT_DURATION} seconds."
                    )
                
                remaining_attempts = self.MAX_ATTEMPTS - self.failed_attempts
                raise AuthenticationError(
                    f"Invalid password. {remaining_attempts} attempts remaining."
                )
        
        except (AccountLockedError, AuthenticationError):
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    def trigger_lockout(self):
        """Lock account for specified duration."""
        self.lockout_until = time.time() + self.LOCKOUT_DURATION
        logger.warning(
            f"Account locked after {self.failed_attempts} failed attempts. "
            f"Lockout duration: {self.LOCKOUT_DURATION} seconds"
        )
    
    def is_locked_out(self) -> bool:
        """Check if account is currently locked."""
        if self.lockout_until is None:
            return False
        return time.time() < self.lockout_until
    
    def get_lockout_remaining(self) -> int:
        """Get remaining lockout time in seconds."""
        if not self.is_locked_out():
            return 0
        return int(self.lockout_until - time.time())
    
    def get_stored_salt(self) -> Optional[bytes]:
        """Retrieve the stored salt from auth file."""
        try:
            if not self.auth_file.exists():
                return None
            
            with open(self.auth_file, 'r') as f:
                auth_data = json.load(f)
            
            return bytes.fromhex(auth_data["salt"])
        except Exception as e:
            logger.error(f"Failed to retrieve salt: {e}")
            return None
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password meets security requirements.
        
        Requirements:
        - At least 12 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains digit
        - Contains special character
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (valid, message)
        """
        if len(password) < 12:
            return False, "Password must be at least 12 characters"
        
        if len(password) > 128:
            return False, "Password must not exceed 128 characters"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password)
        
        missing = []
        if not has_upper:
            missing.append("uppercase letter")
        if not has_lower:
            missing.append("lowercase letter")
        if not has_digit:
            missing.append("digit")
        if not has_special:
            missing.append("special character")
        
        if missing:
            return False, f"Password must contain: {', '.join(missing)}"
        
        # Check for common weak patterns
        weak_patterns = ['password', '12345', 'qwerty', 'admin', 'letmein']
        password_lower = password.lower()
        for pattern in weak_patterns:
            if pattern in password_lower:
                return False, f"Password contains common weak pattern: {pattern}"
        
        return True, "Password meets requirements"
    
    def calculate_password_strength(self, password: str) -> int:
        """
        Calculate password strength score (0-100).
        
        Args:
            password: Password to evaluate
            
        Returns:
            Strength score from 0 (weak) to 100 (excellent)
        """
        if not password:
            return 0
        
        strength = 0
        
        # Length scoring
        if len(password) >= 8:
            strength += 20
        if len(password) >= 12:
            strength += 20
        if len(password) >= 16:
            strength += 10
        if len(password) >= 20:
            strength += 10
        
        # Character variety
        if any(c.islower() for c in password):
            strength += 10
        if any(c.isupper() for c in password):
            strength += 10
        if any(c.isdigit() for c in password):
            strength += 10
        if any(not c.isalnum() for c in password):
            strength += 10
        
        return min(strength, 100)
    
    def get_stored_salt(self) -> Optional[bytes]:
        """Get stored salt for key derivation."""
        if not self.auth_file.exists():
            return None
        
        try:
            with open(self.auth_file, 'r') as f:
                auth_data = json.load(f)
            return bytes.fromhex(auth_data["salt"])
        except Exception as e:
            logger.error(f"Failed to retrieve salt: {e}")
            return None
    
    def clear_encryption_key(self):
        """Securely clear encryption key from memory."""
        if self.encryption_key:
            # Overwrite with zeros
            self.encryption_key = b'\x00' * len(self.encryption_key)
            self.encryption_key = None
            logger.info("Encryption key cleared from memory")