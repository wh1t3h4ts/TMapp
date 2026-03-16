"""Automated backup management."""
import logging
import shutil
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class BackupManager:
    """Manage automated backups of the database."""
    
    def __init__(self, config):
        self.config = config
        self.backup_dir = config.app_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, db_path):
        """Create a timestamped backup of the database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"tmapp_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(db_path, backup_path)
            
            logger.info(f"Backup created: {backup_path}")
            self._cleanup_old_backups()
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count=10):
        """Keep only the most recent backups."""
        try:
            backups = sorted(self.backup_dir.glob("tmapp_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            for old_backup in backups[keep_count:]:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def list_backups(self):
        """List all available backups."""
        try:
            backups = sorted(self.backup_dir.glob("tmapp_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
            return backups
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def restore_backup(self, backup_path, db_path):
        """Restore database from backup."""
        try:
            shutil.copy2(backup_path, db_path)
            logger.info(f"Restored from backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
