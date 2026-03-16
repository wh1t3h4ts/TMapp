"""Settings dialog for application preferences."""
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QSpinBox, QCheckBox, QGroupBox, QComboBox)
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Application settings dialog."""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Setup the settings UI."""
        layout = QVBoxLayout(self)
        
        # Security Settings
        security_group = QGroupBox("Security")
        security_layout = QVBoxLayout()
        
        auto_lock_layout = QHBoxLayout()
        auto_lock_layout.addWidget(QLabel("Auto-lock timeout (minutes):"))
        self.auto_lock_spin = QSpinBox()
        self.auto_lock_spin.setRange(0, 60)
        self.auto_lock_spin.setSpecialValueText("Disabled")
        auto_lock_layout.addWidget(self.auto_lock_spin)
        auto_lock_layout.addStretch()
        security_layout.addLayout(auto_lock_layout)
        
        self.clipboard_clear_check = QCheckBox("Clear clipboard on lock")
        security_layout.addWidget(self.clipboard_clear_check)
        
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)
        
        # Backup Settings
        backup_group = QGroupBox("Backup")
        backup_layout = QVBoxLayout()
        
        self.auto_backup_check = QCheckBox("Enable automatic backups")
        backup_layout.addWidget(self.auto_backup_check)
        
        backup_freq_layout = QHBoxLayout()
        backup_freq_layout.addWidget(QLabel("Backup frequency (days):"))
        self.backup_freq_spin = QSpinBox()
        self.backup_freq_spin.setRange(1, 30)
        backup_freq_layout.addWidget(self.backup_freq_spin)
        backup_freq_layout.addStretch()
        backup_layout.addLayout(backup_freq_layout)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # Editor Settings
        editor_group = QGroupBox("Editor")
        editor_layout = QVBoxLayout()
        
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Font size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 24)
        font_size_layout.addWidget(self.font_size_spin)
        font_size_layout.addStretch()
        editor_layout.addLayout(font_size_layout)
        
        self.spell_check = QCheckBox("Enable spell check")
        editor_layout.addWidget(self.spell_check)
        
        self.auto_save_check = QCheckBox("Enable auto-save")
        editor_layout.addWidget(self.auto_save_check)
        
        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self._save_settings)
        btn_save.setDefault(True)
        button_layout.addWidget(btn_save)
        
        layout.addLayout(button_layout)
    
    def _load_settings(self):
        """Load current settings."""
        self.auto_lock_spin.setValue(self.config.get("auto_lock_timeout", 5))
        self.clipboard_clear_check.setChecked(self.config.get("clear_clipboard_on_lock", True))
        self.auto_backup_check.setChecked(self.config.get("auto_backup_enabled", True))
        self.backup_freq_spin.setValue(self.config.get("backup_frequency_days", 7))
        self.font_size_spin.setValue(self.config.get("editor_font_size", 14))
        self.spell_check.setChecked(self.config.get("spell_check_enabled", False))
        self.auto_save_check.setChecked(self.config.get("auto_save_enabled", True))
    
    def _save_settings(self):
        """Save settings to config."""
        self.config.set("auto_lock_timeout", self.auto_lock_spin.value())
        self.config.set("clear_clipboard_on_lock", self.clipboard_clear_check.isChecked())
        self.config.set("auto_backup_enabled", self.auto_backup_check.isChecked())
        self.config.set("backup_frequency_days", self.backup_freq_spin.value())
        self.config.set("editor_font_size", self.font_size_spin.value())
        self.config.set("spell_check_enabled", self.spell_check.isChecked())
        self.config.set("auto_save_enabled", self.auto_save_check.isChecked())
        
        self.config.save()
        logger.info("Settings saved")
        self.accept()
