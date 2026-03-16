"""Note versioning system."""
import logging
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class NoteVersionManager:
    """Manage note versions and history."""
    
    def __init__(self, config):
        self.config = config
        self.versions_dir = config.app_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
    
    def save_version(self, note_id, title, content):
        """Save a version of the note."""
        try:
            note_dir = self.versions_dir / note_id
            note_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            version_file = note_dir / f"version_{timestamp}.json"
            
            version_data = {
                "note_id": note_id,
                "title": title,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Version saved for note {note_id}")
            self._cleanup_old_versions(note_id)
            return True
        except Exception as e:
            logger.error(f"Failed to save version: {e}")
            return False
    
    def get_versions(self, note_id):
        """Get all versions of a note."""
        try:
            note_dir = self.versions_dir / note_id
            if not note_dir.exists():
                return []
            
            versions = []
            for version_file in sorted(note_dir.glob("version_*.json"), reverse=True):
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    versions.append(version_data)
            
            return versions
        except Exception as e:
            logger.error(f"Failed to get versions: {e}")
            return []
    
    def restore_version(self, note_id, timestamp):
        """Restore a specific version of a note."""
        try:
            note_dir = self.versions_dir / note_id
            version_file = note_dir / f"version_{timestamp}.json"
            
            if not version_file.exists():
                return None
            
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            
            return version_data
        except Exception as e:
            logger.error(f"Failed to restore version: {e}")
            return None
    
    def _cleanup_old_versions(self, note_id, keep_count=20):
        """Keep only the most recent versions."""
        try:
            note_dir = self.versions_dir / note_id
            versions = sorted(note_dir.glob("version_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            for old_version in versions[keep_count:]:
                old_version.unlink()
                logger.info(f"Removed old version: {old_version}")
        except Exception as e:
            logger.error(f"Version cleanup failed: {e}")
