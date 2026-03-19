"""Encryption service using AES-256-GCM and Argon2id."""
import base64
import secrets
import logging
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.exceptions import InvalidTag

logger = logging.getLogger(__name__)


class EncryptionService:
    """Secure encryption service using AES-256-GCM with Argon2id key derivation."""
    
    KEY_SIZE = 32
    SALT_SIZE = 16
    NONCE_SIZE = 12
    TAG_SIZE = 16
    
    ARGON2_TIME_COST = 3
    ARGON2_MEMORY_COST = 102400  # 100 MB
    ARGON2_LANES = 4
    
    def __init__(self):
        """Initialize encryption service."""
        self._cached_key: Optional[bytes] = None
        self._cached_salt: Optional[bytes] = None
        logger.info("EncryptionService initialized")
    
    def derive_key(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Derive encryption key from password using Argon2id."""
        if not password:
            raise ValueError("Password cannot be empty")
        
        if salt is None:
            salt = secrets.token_bytes(self.SALT_SIZE)
        elif len(salt) != self.SALT_SIZE:
            raise ValueError(f"Salt must be {self.SALT_SIZE} bytes")
        
        try:
            kdf = Argon2id(
                salt=salt,
                length=self.KEY_SIZE,
                iterations=self.ARGON2_TIME_COST,
                lanes=self.ARGON2_LANES,
                memory_cost=self.ARGON2_MEMORY_COST
            )
            key = kdf.derive(password.encode('utf-8'))
            logger.info("Key derived successfully")
            return key, salt
        
        except Exception as e:
            logger.error(f"Key derivation failed: {str(e)}")
            raise ValueError(f"Failed to derive encryption key: {str(e)}")
    
    def cache_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive and cache the encryption key."""
        try:
            self._cached_key, salt_used = self.derive_key(password, salt)
            self._cached_salt = salt_used
            logger.info("Encryption key cached")
            return salt_used
        except Exception as e:
            logger.error(f"Failed to cache key: {str(e)}")
            raise
    
    def clear_cached_key(self):
        """Securely clear cached encryption key."""
        try:
            if self._cached_key:
                self._cached_key = b'\x00' * len(self._cached_key)
                self._cached_key = None
            if self._cached_salt:
                self._cached_salt = b'\x00' * len(self._cached_salt)
                self._cached_salt = None
            logger.info("Cached key cleared")
        except Exception as e:
            logger.error(f"Error clearing key: {str(e)}")
    
    def encrypt(self, plaintext: str, password: Optional[str] = None) -> str:
        """Encrypt plaintext using AES-256-GCM. Returns base64-encoded string."""
        if not plaintext:
            raise ValueError("Plaintext cannot be empty")
        
        if password:
            key, salt = self.derive_key(password)
        elif self._cached_key and self._cached_salt:
            key = self._cached_key
            salt = self._cached_salt
        else:
            raise ValueError("No password or cached key available")
        
        try:
            nonce = secrets.token_bytes(self.NONCE_SIZE)
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
            encrypted_bytes = salt + nonce + ciphertext
            logger.info(f"Data encrypted ({len(plaintext)} bytes)")
            return base64.b64encode(encrypted_bytes).decode('ascii')
        
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"Encryption failed: {str(e)}")
        
        finally:
            if password and 'key' in locals():
                key = b'\x00' * len(key)
    
    def decrypt(self, encrypted_data, password: Optional[str] = None) -> str:
        """Decrypt base64-encoded or raw bytes data encrypted with AES-256-GCM."""
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")

        # Normalise: accept both base64 str and legacy raw bytes
        if isinstance(encrypted_data, str):
            try:
                raw = base64.b64decode(encrypted_data)
            except Exception:
                # Legacy: SQLite stored raw bytes as a latin-1 string
                try:
                    raw = encrypted_data.encode('latin-1')
                except Exception:
                    raise ValueError("Invalid encrypted data: cannot decode")
        else:
            raw = bytes(encrypted_data)
        
        min_length = self.SALT_SIZE + self.NONCE_SIZE + self.TAG_SIZE
        if len(raw) < min_length:
            raise ValueError("Invalid encrypted data: too short")
        
        try:
            salt = raw[:self.SALT_SIZE]
            nonce = raw[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
            ciphertext = raw[self.SALT_SIZE + self.NONCE_SIZE:]
            
            if password:
                key, _ = self.derive_key(password, salt)
            elif self._cached_key and self._cached_salt:
                if salt != self._cached_salt:
                    raise ValueError("Salt mismatch — data was not encrypted with the current key")
                key = self._cached_key
            else:
                logger.error("No password available for decryption")
                raise ValueError("No password or cached key available")
            
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        
        except InvalidTag:
            logger.warning("Decryption failed: wrong password")
            raise ValueError("Decryption failed: incorrect password or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Decryption failed: {str(e)}")
        
        finally:
            if password and 'key' in locals():
                key = b'\x00' * len(key)
    
    def verify_password(self, password: str, salt: bytes) -> bool:
        """Verify if a password matches."""
        try:
            self.derive_key(password, salt)
            return True
        except Exception:
            return False
    
    def __del__(self):
        """Cleanup."""
        self.clear_cached_key()
