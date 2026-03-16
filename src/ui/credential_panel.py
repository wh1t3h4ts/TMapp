"""
Credential panel — right-sidebar widget.

Shows a lock screen when the vault is locked, a searchable list of
credentials when unlocked, and inline copy/edit/delete actions.
"""
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QInputDialog, QApplication, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from src.controllers.credential_controller import CredentialController
from src.models.credential import Credential
from src.core.credential_crypto import generate_totp

logger = logging.getLogger(__name__)

_CLIP_MS = 30_000


class CredentialPanel(QWidget):
    """Collapsible right-sidebar panel for the secure credential vault."""

    # Emitted when the credential count changes (for status bar)
    count_changed = pyqtSignal(int)

    def __init__(self, controller: CredentialController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("credentialPanel")
        self._clip_timer = QTimer(self)
        self._clip_timer.setSingleShot(True)
        self._clip_timer.timeout.connect(self._clear_clip)
        self._last_clip_text = ""
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # header
        hdr = QWidget()
        hdr.setObjectName("rightPanelHeader")
        hdr.setFixedHeight(44)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 0, 10, 0)
        lbl = QLabel("SECURE VAULT")
        lbl.setObjectName("sidebarSectionLabel")
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        hl.addWidget(lbl)
        hl.addStretch()
        self.btn_add = QPushButton("+")
        self.btn_add.setObjectName("iconButton")
        self.btn_add.setFixedSize(26, 26)
        self.btn_add.setToolTip("New credential")
        self.btn_add.clicked.connect(self._new_credential)
        self.btn_add.setVisible(False)
        hl.addWidget(self.btn_add)
        layout.addWidget(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("sidebarSep")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # ── lock screen ───────────────────────────────────────────────────────
        self.lock_widget = QWidget()
        self.lock_widget.setObjectName("credLockScreen")
        lw = QVBoxLayout(self.lock_widget)
        lw.setContentsMargins(16, 20, 16, 20)
        lw.setSpacing(10)
        lock_icon = QLabel("[LOCKED]")
        lock_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lock_icon.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lw.addWidget(lock_icon)
        lock_msg = QLabel("Enter vault passphrase\nto unlock credentials")
        lock_msg.setObjectName("credLockMsg")
        lock_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lw.addWidget(lock_msg)
        self.passphrase_input = QLineEdit()
        self.passphrase_input.setObjectName("credField")
        self.passphrase_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.passphrase_input.setPlaceholderText("Vault passphrase…")
        self.passphrase_input.returnPressed.connect(self._unlock)
        lw.addWidget(self.passphrase_input)
        btn_unlock = QPushButton("Unlock Vault")
        btn_unlock.setObjectName("credUnlockBtn")
        btn_unlock.clicked.connect(self._unlock)
        lw.addWidget(btn_unlock)
        self.lock_error = QLabel("")
        self.lock_error.setObjectName("credLockError")
        self.lock_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lw.addWidget(self.lock_error)
        lw.addStretch()
        layout.addWidget(self.lock_widget)

        # ── unlocked view ─────────────────────────────────────────────────────
        self.vault_widget = QWidget()
        self.vault_widget.setVisible(False)
        vw = QVBoxLayout(self.vault_widget)
        vw.setContentsMargins(0, 0, 0, 0)
        vw.setSpacing(0)

        # search
        sw = QWidget()
        sw.setObjectName("searchWrap")
        sl = QHBoxLayout(sw)
        sl.setContentsMargins(8, 6, 8, 6)
        self.search_box = QLineEdit()
        self.search_box.setObjectName("panelSearch")
        self.search_box.setPlaceholderText("Filter credentials…")
        self.search_box.setFixedHeight(28)
        self.search_box.textChanged.connect(self._refresh_list)
        sl.addWidget(self.search_box)
        vw.addWidget(sw)

        # list
        self.cred_list = QListWidget()
        self.cred_list.setObjectName("credList")
        self.cred_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cred_list.itemDoubleClicked.connect(self._edit_credential)
        vw.addWidget(self.cred_list, stretch=1)

        # lock button
        btn_lock = QPushButton("🔒  Lock Vault")
        btn_lock.setObjectName("credLockBtn")
        btn_lock.clicked.connect(self._lock)
        vw.addWidget(btn_lock)

        layout.addWidget(self.vault_widget, stretch=1)

    # ── Lock / unlock ─────────────────────────────────────────────────────────
    def _unlock(self):
        pp = self.passphrase_input.text()
        if not pp:
            self.lock_error.setText("Passphrase cannot be empty.")
            return
        # Validate by attempting to decrypt the first credential (if any)
        self.controller.unlock(pp)
        creds = self.controller.get_all()
        if creds:
            try:
                self.controller.decrypt_username(creds[0])
            except Exception:
                self.controller.lock()
                self.lock_error.setText("Wrong passphrase.")
                self.passphrase_input.clear()
                return
        self.lock_error.setText("")
        self.passphrase_input.clear()
        self.lock_widget.setVisible(False)
        self.vault_widget.setVisible(True)
        self.btn_add.setVisible(True)
        self._refresh_list()

    def _lock(self):
        self.controller.lock()
        self.vault_widget.setVisible(False)
        self.lock_widget.setVisible(True)
        self.btn_add.setVisible(False)
        self.cred_list.clear()

    # ── List management ───────────────────────────────────────────────────────
    def _refresh_list(self, query: str = ""):
        self.cred_list.clear()
        creds = (self.controller.search(query)
                 if query else self.controller.get_all())
        for cred in creds:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, cred.id)
            # Build display text — no plaintext passwords in list
            display = f"{cred.service}\n{cred.url or cred.category}"
            item.setText(display)
            item.setToolTip(f"Service: {cred.service}\nURL: {cred.url}")
            self.cred_list.addItem(item)
        self.count_changed.emit(self.controller.count())

    # ── Actions ───────────────────────────────────────────────────────────────
    def _new_credential(self):
        from src.ui.credential_dialog import CredentialDialog
        dlg = CredentialDialog(self.controller, parent=self)
        if dlg.exec():
            self._refresh_list(self.search_box.text())

    def _edit_credential(self, item: QListWidgetItem):
        cred_id = item.data(Qt.ItemDataRole.UserRole)
        cred = self.controller.get(cred_id)
        if not cred:
            return
        from src.ui.credential_dialog import CredentialDialog
        dlg = CredentialDialog(self.controller, credential=cred, parent=self)
        if dlg.exec():
            self._refresh_list(self.search_box.text())

    def _copy_to_clipboard(self, text: str):
        self._last_clip_text = text
        QApplication.clipboard().setText(text)
        self._clip_timer.start(_CLIP_MS)

    def _clear_clip(self):
        if QApplication.clipboard().text() == self._last_clip_text:
            QApplication.clipboard().clear()

    # ── Public API (called from main_window) ──────────────────────────────────
    def refresh(self):
        """Refresh list if vault is unlocked."""
        if self.controller.is_unlocked:
            self._refresh_list(self.search_box.text())
