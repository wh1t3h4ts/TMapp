"""Database migration utilities for re-encrypting notes."""
import logging
from typing import Optional
from src.core.database import Database
from src.core.encryption import EncryptionService

logger = logging.getLogger(__name__)


class MigrationManager:
    """Handles database migrations and data re-encryption."""
    
    def __init__(self, database: Database, encryption_service: EncryptionService):
        self.db = database
        self.encryption = encryption_service
    
    def reencrypt_all_notes(self, password: str, target_salt: bytes) -> bool:
        """
        Re-encrypt all notes with a consistent salt.
        
        Args:
            password: Master password for decryption/encryption
            target_salt: Target salt to use for all notes
            
        Returns:
            Success status
        """
        try:
            logger.info("Starting note re-encryption migration...")
            
            # Get all notes (encrypted)
            results = self.db.query_all("SELECT id, title, content FROM notes")
            
            if not results:
                logger.info("No notes to migrate")
                return True
            
            migrated_count = 0
            failed_count = 0
            
            for row in results:
                note_id = row['id']
                encrypted_title = row['title']
                encrypted_content = row['content']
                
                try:
                    # Decrypt with password (handles any salt)
                    decrypted_title = self.encryption.decrypt(encrypted_title, password)
                    decrypted_content = self.encryption.decrypt(encrypted_content, password)
                    
                    # Re-encrypt with target salt
                    temp_key = self.encryption._cached_key
                    temp_salt = self.encryption._cached_salt
                    
                    # Set target salt temporarily
                    self.encryption._cached_salt = target_salt
                    key, _ = self.encryption.derive_key(password, target_salt)
                    self.encryption._cached_key = key
                    
                    # Re-encrypt
                    new_encrypted_title = self.encryption.encrypt(decrypted_title)
                    new_encrypted_content = self.encryption.encrypt(decrypted_content)
                    
                    # Update database
                    self.db.execute(
                        "UPDATE notes SET title = ?, content = ? WHERE id = ?",
                        (new_encrypted_title, new_encrypted_content, note_id)
                    )
                    
                    # Restore cached values
                    self.encryption._cached_key = temp_key
                    self.encryption._cached_salt = temp_salt
                    
                    migrated_count += 1
                    logger.debug(f"Re-encrypted note: {note_id}")
                
                except Exception as e:
                    logger.error(f"Failed to re-encrypt note {note_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Migration complete: {migrated_count} notes re-encrypted, {failed_count} failed")
            return failed_count == 0
        
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return False
