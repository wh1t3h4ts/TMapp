"""
Credential create/edit dialog.

Masked fields reveal on click and auto-hide after 10 s.
Copy buttons clear the clipboard after 30 s.
"""
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QDialogButtonBox,
    QWidget, QProgressBar, QMessageBox, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QClipboard
from PyQt6.QtWidgets import QApplication

from src.controllers.credential_controller import CredentialController
from src.models.credential import Credential
from src.core.credential_crypto import (
    generate_password, password_strength, generate_totp,
)

logger = logging.getLogger(__name__)

_CATEGORIES = ["web", "ssh", "api", "email", "database", "wifi", "other"]
_REVEAL_MS  = 10_000   # auto-hide after 10 s
_CLIP_MS    = 30_000   # clear clipboard after 30 s


class _MaskedField(QWidget):
    """A password-style field with reveal toggle and copy button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.edit = QLineEdit()
        self.edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit.setObjectName("credField")
        layout.addWidget(self.edit, stretch=1)

        self.btn_reveal = QPushButton("👁")
        self.btn_reveal.setObjectName("credIconBtn")
        self.btn_reveal.setFixedSize(28, 28)
        self.btn_reveal.setToolTip("Reveal (auto-hides in 10 s)")
        self.btn_reveal.clicked.connect(self._reveal)
        layout.addWidget(self.btn_reveal)

        self.btn_copy = QPushButton("⎘")
        self.btn_copy.setObjectName("credIconBtn")
        self.btn_copy.setFixedSize(28, 28)
        self.btn_copy.setToolTip("Copy (clears clipboard in 30 s)")
        self.btn_copy.clicked.connect(self._copy)
        layout.addWidget(self.btn_copy)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._hide)

        self._clip_timer = QTimer(self)
        self._clip_timer.setSingleShot(True)
        self._clip_timer.timeout.connect(self._clear_clip)

    def text(self) -> str:
        return self.edit.text()

    def setText(self, v: str):
        self.edit.setText(v)

    def _reveal(self):
        self.edit.setEchoMode(QLineEdit.EchoMode.Normal)
        self._hide_timer.start(_REVEAL_MS)

    def _hide(self):
        self.edit.setEchoMode(QLineEdit.EchoMode.Password)

    def _copy(self):
        cb = QApplication.clipboard()
        cb.setText(self.edit.text())
        self._clip_timer.start(_CLIP_MS)

    def _clear_clip(self):
        cb = QApplication.clipboard()
        if cb.text() == self.edit.text():
            cb.clear()


class CredentialDialog(QDialog):
    """Create or edit a credential entry."""

    def __init__(self, controller: CredentialController,
                 credential: Optional[Credential] = None,
                 parent=None):
        super().__init__(parent)
        self.controller = controller
        self.credential = credential
        self._editing = credential is not None
        self.setWindowTitle("Edit Credential" if self._editing else "New Credential")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        if self._editing:
            self._populate()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(20, 16, 20, 16)

        # ── header ────────────────────────────────────────────────────────────
        hdr = QLabel("Secure Credential")
        hdr.setObjectName("credDialogHeader")
        hdr.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        root.addWidget(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("credSep")
        root.addWidget(sep)

        # ── form ──────────────────────────────────────────────────────────────
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(8)

        self.f_service = QLineEdit()
        self.f_service.setObjectName("credField")
        self.f_service.setPlaceholderText("e.g. GitHub")
        form.addRow("Service:", self.f_service)

        self.f_category = QComboBox()
        self.f_category.setObjectName("credField")
        self.f_category.addItems(_CATEGORIES)
        form.addRow("Category:", self.f_category)

        self.f_url = QLineEdit()
        self.f_url.setObjectName("credField")
        self.f_url.setPlaceholderText("https://")
        form.addRow("URL:", self.f_url)

        self.f_username = _MaskedField()
        form.addRow("Username:", self.f_username)

        # password row with generator
        pw_row = QWidget()
        pw_layout = QHBoxLayout(pw_row)
        pw_layout.setContentsMargins(0, 0, 0, 0)
        pw_layout.setSpacing(4)
        self.f_password = _MaskedField()
        pw_layout.addWidget(self.f_password, stretch=1)
        btn_gen = QPushButton("⚡ Generate")
        btn_gen.setObjectName("credGenBtn")
        btn_gen.setFixedHeight(28)
        btn_gen.setToolTip("Generate a strong random password")
        btn_gen.clicked.connect(self._generate_password)
        pw_layout.addWidget(btn_gen)
        form.addRow("Password:", pw_row)

        # strength bar
        self.strength_bar = QProgressBar()
        self.strength_bar.setObjectName("strengthBar")
        self.strength_bar.setRange(0, 4)
        self.strength_bar.setValue(0)
        self.strength_bar.setFixedHeight(6)
        self.strength_bar.setTextVisible(False)
        self.strength_label = QLabel("—")
        self.strength_label.setObjectName("strengthLabel")
        strength_row = QWidget()
        sl = QHBoxLayout(strength_row)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.addWidget(self.strength_bar, stretch=1)
        sl.addWidget(self.strength_label)
        form.addRow("Strength:", strength_row)
        self.f_password.edit.textChanged.connect(self._update_strength)

        self.f_totp = QLineEdit()
        self.f_totp.setObjectName("credField")
        self.f_totp.setPlaceholderText("Base32 TOTP secret (optional)")
        form.addRow("TOTP Secret:", self.f_totp)

        root.addLayout(form)

        # ── TOTP live display (only shown when secret present) ────────────────
        self.totp_widget = QWidget()
        self.totp_widget.setObjectName("totpWidget")
        self.totp_widget.setVisible(False)
        tl = QHBoxLayout(self.totp_widget)
        tl.setContentsMargins(0, 0, 0, 0)
        self.totp_code_lbl = QLabel("------")
        self.totp_code_lbl.setObjectName("totpCode")
        self.totp_code_lbl.setFont(QFont("Cascadia Code", 18, QFont.Weight.Bold))
        self.totp_timer_lbl = QLabel("")
        self.totp_timer_lbl.setObjectName("totpTimer")
        tl.addWidget(QLabel("TOTP:"))
        tl.addWidget(self.totp_code_lbl)
        tl.addWidget(self.totp_timer_lbl)
        tl.addStretch()
        root.addWidget(self.totp_widget)

        self._totp_refresh = QTimer(self)
        self._totp_refresh.timeout.connect(self._refresh_totp)
        self._totp_refresh.start(1000)
        self.f_totp.textChanged.connect(self._on_totp_changed)

        # ── buttons ───────────────────────────────────────────────────────────
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    # ── Populate for edit ─────────────────────────────────────────────────────
    def _populate(self):
        c = self.credential
        self.f_service.setText(c.service)
        idx = self.f_category.findText(c.category)
        if idx >= 0:
            self.f_category.setCurrentIndex(idx)
        self.f_url.setText(c.url)
        try:
            self.f_username.setText(self.controller.decrypt_username(c))
            self.f_password.setText(self.controller.decrypt_password(c))
            totp_s = self.controller.decrypt_totp_secret(c)
            self.f_totp.setText(totp_s)
        except Exception as e:
            QMessageBox.warning(self, "Decrypt Error", str(e))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _generate_password(self):
        pw = generate_password(20, use_symbols=True)
        self.f_password.setText(pw)
        self.f_password.edit.setEchoMode(QLineEdit.EchoMode.Normal)

    def _update_strength(self, text: str):
        score, label = password_strength(text)
        self.strength_bar.setValue(score)
        self.strength_label.setText(label)
        colors = ["#ff2d55", "#ff6b35", "#ffbe00", "#39ff14", "#00d4ff"]
        self.strength_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {colors[score]}; border-radius: 3px; }}")

    def _on_totp_changed(self, text: str):
        self.totp_widget.setVisible(bool(text.strip()))
        if text.strip():
            self._refresh_totp()

    def _refresh_totp(self):
        secret = self.f_totp.text().strip()
        if not secret or not self.totp_widget.isVisible():
            return
        code, remaining = generate_totp(secret)
        self.totp_code_lbl.setText(code)
        self.totp_timer_lbl.setText(f"({remaining}s)")

    # ── Save ──────────────────────────────────────────────────────────────────
    def _save(self):
        service = self.f_service.text().strip()
        if not service:
            QMessageBox.warning(self, "Validation", "Service name is required.")
            return
        try:
            if self._editing:
                self.controller.update(
                    cred_id=self.credential.id,
                    service=service,
                    username=self.f_username.text(),
                    password=self.f_password.text(),
                    url=self.f_url.text().strip(),
                    category=self.f_category.currentText(),
                    totp_secret=self.f_totp.text().strip(),
                )
            else:
                self.credential = self.controller.create(
                    service=service,
                    username=self.f_username.text(),
                    password=self.f_password.text(),
                    url=self.f_url.text().strip(),
                    category=self.f_category.currentText(),
                    totp_secret=self.f_totp.text().strip(),
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))
