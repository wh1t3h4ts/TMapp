"""Authentication dialog for password entry."""
import logging
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QPushButton, QFrame, QApplication)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

from src.core.auth_manager import AuthenticationManager, AccountLockedError, AuthenticationError

logger = logging.getLogger(__name__)

import sys as _sys

def _resource_path(relative: str) -> str:
    base = getattr(_sys, '_MEIPASS', os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base, relative)

_LOGO_PATH = _resource_path('src/logo.png')


class AuthenticationDialog(QDialog):
    """
    Modal dialog for password authentication.
    This is shown on every app launch - user MUST authenticate to proceed.
    """
    
    authentication_successful = pyqtSignal(bytes)  # Emits encryption key
    
    def __init__(self, auth_manager: AuthenticationManager, parent=None):
        super().__init__(parent)
        
        self.auth_manager = auth_manager
        self.encryption_key = None
        self.entered_password = None  # Store password for migration
        
        self._setup_ui()
        self._apply_theme()
        
        # Make dialog modal and prevent closing
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.CustomizeWindowHint | 
            Qt.WindowType.WindowTitleHint
        )
        
        # Disable close button
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        
        logger.info("Authentication dialog initialized")
    
    def _setup_ui(self):
        """Create authentication dialog UI."""
        self.setWindowTitle("Starlex - Authentication")
        self.setMinimumSize(500, 600)
        self.setMaximumSize(500, 600)
        if os.path.exists(_LOGO_PATH):
            self.setWindowIcon(QIcon(_LOGO_PATH))
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo image — replaces the Starlex text title
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(_LOGO_PATH) if os.path.exists(_LOGO_PATH) else QPixmap()
        if not pix.isNull():
            logo_label.setPixmap(pix.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))
            logo_label.setStyleSheet("margin: 8px 0 16px 0;")
        else:
            logo_label.setText("Starlex")
            logo_label.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
            logo_label.setStyleSheet("margin: 8px 0 16px 0;")
        
        subtitle = QLabel("Secure Notes")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 16))
        subtitle.setStyleSheet("margin-bottom: 32px;")
        
        # Password label
        password_label = QLabel("Enter Your Master Password:")
        password_label.setFont(QFont("Segoe UI", 12))
        password_label.setStyleSheet("margin-top: 16px;")
        
        # Password input with toggle
        password_container = QHBoxLayout()
        password_container.setSpacing(8)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Master password")
        self.password_input.setFont(QFont("Segoe UI", 14))
        self.password_input.setMinimumHeight(48)
        self.password_input.returnPressed.connect(self.attempt_login)
        
        self.toggle_visibility_btn = QPushButton("👁️")
        self.toggle_visibility_btn.setObjectName("toggle_visibility_btn")
        self.toggle_visibility_btn.setFixedSize(48, 48)
        self.toggle_visibility_btn.setToolTip("Show/hide password")
        self.toggle_visibility_btn.clicked.connect(self.toggle_password_visibility)
        
        password_container.addWidget(self.password_input)
        password_container.addWidget(self.toggle_visibility_btn)
        
        # Error message
        self.error_label = QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setVisible(False)
        self.error_label.setMinimumHeight(60)
        
        # Unlock button
        self.unlock_btn = QPushButton("Unlock")
        self.unlock_btn.setObjectName("unlock_btn")
        self.unlock_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.unlock_btn.setMinimumHeight(48)
        self.unlock_btn.clicked.connect(self.attempt_login)
        self.unlock_btn.setDefault(True)
        
        # Bottom actions
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)
        
        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setObjectName("exit_btn")
        self.exit_btn.setFont(QFont("Segoe UI", 11))
        self.exit_btn.clicked.connect(self.exit_application)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.exit_btn)
        bottom_layout.addStretch()
        
        # Add all to main layout
        layout.addStretch()
        layout.addWidget(logo_label)
        layout.addWidget(subtitle)
        layout.addWidget(password_label)
        layout.addLayout(password_container)
        layout.addWidget(self.error_label)
        layout.addSpacing(16)
        layout.addWidget(self.unlock_btn)
        layout.addSpacing(32)
        layout.addLayout(bottom_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Focus password input
        QTimer.singleShot(100, self.password_input.setFocus)
    
    def attempt_login(self):
        """Attempt to authenticate user."""
        password = self.password_input.text()
        
        if not password:
            self.show_error("Please enter your password")
            return
        
        try:
            # Disable UI during verification
            self.set_ui_enabled(False)
            self.unlock_btn.setText("Verifying...")
            self.error_label.setVisible(False)
            
            # Process events to update UI
            QApplication.processEvents()
            
            # Verify password (may take 1-3 seconds due to Argon2id)
            success, key = self.auth_manager.verify_master_password(password)
            
            if success:
                # Success - store key and password, then close dialog
                self.encryption_key = key
                self.entered_password = password  # Store for migration
                self.authentication_successful.emit(key)
                logger.info("Authentication successful")
                self.accept()
        
        except AccountLockedError as e:
            self.show_error(str(e))
            self.set_ui_enabled(False)  # Keep disabled during lockout
            
            # Start timer to re-enable after lockout
            remaining = self.auth_manager.get_lockout_remaining()
            QTimer.singleShot(remaining * 1000, lambda: self.set_ui_enabled(True))
        
        except AuthenticationError as e:
            self.show_error(str(e))
            self.password_input.clear()
            self.password_input.setFocus()
            self.set_ui_enabled(True)
        
        except Exception as e:
            self.show_error("Authentication failed. Please try again.")
            logger.error(f"Authentication error: {e}", exc_info=True)
            self.set_ui_enabled(True)
        
        finally:
            if self.unlock_btn.text() == "Verifying...":
                self.unlock_btn.setText("Unlock")
                self.set_ui_enabled(True)
    
    def show_error(self, message: str):
        """Display error message with animation."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        
        # Shake animation
        self.animate_shake()
    
    def animate_shake(self):
        """Shake animation for failed login."""
        animation = QPropertyAnimation(self, b"pos")
        animation.setDuration(50)
        animation.setLoopCount(3)
        
        current_pos = self.pos()
        animation.setKeyValueAt(0, current_pos)
        animation.setKeyValueAt(0.25, current_pos + QPoint(10, 0))
        animation.setKeyValueAt(0.75, current_pos - QPoint(10, 0))
        animation.setKeyValueAt(1, current_pos)
        
        animation.start()
    
    def toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def get_entered_password(self) -> str:
        """Get the entered password for migration purposes."""
        return self.entered_password
    
    def set_ui_enabled(self, enabled: bool):
        """Enable/disable UI elements."""
        self.password_input.setEnabled(enabled)
        self.unlock_btn.setEnabled(enabled)
        self.toggle_visibility_btn.setEnabled(enabled)
    
    def exit_application(self):
        """Exit application securely."""
        logger.info("User exited from authentication dialog")
        self.reject()
        QApplication.quit()
    
    def closeEvent(self, event):
        """Prevent closing dialog without authentication."""
        event.ignore()  # User must authenticate or exit explicitly
    
    def _apply_theme(self):
        """Apply cyberpunk dark theme to authentication dialog."""
        self.setStyleSheet("""
        QDialog {
            background-color: #05070f;
        }

        QWidget {
            background-color: transparent;
            font-family: 'Segoe UI', 'Inter', system-ui, sans-serif;
        }

        QLabel {
            color: #e2e8f0;
            background: transparent;
        }

        QLabel#subtitle {
            color: #64748b;
            letter-spacing: 0.5px;
        }

        QLineEdit {
            background-color: #0d1117;
            color: #e2e8f0;
            border: 1px solid #2d3f55;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            selection-background-color: #00d4ff;
            selection-color: #05070f;
        }

        QLineEdit:focus {
            border-color: #00d4ff;
            background-color: #111827;
        }

        QLineEdit:hover {
            border-color: #3d5a7a;
        }

        QPushButton#unlock_btn {
            background-color: #00d4ff;
            color: #05070f;
            border: none;
            border-radius: 8px;
            padding: 12px 32px;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.5px;
        }

        QPushButton#unlock_btn:hover {
            background-color: #33ddff;
        }

        QPushButton#unlock_btn:pressed {
            background-color: #0099cc;
        }

        QPushButton#unlock_btn:disabled {
            background-color: #1e293b;
            color: #475569;
        }

        QPushButton#toggle_visibility_btn {
            background-color: #0d1117;
            border: 1px solid #2d3f55;
            border-radius: 8px;
            font-size: 18px;
            color: #64748b;
        }

        QPushButton#toggle_visibility_btn:hover {
            background-color: #111827;
            border-color: #00d4ff;
            color: #00d4ff;
        }

        QPushButton#exit_btn {
            background-color: transparent;
            color: #64748b;
            border: 1px solid #1e293b;
            border-radius: 7px;
            padding: 8px 24px;
            font-size: 12px;
        }

        QPushButton#exit_btn:hover {
            color: #e2e8f0;
            border-color: #2d3f55;
        }

        QLabel#error_label {
            color: #fca5a5;
            background-color: rgba(255, 45, 85, 0.10);
            border: 1px solid rgba(255, 45, 85, 0.40);
            border-radius: 7px;
            padding: 10px 14px;
            font-size: 12px;
        }
        """)