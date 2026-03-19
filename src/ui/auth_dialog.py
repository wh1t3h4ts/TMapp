"""Authentication window for password entry."""
import logging
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QLineEdit, QPushButton, QApplication)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

from src.core.auth_manager import AuthenticationManager, AccountLockedError, AuthenticationError

logger = logging.getLogger(__name__)

_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')


class AuthenticationDialog(QMainWindow):
    """
    Standalone authentication window.
    Shown on every app launch — user MUST authenticate to proceed.
    """

    authentication_successful = pyqtSignal(bytes)
    # Mimic QDialog result codes so app.py works unchanged
    class DialogCode:
        Accepted = 1
        Rejected = 0

    def __init__(self, auth_manager: AuthenticationManager, app_mode: str = "both", parent=None):
        super().__init__(parent)

        self.auth_manager = auth_manager
        self.encryption_key = None
        self.entered_password = None
        self._result = self.DialogCode.Rejected
        self._app_mode = app_mode

        self._setup_ui()
        self._apply_theme()
        self.showMaximized()

        logger.info("Authentication window initialized")
    
    def _setup_ui(self):
        """Create authentication window UI."""
        self.setWindowTitle("TMapp — Authentication")
        self.setMinimumSize(400, 400)
        if os.path.exists(_LOGO_PATH):
            self.setWindowIcon(QIcon(_LOGO_PATH))

        central = QWidget()
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)

        # horizontal centering: stretch(1) | form(2) | stretch(1) = 50% width
        h_row = QHBoxLayout()
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(0, 40, 0, 40)

        h_row.addStretch(1)
        h_row.addWidget(form_widget, 2)
        h_row.addStretch(1)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(_LOGO_PATH) if os.path.exists(_LOGO_PATH) else QPixmap()
        if not pix.isNull():
            logo_label.setPixmap(pix.scaled(320, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))
            logo_label.setStyleSheet("margin: 8px 0 16px 0;")

        _SUBTITLES = {
            "notes":     "Secure Notes",
            "passwords": "Password Manager",
            "both":      "Secure Notes",
        }
        subtitle = QLabel(_SUBTITLES.get(self._app_mode, "Secure Notes"))
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

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setObjectName("exit_btn")
        self.exit_btn.setFont(QFont("Segoe UI", 11))
        self.exit_btn.setAutoDefault(False)
        self.exit_btn.clicked.connect(self.exit_application)

        exit_row = QHBoxLayout()
        exit_row.addStretch()
        exit_row.addWidget(self.exit_btn)
        exit_row.addStretch()

        # forgot password link (only shown if MFA was configured)
        self._forgot_btn = QPushButton("Forgot password? Use recovery code")
        self._forgot_btn.setObjectName("forgot_btn")
        self._forgot_btn.setFlat(True)
        self._forgot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._forgot_btn.clicked.connect(self._show_recovery)
        self._forgot_btn.setVisible(self.auth_manager.get_totp_secret() is not None)

        forgot_row = QHBoxLayout()
        forgot_row.addStretch()
        forgot_row.addWidget(self._forgot_btn)
        forgot_row.addStretch()

        form_layout.addStretch()
        form_layout.addWidget(logo_label)
        form_layout.addWidget(subtitle)
        form_layout.addWidget(password_label)
        form_layout.addLayout(password_container)
        form_layout.addWidget(self.error_label)
        form_layout.addSpacing(16)
        form_layout.addWidget(self.unlock_btn)
        form_layout.addSpacing(8)
        form_layout.addLayout(forgot_row)
        form_layout.addSpacing(24)
        form_layout.addLayout(exit_row)
        form_layout.addStretch()

        outer.addLayout(h_row)

        QTimer.singleShot(100, self.password_input.setFocus)
    
    def _show_recovery(self):
        """Show TOTP-based password reset dialog."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
        dlg = QDialog(self)
        dlg.setWindowTitle("Reset Master Password")
        dlg.setMinimumWidth(400)
        dlg.setModal(True)
        dlg.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        lbl_title = QLabel("Reset Master Password")
        lbl_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(lbl_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        layout.addWidget(QLabel("Enter the 6-digit code from your authenticator app:"))
        totp_input = QLineEdit()
        totp_input.setPlaceholderText("000000")
        totp_input.setMaxLength(6)
        totp_input.setFont(QFont("Cascadia Code", 16))
        totp_input.setMinimumHeight(44)
        totp_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(totp_input)

        layout.addWidget(QLabel("New master password:"))
        new_pw = QLineEdit()
        new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        new_pw.setPlaceholderText("12+ characters")
        new_pw.setMinimumHeight(40)
        layout.addWidget(new_pw)

        layout.addWidget(QLabel("Confirm new password:"))
        confirm_pw = QLineEdit()
        confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_pw.setPlaceholderText("Re-enter password")
        confirm_pw.setMinimumHeight(40)
        layout.addWidget(confirm_pw)

        status_lbl = QLabel("")
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_lbl)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("exit_btn")
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)

        reset_btn = QPushButton("Reset Password")
        reset_btn.setObjectName("unlock_btn")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(lambda: self._do_reset(
            dlg, totp_input.text(), new_pw.text(), confirm_pw.text(), status_lbl))
        btn_row.addWidget(reset_btn)
        layout.addLayout(btn_row)

        dlg.exec()

    def _do_reset(self, dlg, code, new_pw, confirm_pw, status_lbl):
        if new_pw != confirm_pw:
            status_lbl.setText("✗ Passwords do not match")
            status_lbl.setStyleSheet("color:#ffb3a0;")
            return
        ok, msg = self.auth_manager.reset_password_with_totp(code, new_pw)
        if ok:
            from PyQt6.QtWidgets import QMessageBox
            dlg.accept()
            QMessageBox.information(self, "Password Reset",
                "Password reset successfully. Please log in with your new password.")
        else:
            status_lbl.setText(f"✗ {msg}")
            status_lbl.setStyleSheet("color:#ffb3a0;")

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
    
    # ── QDialog-compatible API so app.py works unchanged ─────────────────────

    def exec(self) -> int:
        """Show window and block until accepted or rejected."""
        self._loop = QApplication.instance()
        self.show()
        # Spin the event loop until _result is set
        from PyQt6.QtCore import QEventLoop
        self._event_loop = QEventLoop()
        self._event_loop.exec()
        return self._result

    def accept(self):
        self._result = self.DialogCode.Accepted
        self.close()
        if hasattr(self, '_event_loop'):
            self._event_loop.quit()

    def reject(self):
        self._result = self.DialogCode.Rejected
        self.close()
        if hasattr(self, '_event_loop'):
            self._event_loop.quit()

    def exit_application(self):
        """Exit application securely."""
        logger.info("User exited from authentication window")
        self.reject()
        QApplication.quit()

    def closeEvent(self, event):
        """Closing the window exits the app."""
        event.accept()
        if hasattr(self, '_event_loop'):
            self._event_loop.quit()
        QApplication.quit()

    def keyPressEvent(self, event):
        """Block Escape; route Enter to attempt_login."""
        if event.key() == Qt.Key.Key_Escape:
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.attempt_login()
            return
        super().keyPressEvent(event)
    
    def _apply_theme(self):
        """Apply dark theme to authentication window."""
        self.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #080f0a;
            font-family: 'Segoe UI', 'Inter', system-ui, sans-serif;
        }

        QWidget {
            background-color: transparent;
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

        QPushButton#forgot_btn {
            background-color: transparent;
            color: #8faa88;
            border: none;
            font-size: 11px;
            padding: 2px;
        }

        QPushButton#forgot_btn:hover {
            color: #f45e29;
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
