import os
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AppConfig:
    """Application configuration manager."""
    
    def __init__(self):
        """Initialize configuration."""
        self.app_dir = Path.home() / ".tmapp"
        self.config_file = self.app_dir / "config.json"
        self.db_file = self.app_dir / "notes.db"
        
        # Default configuration
        self.defaults = {
            "version": "1.0.0",
            "first_run": True,
            "auto_save_interval": 2000,  # ms
            "auto_lock_timeout": 300,  # seconds (5 minutes)
            "default_view": "list",  # list or grid
            "theme": "dark",  # dark or light
            "sidebar_width": 250,
            "notes_panel_width": 300,
            "font_family": "Segoe UI",
            "font_size": 11,
            "editor_font_family": "Consolas",
            "editor_font_size": 11,
            "spell_check": True,
            "default_notebook": "default",
        }
        
        self.config: Dict[str, Any] = {}
        self._ensure_app_directory()
        self.load()
    
    def _ensure_app_directory(self):
        """Create application directory if it doesn't exist."""
        try:
            self.app_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Application directory: {self.app_dir}")
        except Exception as e:
            logger.error(f"Failed to create app directory: {e}")
            raise
    
    def load(self):
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info("Configuration loaded")
            else:
                self.config = self.defaults.copy()
                logger.info("Using default configuration")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = self.defaults.copy()
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
    
    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        return self.config.get("first_run", True)
    
    def mark_initialized(self):
        """Mark application as initialized."""
        self.config["first_run"] = False
        self.save()