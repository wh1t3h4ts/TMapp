import hashlib
import os
import json
from pathlib import Path
from typing import Optional
import time

class AuthenticationManager:
    """
    Manages user authentication with master password.
    Security Controls: Spoofing, Elevation of Privilege
    """
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or os.path.expanduser("~/.secure-notes"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.auth_file = self.config_dir / "auth.json"
        self.failed_attempts = 0
        self.lockout_until = 0
        self.MAX_ATTEMPTS = 5
        self.LOCKOUT_DURATION = 300  # 5 minutes
    
    def is_first_run(self) -> bool:
        """Check if this is first time setup."""
        return not self.auth_file.exists()
    
    def setup_password(self, password: str) -> tuple[bool, str]:
        """
        Setup master password on first run.
        Validates password strength.
        """
        is_valid, message = self._validate_password_strength(password)
        if not is_valid:
            return False, message
        
        # Generate salt and hash
        salt = os.urandom(32)
        password_hash = self._hash_password(password, salt)
        
        auth_data = {
            "password_hash": password_hash.hex(),
            "salt": salt.hex(),
            "created_at": time.time()
        }
        
        with open(self.auth_file, 'w') as f:
            json.dump(auth_data, f)
        
        # Secure file permissions (Unix-like systems)
        if os.name != 'nt':
            os.chmod(self.auth_file, 0o600)
        
        return True, "Password setup successful"
    
    def verify_password(self, password: str) -> tuple[bool, str]:
        """
        Verify password against stored hash.
        Implements account lockout on failed attempts.
        """
        # Check lockout
        if time.time() < self.lockout_until:
            remaining = int(self.lockout_until - time.time())
            return False, f"Account locked. Try again in {remaining} seconds"
        
        if not self.auth_file.exists():
            return False, "No password configured"
        
        try:
            with open(self.auth_file, 'r') as f:
                auth_data = json.load(f)
            
            stored_hash = bytes.fromhex(auth_data["password_hash"])
            salt = bytes.fromhex(auth_data["salt"])
            
            computed_hash = self._hash_password(password, salt)
            
            if computed_hash == stored_hash:
                self.failed_attempts = 0
                return True, "Authentication successful"
            else:
                self.failed_attempts += 1
                if self.failed_attempts >= self.MAX_ATTEMPTS:
                    self.lockout_until = time.time() + self.LOCKOUT_DURATION
                    return False, f"Too many failed attempts. Locked for {self.LOCKOUT_DURATION} seconds"
                return False, f"Incorrect password ({self.MAX_ATTEMPTS - self.failed_attempts} attempts remaining)"
        
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def _hash_password(self, password: str, salt: bytes) -> bytes:
        """Hash password with PBKDF2-HMAC-SHA256."""
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    
    def _validate_password_strength(self, password: str) -> tuple[bool, str]:
        """
        Validate password meets security requirements.
        """
        if len(password) < 12:
            return False, "Password must be at least 12 characters"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return False, "Password must contain uppercase, lowercase, digit, and special character"
        
        return True, "Password meets requirements"
    
    def get_salt(self) -> Optional[bytes]:
        """Retrieve salt for encryption key derivation."""
        if not self.auth_file.exists():
            return None
        
        with open(self.auth_file, 'r') as f:
            auth_data = json.load(f)
        return bytes.fromhex(auth_data["salt"])