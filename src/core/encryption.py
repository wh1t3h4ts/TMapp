"""Encryption service using AES-256-GCM and Argon2id."""
import secrets
import logging
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.exceptions import InvalidTag

logger = logging.getLogger(__name__)


class EncryptionService:
    """Secure encryption service using AES-256-GCM with Argon2id key derivation."""
    
<<<<<<< HEAD
    KEY_SIZE = 32
    SALT_SIZE = 16
    NONCE_SIZE = 12
    TAG_SIZE = 16
    
    # Enhanced Argon2id parameters for better security
    ARGON2_TIME_COST = 3
    ARGON2_MEMORY_COST = 102400  # 100 MB
    ARGON2_LANES = 4
=======
    KEY_SIZE = 32  # 256 bits for AES-256
    SALT_SIZE = 16  # 128 bits
    NONCE_SIZE = 12  # 96 bits (recommended for GCM)
    TAG_SIZE = 16  # 128 bits authentication tag
    
    # Argon2id parameters
    ARGON2_TIME_COST = 2
    ARGON2_MEMORY_COST = 65536  # 64 MB
    ARGON2_LANES = 4  # parallelism
>>>>>>> 07f8357c75001a99bd7ebbb69168f8bb8f818e2d
    
    def __init__(self):
        """Initialize encryption service."""
        self._cached_key: Optional[bytes] = None
        self._cached_salt: Optional[bytes] = None
<<<<<<< HEAD
        self._cached_password: Optional[str] = None  # Store password for decryption
=======
>>>>>>> 07f8357c75001a99bd7ebbb69168f8bb8f818e2d
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
            password_bytes = password.encode('utf-8')
            
            # Create KDF with all required parameters
            kdf = Argon2id(
                salt=salt,
                length=self.KEY_SIZE,
                iterations=self.ARGON2_TIME_COST,
                lanes=self.ARGON2_LANES,
                memory_cost=self.ARGON2_MEMORY_COST
            )
            
            key = kdf.derive(password_bytes)
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
<<<<<<< HEAD
            self._cached_password = password  # Cache password for flexible decryption
=======
>>>>>>> 07f8357c75001a99bd7ebbb69168f8bb8f818e2d
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
<<<<<<< HEAD
            if self._cached_password:
                self._cached_password = None
=======
>>>>>>> 07f8357c75001a99bd7ebbb69168f8bb8f818e2d
            logger.info("Cached key cleared")
        except Exception as e:
            logger.error(f"Error clearing key: {str(e)}")
    
    def encrypt(self, plaintext: str, password: Optional[str] = None) -> bytes:
        """Encrypt plaintext using AES-256-GCM."""
        if not plaintext:
            raise ValueError("Plaintext cannot be empty")
        
        if password:
            key, salt = self.derive_key(password)
        elif self._cached_key and self._cached_salt:
<<<<<<< HEAD
            # Use cached key and salt for all notes in session
=======
>>>>>>> 07f8357c75001a99bd7ebbb69168f8bb8f818e2d
            key = self._cached_key
            salt = self._cached_salt
        else:
            raise ValueError("No password or cached key available")
        
        try:
            nonce = secrets.token_bytes(self.NONCE_SIZE)
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
            encrypted_data = salt + nonce + ciphertext
            logger.info(f"Data encrypted ({len(plaintext)} bytes)")
            return encrypted_data
        
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"Encryption failed: {str(e)}")
        
        finally:
            if password and 'key' in locals():
                key = b'\x00' * len(key)
    
    def decrypt(self, encrypted_data: bytes, password: Optional[str] = None) -> str:
        """Decrypt data encrypted with AES-256-GCM."""
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")
        
        min_length = self.SALT_SIZE + self.NONCE_SIZE + self.TAG_SIZE
        if len(encrypted_data) < min_length:
            raise ValueError(f"Invalid encrypted data: too short")
        
        try:
            salt = encrypted_data[:self.SALT_SIZE]
            nonce = encrypted_data[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
            ciphertext = encrypted_data[self.SALT_SIZE + self.NONCE_SIZE:]
            
<<<<<<< HEAD
            # Always use password-based decryption to handle any salt
            if password:
                key, _ = self.derive_key(password, salt)
            elif self._cached_password:
                # Use cached password to derive key with the note's salt
                key, _ = self.derive_key(self._cached_password, salt)
            else:
                logger.error("No password available for decryption")
                raise ValueError("No password or cached key available")
            
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
=======
            if password:
                key, _ = self.derive_key(password, salt)
            elif self._cached_key and self._cached_salt == salt:
                key = self._cached_key
            else:
                raise ValueError("No password or matching cached key")
            
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            logger.info("Data decrypted")
>>>>>>> 07f8357c75001a99bd7ebbb69168f8bb8f818e2d
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