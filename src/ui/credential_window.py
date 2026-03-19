"""Standalone password manager window — used when app_mode == 'passwords'."""
import logging
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QFont

from src.ui.credential_panel import CredentialPanel
from src.ui.theme_manager import ThemeManager

logger = logging.getLogger(__name__)

_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')


class CredentialWindow(QMainWindow):
    """Full-screen password manager — mirrors auth dialog layout."""

    def __init__(self, credential_controller, config, master_password=None, parent=None):
        super().__init__(parent)
        self.credential_controller = credential_controller
        self.config = config
        self._master_password = master_password

        self.setWindowTitle("TMapp — Password Manager")
        self.setMinimumSize(400, 400)
        if os.path.exists(_LOGO_PATH):
            self.setWindowIcon(QIcon(_LOGO_PATH))

        self._setup_ui()
        self.setStyleSheet(ThemeManager().get_stylesheet())
        self.showMaximized()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        # ── outer: vertical centering ─────────────────────────────────────────
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── horizontal centering: 1 : 2 : 1 (same as auth dialog) ────────────
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # inner form column
        form = QWidget()
        fl = QVBoxLayout(form)
        fl.setContentsMargins(0, 40, 0, 40)
        fl.setSpacing(12)

        # logo
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(_LOGO_PATH) if os.path.exists(_LOGO_PATH) else QPixmap()
        if not pix.isNull():
            logo.setPixmap(pix.scaled(320, 100,
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
            logo.setStyleSheet("margin: 8px 0 4px 0;")
        else:
            logo.setText("🔑")
            logo.setStyleSheet("font-size: 56px; margin: 8px;")
        fl.addWidget(logo)

        # subtitle
        sub = QLabel("Password Manager")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Segoe UI", 14))
        sub.setStyleSheet("margin-bottom: 20px;")
        fl.addWidget(sub)

        # credential panel (lock screen + vault)
        self.cred_panel = CredentialPanel(self.credential_controller, standalone=True)
        fl.addWidget(self.cred_panel, stretch=1)

        # auto-unlock with master password so user doesn't enter it twice
        if self._master_password:
            self.cred_panel._auto_unlock(self._master_password)

        h.addStretch(1)
        h.addWidget(form, 2)
        h.addStretch(1)

        outer.addStretch(1)
        outer.addLayout(h, stretch=18)
        outer.addStretch(1)

    def closeEvent(self, event):
        event.accept()
        QApplication.quit()
