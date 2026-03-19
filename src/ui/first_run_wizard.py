"""First-run wizard for TMapp password setup."""
import logging
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QCheckBox, QProgressBar,
                              QFrame, QWidget, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

logger = logging.getLogger(__name__)

_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')


class FirstRunWizard(QDialog):
    """Single-window password setup dialog for first-time users."""
    
    wizard_completed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.password_valid = False
        self.requirements_met = {
            'length': False, 'uppercase': False,
            'lowercase': False, 'digit': False, 'special': False
        }
        
        self._setup_ui()
        self._apply_theme()
        
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        
        logger.info("First-run wizard initialized")
    
    def _setup_ui(self):
        """Create the password setup UI."""
        self.setWindowTitle("TMapp - Setup")
        self.setMinimumSize(550, 580)
        self.setMaximumSize(550, 580)
        if os.path.exists(_LOGO_PATH):
            self.setWindowIcon(QIcon(_LOGO_PATH))
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(40, 30, 40, 30)
        
        # Logo
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(_LOGO_PATH) if os.path.exists(_LOGO_PATH) else QPixmap()
        if not pix.isNull():
            logo.setPixmap(pix.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
            logo.setStyleSheet("margin: 8px;")
        else:
            logo.setText("🔐")
            logo.setStyleSheet("font-size: 56px; margin: 8px;")
        
        title = QLabel("Welcome to TMapp")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        
        subtitle = QLabel("Create your master password to secure your notes")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setWordWrap(True)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("separator")
        
        password_label = QLabel("Master Password:")
        password_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        password_container = QHBoxLayout()
        password_container.setSpacing(8)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password (12+ characters)")
        self.password_input.setFont(QFont("Segoe UI", 12))
        self.password_input.setMinimumHeight(44)
        self.password_input.textChanged.connect(self._validate_password)
        
        self.toggle_password_btn = QPushButton("👁️")
        self.toggle_password_btn.setObjectName("toggle_btn")
        self.toggle_password_btn.setFixedSize(44, 44)
        self.toggle_password_btn.setToolTip("Show/hide password")
        self.toggle_password_btn.clicked.connect(self._toggle_password_visibility)
        
        password_container.addWidget(self.password_input)
        password_container.addWidget(self.toggle_password_btn)
        
        strength_layout = QHBoxLayout()
        
        self.strength_bar = QProgressBar()
        self.strength_bar.setMaximum(100)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setMaximumHeight(6)
        
        self.strength_text = QLabel("Weak")
        self.strength_text.setObjectName("strength_text")
        self.strength_text.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.strength_text.setMinimumWidth(70)
        
        strength_layout.addWidget(self.strength_bar, 1)
        strength_layout.addWidget(self.strength_text)
        
        requirements_grid = QGridLayout()
        requirements_grid.setSpacing(6)
        requirements_grid.setContentsMargins(0, 0, 0, 0)
        
        self.req_length = self._create_requirement_label("12+ characters")
        self.req_uppercase = self._create_requirement_label("Uppercase")
        self.req_lowercase = self._create_requirement_label("Lowercase")
        self.req_digit = self._create_requirement_label("Numbers")
        self.req_special = self._create_requirement_label("Special (!@#$)")
        
        requirements_grid.addWidget(self.req_length, 0, 0)
        requirements_grid.addWidget(self.req_digit, 0, 1)
        requirements_grid.addWidget(self.req_uppercase, 1, 0)
        requirements_grid.addWidget(self.req_special, 1, 1)
        requirements_grid.addWidget(self.req_lowercase, 2, 0)
        
        confirm_label = QLabel("Confirm Password:")
        confirm_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        confirm_container = QHBoxLayout()
        confirm_container.setSpacing(8)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Re-enter password")
        self.confirm_input.setFont(QFont("Segoe UI", 12))
        self.confirm_input.setMinimumHeight(44)
        self.confirm_input.textChanged.connect(self._validate_confirmation)
        
        self.toggle_confirm_btn = QPushButton("👁️")
        self.toggle_confirm_btn.setObjectName("toggle_btn")
        self.toggle_confirm_btn.setFixedSize(44, 44)
        self.toggle_confirm_btn.setToolTip("Show/hide password")
        self.toggle_confirm_btn.clicked.connect(self._toggle_confirm_visibility)
        
        confirm_container.addWidget(self.confirm_input)
        confirm_container.addWidget(self.toggle_confirm_btn)
        
        self.match_label = QLabel("")
        self.match_label.setObjectName("match_label")
        self.match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.match_label.setFont(QFont("Segoe UI", 10))
        
        self.acknowledge_cb = QCheckBox("I understand this password cannot be recovered if lost")
        self.acknowledge_cb.setFont(QFont("Segoe UI", 10))
        self.acknowledge_cb.stateChanged.connect(self._update_continue_button)
        
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setObjectName("continue_btn")
        self.continue_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.continue_btn.setMinimumHeight(44)
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self._on_continue)
        
        main_layout.addWidget(logo)
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addWidget(separator)
        main_layout.addSpacing(8)
        main_layout.addWidget(password_label)
        main_layout.addLayout(password_container)
        main_layout.addLayout(strength_layout)
        main_layout.addSpacing(4)
        main_layout.addLayout(requirements_grid)
        main_layout.addSpacing(12)
        main_layout.addWidget(confirm_label)
        main_layout.addLayout(confirm_container)
        main_layout.addWidget(self.match_label)
        main_layout.addSpacing(8)
        main_layout.addWidget(self.acknowledge_cb)
        main_layout.addSpacing(12)
        main_layout.addWidget(self.continue_btn)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def _create_requirement_label(self, text: str) -> QLabel:
        label = QLabel(f"○ {text}")
        label.setObjectName("requirement")
        label.setFont(QFont("Segoe UI", 9))
        label.setMinimumHeight(20)
        return label
    
    def _validate_password(self, password: str):
        self.requirements_met['length'] = len(password) >= 12
        self.requirements_met['uppercase'] = any(c.isupper() for c in password)
        self.requirements_met['lowercase'] = any(c.islower() for c in password)
        self.requirements_met['digit'] = any(c.isdigit() for c in password)
        self.requirements_met['special'] = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password)
        
        self._update_requirement_label(self.req_length, self.requirements_met['length'])
        self._update_requirement_label(self.req_uppercase, self.requirements_met['uppercase'])
        self._update_requirement_label(self.req_lowercase, self.requirements_met['lowercase'])
        self._update_requirement_label(self.req_digit, self.requirements_met['digit'])
        self._update_requirement_label(self.req_special, self.requirements_met['special'])
        
        strength = self._calculate_strength(password)
        self.strength_bar.setValue(strength)
        
        if strength < 40:
            self.strength_text.setText("Weak")
            self.strength_text.setStyleSheet("color: #f85149;")
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: #f85149; }")
        elif strength < 60:
            self.strength_text.setText("Fair")
            self.strength_text.setStyleSheet("color: #d29922;")
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: #d29922; }")
        elif strength < 80:
            self.strength_text.setText("Good")
            self.strength_text.setStyleSheet("color: #e3b341;")
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: #e3b341; }")
        elif strength < 90:
            self.strength_text.setText("Strong")
            self.strength_text.setStyleSheet("color: #3fb950;")
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: #3fb950; }")
        else:
            self.strength_text.setText("Excellent")
            self.strength_text.setStyleSheet("color: #58a6ff;")
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: #58a6ff; }")
        
        self.password_valid = all(self.requirements_met.values())
        self._validate_confirmation(self.confirm_input.text())
        self._update_continue_button()
    
    def _update_requirement_label(self, label: QLabel, met: bool):
        text = label.text()[2:]
        if met:
            label.setText(f"✓ {text}")
            label.setStyleSheet("color: #3fb950;")
        else:
            label.setText(f"○ {text}")
            label.setStyleSheet("color: #8B949E;")
    
    def _calculate_strength(self, password: str) -> int:
        if not password:
            return 0
        strength = 0
        if len(password) >= 8: strength += 15
        if len(password) >= 12: strength += 20
        if len(password) >= 16: strength += 15
        if len(password) >= 20: strength += 10
        if any(c.islower() for c in password): strength += 10
        if any(c.isupper() for c in password): strength += 10
        if any(c.isdigit() for c in password): strength += 10
        if any(not c.isalnum() for c in password): strength += 10
        return min(strength, 100)
    
    def _validate_confirmation(self, confirm_password: str):
        password = self.password_input.text()
        if not confirm_password:
            self.match_label.setText("")
            return
        if password == confirm_password:
            self.match_label.setText("✓ Passwords match")
            self.match_label.setStyleSheet("color: #3fb950;")
        else:
            self.match_label.setText("✗ Passwords do not match")
            self.match_label.setStyleSheet("color: #f85149;")
        self._update_continue_button()
    
    def _update_continue_button(self):
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        can_continue = (
            self.password_valid and
            password == confirm and
            len(confirm) > 0 and
            self.acknowledge_cb.isChecked()
        )
        self.continue_btn.setEnabled(can_continue)
    
    def _toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _toggle_confirm_visibility(self):
        if self.confirm_input.echoMode() == QLineEdit.EchoMode.Password:
            self.confirm_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _on_continue(self):
        password = self.password_input.text()
        if not self.password_valid:
            return
        if password != self.confirm_input.text():
            return
        if not self.acknowledge_cb.isChecked():
            return
        logger.info("Password setup completed")
        self.wizard_completed.emit(password)
        self.accept()
    
    def closeEvent(self, event):
        event.ignore()
    
    def field(self, name: str) -> str:
        if name == "password":
            return self.password_input.text()
        return ""
    
    def _apply_theme(self):
        """Apply dark theme to wizard."""
        self.setStyleSheet("""
        QDialog {
            background-color: #0f1a14;
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

        QLabel#requirement {
            padding: 2px 8px;
            font-size: 12px;
        }

        QLabel#match_label {
            padding: 4px;
            margin-top: 4px;
            font-size: 12px;
        }

        QFrame#separator {
            color: #2a3d24;
            background-color: #2a3d24;
        }

        QLineEdit {
            background-color: #162010;
            color: #f0f7ee;
            border: 1px solid #2a3d24;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
            selection-background-color: #f45e29;
            selection-color: #0f1a14;
        }

        QLineEdit:focus {
            border-color: #f45e29;
            background-color: #1c2a18;
        }

        QLineEdit:hover {
            border-color: #3a5232;
        }

        QPushButton#toggle_btn {
            background-color: #162010;
            border: 1px solid #2a3d24;
            border-radius: 8px;
            font-size: 18px;
            color: #8faa88;
        }

        QPushButton#toggle_btn:hover {
            background-color: #1c2a18;
            border-color: #f45e29;
            color: #f45e29;
        }

        QProgressBar {
            border: none;
            border-radius: 3px;
            background-color: #2a3d24;
            height: 6px;
        }

        QProgressBar::chunk {
            border-radius: 3px;
        }

        QCheckBox {
            color: #8faa88;
            spacing: 8px;
            font-size: 12px;
        }

        QCheckBox:hover {
            color: #f0f7ee;
        }

        QCheckBox::indicator {
            width: 17px;
            height: 17px;
            border: 1px solid #2a3d24;
            border-radius: 4px;
            background-color: #162010;
        }

        QCheckBox::indicator:hover {
            border-color: #f45e29;
        }

        QCheckBox::indicator:checked {
            background-color: #1ed794;
            border-color: #1ed794;
        }

        QPushButton#continue_btn {
            background-color: #f45e29;
            color: #0f1a14;
            border: none;
            border-radius: 8px;
            padding: 10px 32px;
            font-weight: 700;
            font-size: 14px;
        }

        QPushButton#continue_btn:hover {
            background-color: #fd742e;
        }

        QPushButton#continue_btn:pressed {
            background-color: #d94e1f;
        }

        QPushButton#continue_btn:disabled {
            background-color: #1c2a18;
            color: #4a6044;
        }
        """)
