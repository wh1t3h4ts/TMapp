"""Authentication dialog for password entry."""
import logging
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFrame, QApplication)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

from src.core.auth_manager import AuthenticationManager, AccountLockedError, AuthenticationError

logger = logging.getLogger(__name__)

_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')


class AuthenticationDialog(QDialog):
    """
    Modal dialog for password authentication.
    Shown on every app launch — user MUST authenticate to proceed.
    """
    
    authentication_successful = pyqtSignal(bytes)
    
    def __init__(self, auth_manager: AuthenticationManager, parent=None):
        super().__init__(parent)
        
        self.auth_manager = auth_manager
        self.encryption_key = None
        self.entered_password = None
        
        self._setup_ui()
        self._apply_theme()
        
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        
        logger.info("Authentication dialog initialized")
    
    def _setup_ui(self):
        """Create authentication dialog UI."""
        self.setWindowTitle("TMapp - Authentication")
        self.setMinimumSize(500, 600)
        self.setMaximumSize(500, 600)
        if os.path.exists(_LOGO_PATH):
            self.setWindowIcon(QIcon(_LOGO_PATH))
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(_LOGO_PATH) if os.path.exists(_LOGO_PATH) else QPixmap()
        if not pix.isNull():
            logo_label.setPixmap(pix.scaled(320, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))
            logo_label.setStyleSheet("margin: 8px 0 16px 0;")
        
        subtitle = QLabel("Secure Notes")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 16))
        subtitle.setStyleSheet("margin-bottom: 32px;")
        
        password_label = QLabel("Enter Your Master Password:")
        password_label.setFont(QFont("Segoe UI", 12))
        password_label.setStyleSheet("margin-top: 16px;")
        
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
        self.toggle_visibility_btn.setAutoDefault(False)
        self.toggle_visibility_btn.clicked.connect(self.toggle_password_visibility)
        
        password_container.addWidget(self.password_input)
        password_container.addWidget(self.toggle_visibility_btn)
        
        self.error_label = QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setVisible(False)
        self.error_label.setMinimumHeight(60)
        
        self.unlock_btn = QPushButton("Unlock")
        self.unlock_btn.setObjectName("unlock_btn")
        self.unlock_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.unlock_btn.setMinimumHeight(48)
        self.unlock_btn.setDefault(False)
        self.unlock_btn.setAutoDefault(False)
        self.unlock_btn.clicked.connect(self.attempt_login)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)
        
        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setObjectName("exit_btn")
        self.exit_btn.setFont(QFont("Segoe UI", 11))
        self.exit_btn.setAutoDefault(False)
        self.exit_btn.clicked.connect(self.exit_application)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.exit_btn)
        bottom_layout.addStretch()
        
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
        QTimer.singleShot(100, self.password_input.setFocus)
    
    def attempt_login(self):
        """Attempt to authenticate user."""
        password = self.password_input.text()
        
        if not password:
            remaining = self.auth_manager.MAX_ATTEMPTS - self.auth_manager.failed_attempts
            self.show_error(f"Please enter your password. {remaining} attempt(s) remaining.")
            return
        
        self.set_ui_enabled(False)
        self.unlock_btn.setText("Verifying...")
        self.error_label.setVisible(False)
        QApplication.processEvents()
        
        try:
            success, key = self.auth_manager.verify_master_password(password)
            if success:
                self.encryption_key = key
                self.entered_password = password
                self.authentication_successful.emit(key)
                logger.info("Authentication successful")
                self.accept()
        
        except AccountLockedError as e:
            self.unlock_btn.setText("Unlock")
            self.show_error(str(e))
            # keep UI disabled — account is locked
        
        except AuthenticationError as e:
            self.unlock_btn.setText("Unlock")
            self.show_error(str(e))
            self.password_input.clear()
            self.set_ui_enabled(True)
            self.password_input.setFocus()
        
        except Exception as e:
            self.unlock_btn.setText("Unlock")
            self.show_error("Authentication failed. Please try again.")
            logger.error(f"Authentication error: {e}", exc_info=True)
            self.set_ui_enabled(True)
    
    def show_error(self, message: str):
        """Display error message with animation."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
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
        """Get the entered password."""
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
        event.ignore()

    def keyPressEvent(self, event):
        """Block Escape and Enter from closing the dialog."""
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.attempt_login()
            return
        super().keyPressEvent(event)
    
    def _apply_theme(self):
        """Apply dark theme to authentication dialog."""
        self.setStyleSheet("""
        QDialog {
            background-color: #080f0a;
        }

        QWidget {
            background-color: transparent;
            font-family: 'Segoe UI', 'Inter', system-ui, sans-serif;
        }

        QLabel {
            color: #f0f7ee;
            background: transparent;
        }

        QLabel#subtitle {
            color: #8faa88;
        }

        QLineEdit {
            background-color: #0d1610;
            color: #f0f7ee;
            border: 1px solid #1e2e1a;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            selection-background-color: #f45e29;
            selection-color: #080f0a;
        }

        QLineEdit:focus {
            border-color: #f45e29;
            background-color: #111d13;
        }

        QLineEdit:hover {
            border-color: #2a3d24;
        }

        QPushButton#unlock_btn {
            background-color: #f45e29;
            color: #0f1a14;
            border: none;
            border-radius: 8px;
            padding: 12px 32px;
            font-weight: 700;
            font-size: 14px;
        }

        QPushButton#unlock_btn:hover {
            background-color: #fd742e;
        }

        QPushButton#unlock_btn:pressed {
            background-color: #d94e1f;
        }

        QPushButton#unlock_btn:disabled {
            background-color: #0d1610;
            color: #4a6044;
        }

        QPushButton#toggle_visibility_btn {
            background-color: #0d1610;
            border: 1px solid #1e2e1a;
            border-radius: 8px;
            font-size: 18px;
            color: #8faa88;
        }

        QPushButton#toggle_visibility_btn:hover {
            background-color: #1c2a18;
            border-color: #f45e29;
            color: #f45e29;
        }

        QPushButton#exit_btn {
            background-color: transparent;
            color: #8faa88;
            border: 1px solid #2a3d24;
            border-radius: 7px;
            padding: 8px 24px;
            font-size: 12px;
        }

        QPushButton#exit_btn:hover {
            color: #f0f7ee;
            border-color: #3a5232;
        }

        QLabel#error_label {
            color: #ffb3a0;
            background-color: rgba(248, 81, 73, 0.10);
            border: 1px solid rgba(248, 81, 73, 0.40);
            border-radius: 7px;
            padding: 10px 14px;
            font-size: 12px;
        }
        """)
