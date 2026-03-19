"""First-run wizard — mode selection + master password setup + MFA."""
import logging
import os
import secrets
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QCheckBox, QProgressBar,
                              QFrame, QWidget, QGridLayout, QApplication,
                              QStackedWidget)
from PyQt6.QtCore import Qt, QEventLoop, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

logger = logging.getLogger(__name__)

_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')

_SS = """
QMainWindow, QWidget { background-color: #0f1a14; }
QWidget { background-color: transparent; font-family: 'Segoe UI', system-ui, sans-serif; }
QLabel { color: #f0f7ee; background: transparent; }
QLabel#subtitle { color: #8faa88; }
QLabel#requirement { padding: 2px 8px; font-size: 12px; }
QLabel#match_label { padding: 4px; margin-top: 4px; font-size: 12px; }
QFrame#separator { color: #2a3d24; background-color: #2a3d24; }
QLineEdit {
    background-color: #162010; color: #f0f7ee;
    border: 1px solid #2a3d24; border-radius: 8px;
    padding: 10px 14px; font-size: 13px;
    selection-background-color: #f45e29; selection-color: #0f1a14;
}
QLineEdit:focus { border-color: #f45e29; background-color: #1c2a18; }
QLineEdit:hover { border-color: #3a5232; }
QPushButton#toggle_btn {
    background-color: #162010; border: 1px solid #2a3d24;
    border-radius: 8px; font-size: 18px; color: #8faa88;
}
QPushButton#toggle_btn:hover { background-color: #1c2a18; border-color: #f45e29; color: #f45e29; }
QProgressBar { border: none; border-radius: 3px; background-color: #2a3d24; height: 6px; }
QProgressBar::chunk { border-radius: 3px; }
QCheckBox { color: #8faa88; spacing: 8px; font-size: 12px; }
QCheckBox:hover { color: #f0f7ee; }
QCheckBox::indicator {
    width: 17px; height: 17px;
    border: 1px solid #2a3d24; border-radius: 4px; background-color: #162010;
}
QCheckBox::indicator:hover { border-color: #f45e29; }
QCheckBox::indicator:checked { background-color: #1ed794; border-color: #1ed794; }
QPushButton#continue_btn {
    background-color: #f45e29; color: #0f1a14; border: none;
    border-radius: 8px; padding: 10px 32px; font-weight: 700; font-size: 14px;
}
QPushButton#continue_btn:hover { background-color: #fd742e; }
QPushButton#continue_btn:pressed { background-color: #d94e1f; }
QPushButton#continue_btn:disabled { background-color: #1c2a18; color: #4a6044; }
QPushButton#back_btn {
    background-color: transparent; color: #8faa88;
    border: 1px solid #2a3d24; border-radius: 8px;
    padding: 10px 24px; font-size: 13px;
}
QPushButton#back_btn:hover { border-color: #f45e29; color: #f45e29; }
QPushButton#modeCard {
    background-color: #162010; border: 2px solid #2a3d24;
    border-radius: 12px; padding: 20px 16px;
    color: #f0f7ee; font-size: 13px; text-align: center;
}
QPushButton#modeCard:hover { border-color: #f45e29; background-color: #1c2a18; }
QPushButton#modeCard[selected="true"] {
    border-color: #1ed794; background-color: #0d2018;
    color: #1ed794;
}
"""


class FirstRunWizard(QMainWindow):
    """Two-step setup: mode selection → master password."""

    wizard_completed = pyqtSignal(str, str, str)   # password, mode, totp_secret

    class DialogCode:
        Accepted = 1
        Rejected = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.password_valid = False
        self.requirements_met = {
            'length': False, 'uppercase': False,
            'lowercase': False, 'digit': False, 'special': False
        }
        self._result = self.DialogCode.Rejected
        self._selected_mode = "both"

        self._totp_secret = ""

        self.setWindowTitle("TMapp — Setup")
        self.setMinimumSize(500, 500)
        if os.path.exists(_LOGO_PATH):
            self.setWindowIcon(QIcon(_LOGO_PATH))
        self.setStyleSheet(_SS)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._stack.addWidget(self._build_mode_page())      # index 0
        self._stack.addWidget(self._build_password_page())   # index 1
        self._stack.addWidget(self._build_mfa_page())        # index 2

        self.showMaximized()

    # ── helpers ───────────────────────────────────────────────────────────────
    def _centered(self, inner: QWidget) -> QWidget:
        """Wrap inner widget in a horizontally centered layout."""
        outer = QWidget()
        h = QHBoxLayout(outer)
        h.setContentsMargins(0, 0, 0, 0)
        h.addStretch(1)
        h.addWidget(inner, 3)
        h.addStretch(1)
        return outer

    def _logo_label(self) -> QLabel:
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(_LOGO_PATH) if os.path.exists(_LOGO_PATH) else QPixmap()
        if not pix.isNull():
            lbl.setPixmap(pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
        else:
            lbl.setText("🔐")
            lbl.setStyleSheet("font-size: 48px;")
        return lbl

    # ── PAGE 1: mode selection ────────────────────────────────────────────────
    def _build_mode_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 40, 0, 40)

        form = QWidget()
        fl = QVBoxLayout(form)
        fl.setSpacing(20)
        fl.setContentsMargins(0, 0, 0, 0)

        fl.addWidget(self._logo_label())

        title = QLabel("Welcome to TMapp")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        fl.addWidget(title)

        sub = QLabel("Choose how you want to use the app")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Segoe UI", 11))
        fl.addWidget(sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        fl.addWidget(sep)

        fl.addSpacing(8)

        # mode cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self._mode_cards = {}
        modes = [
            ("notes",     "📝",  "Notes Only",       "Secure note-taking\nwith rich editor,\nnotebooks & search"),
            ("passwords", "🔑",  "Passwords Only",   "Encrypted credential\nvault with TOTP\n& password generator"),
            ("both",      "⚡",  "Full Suite",       "Everything — notes\n+ password manager\n(recommended)"),
        ]
        for mode_id, icon, label, desc in modes:
            btn = QPushButton(f"{icon}\n\n{label}\n\n{desc}")
            btn.setObjectName("modeCard")
            btn.setMinimumSize(160, 180)
            btn.setCheckable(False)
            btn.clicked.connect(lambda _, m=mode_id: self._select_mode(m))
            self._mode_cards[mode_id] = btn
            cards_row.addWidget(btn)

        fl.addLayout(cards_row)
        fl.addSpacing(8)

        self._mode_hint = QLabel("Selected: Full Suite (Notes + Passwords)")
        self._mode_hint.setObjectName("subtitle")
        self._mode_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mode_hint.setFont(QFont("Segoe UI", 10))
        fl.addWidget(self._mode_hint)

        fl.addSpacing(16)

        next_btn = QPushButton("Next →")
        next_btn.setObjectName("continue_btn")
        next_btn.setMinimumHeight(44)
        next_btn.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        fl.addWidget(next_btn)

        # pre-select "both"
        self._select_mode("both")

        outer.addStretch()
        outer.addWidget(self._centered(form))
        outer.addStretch()
        return page

    def _select_mode(self, mode: str):
        self._selected_mode = mode
        labels = {"notes": "Notes Only", "passwords": "Passwords Only", "both": "Full Suite (Notes + Passwords)"}
        for m, btn in self._mode_cards.items():
            btn.setProperty("selected", "true" if m == mode else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._mode_hint.setText(f"Selected: {labels.get(mode, mode)}")

    # ── PAGE 2: password setup ────────────────────────────────────────────────
    def _build_password_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 40, 0, 40)

        form = QWidget()
        fl = QVBoxLayout(form)
        fl.setSpacing(14)
        fl.setContentsMargins(0, 0, 0, 0)

        fl.addWidget(self._logo_label())

        title = QLabel("Create Master Password")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        fl.addWidget(title)

        sub = QLabel("This password encrypts all your data — keep it safe")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Segoe UI", 11))
        sub.setWordWrap(True)
        fl.addWidget(sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        fl.addWidget(sep)

        # password field
        fl.addWidget(self._bold_label("Master Password:"))
        pw_row = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password (12+ characters)")
        self.password_input.setMinimumHeight(44)
        self.password_input.textChanged.connect(self._validate_password)
        pw_row.addWidget(self.password_input)
        t1 = QPushButton("👁️")
        t1.setObjectName("toggle_btn")
        t1.setFixedSize(44, 44)
        t1.clicked.connect(self._toggle_password_visibility)
        pw_row.addWidget(t1)
        fl.addLayout(pw_row)

        # strength bar
        s_row = QHBoxLayout()
        self.strength_bar = QProgressBar()
        self.strength_bar.setMaximum(100)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setMaximumHeight(6)
        self.strength_text = QLabel("Weak")
        self.strength_text.setObjectName("strength_text")
        self.strength_text.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.strength_text.setMinimumWidth(70)
        s_row.addWidget(self.strength_bar, 1)
        s_row.addWidget(self.strength_text)
        fl.addLayout(s_row)

        # requirements grid
        grid = QGridLayout()
        grid.setSpacing(6)
        self.req_length    = self._req_lbl("12+ characters")
        self.req_uppercase = self._req_lbl("Uppercase")
        self.req_lowercase = self._req_lbl("Lowercase")
        self.req_digit     = self._req_lbl("Numbers")
        self.req_special   = self._req_lbl("Special (!@#$)")
        grid.addWidget(self.req_length,    0, 0)
        grid.addWidget(self.req_digit,     0, 1)
        grid.addWidget(self.req_uppercase, 1, 0)
        grid.addWidget(self.req_special,   1, 1)
        grid.addWidget(self.req_lowercase, 2, 0)
        fl.addLayout(grid)

        # confirm field
        fl.addWidget(self._bold_label("Confirm Password:"))
        cf_row = QHBoxLayout()
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Re-enter password")
        self.confirm_input.setMinimumHeight(44)
        self.confirm_input.textChanged.connect(self._validate_confirmation)
        cf_row.addWidget(self.confirm_input)
        t2 = QPushButton("👁️")
        t2.setObjectName("toggle_btn")
        t2.setFixedSize(44, 44)
        t2.clicked.connect(self._toggle_confirm_visibility)
        cf_row.addWidget(t2)
        fl.addLayout(cf_row)

        self.match_label = QLabel("")
        self.match_label.setObjectName("match_label")
        self.match_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(self.match_label)

        self.acknowledge_cb = QCheckBox("I understand this password cannot be recovered if lost")
        self.acknowledge_cb.setFont(QFont("Segoe UI", 10))
        self.acknowledge_cb.stateChanged.connect(self._update_continue_button)
        fl.addWidget(self.acknowledge_cb)

        # back / finish buttons
        btn_row = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("back_btn")
        back_btn.setMinimumHeight(44)
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        btn_row.addWidget(back_btn)

        self.continue_btn = QPushButton("Next → Set Up Recovery")
        self.continue_btn.setObjectName("continue_btn")
        self.continue_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.continue_btn.setMinimumHeight(44)
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(lambda: self._stack.setCurrentIndex(2))
        btn_row.addWidget(self.continue_btn)
        fl.addLayout(btn_row)

        outer.addStretch()
        outer.addWidget(self._centered(form))
        outer.addStretch()
        return page

    # ── PAGE 3: MFA setup ───────────────────────────────────────────────────
    def _build_mfa_page(self) -> QWidget:
        import pyotp
        self._totp_secret = pyotp.random_base32()

        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 40, 0, 40)

        form = QWidget()
        fl = QVBoxLayout(form)
        fl.setSpacing(14)
        fl.setContentsMargins(0, 0, 0, 0)

        fl.addWidget(self._logo_label())

        title = QLabel("Set Up Recovery Code")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        fl.addWidget(title)

        sub = QLabel("Scan the QR code with an authenticator app (Google Authenticator, Authy, etc.)\n"
                     "If you ever forget your password, use the 6-digit code to reset it.")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Segoe UI", 10))
        sub.setWordWrap(True)
        fl.addWidget(sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        fl.addWidget(sep)

        # QR code
        self._qr_label = QLabel()
        self._qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qr_label.setMinimumHeight(200)
        fl.addWidget(self._qr_label)
        self._render_qr()

        # manual key
        key_lbl = QLabel("Manual key (if QR doesn't work):")
        key_lbl.setFont(QFont("Segoe UI", 10))
        fl.addWidget(key_lbl)

        key_row = QHBoxLayout()
        self._key_display = QLineEdit(self._totp_secret)
        self._key_display.setReadOnly(True)
        self._key_display.setFont(QFont("Cascadia Code", 11))
        self._key_display.setMinimumHeight(36)
        key_row.addWidget(self._key_display)
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("back_btn")
        copy_btn.setFixedHeight(36)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self._totp_secret))
        key_row.addWidget(copy_btn)
        fl.addLayout(key_row)

        # verify field
        fl.addWidget(self._bold_label("Enter the 6-digit code to verify:"))
        verify_row = QHBoxLayout()
        self._totp_verify_input = QLineEdit()
        self._totp_verify_input.setPlaceholderText("000000")
        self._totp_verify_input.setMaxLength(6)
        self._totp_verify_input.setFont(QFont("Cascadia Code", 16))
        self._totp_verify_input.setMinimumHeight(44)
        self._totp_verify_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._totp_verify_input.textChanged.connect(self._on_totp_verify_changed)
        verify_row.addWidget(self._totp_verify_input)
        fl.addLayout(verify_row)

        self._totp_status = QLabel("")
        self._totp_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._totp_status.setFont(QFont("Segoe UI", 10))
        fl.addWidget(self._totp_status)

        # buttons
        btn_row = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("back_btn")
        back_btn.setMinimumHeight(44)
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        btn_row.addWidget(back_btn)

        self._finish_btn = QPushButton("Finish Setup")
        self._finish_btn.setObjectName("continue_btn")
        self._finish_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._finish_btn.setMinimumHeight(44)
        self._finish_btn.setEnabled(False)
        self._finish_btn.clicked.connect(self._on_continue)
        btn_row.addWidget(self._finish_btn)
        fl.addLayout(btn_row)

        outer.addStretch()
        outer.addWidget(self._centered(form))
        outer.addStretch()
        return page

    def _render_qr(self):
        try:
            import pyotp, qrcode
            from io import BytesIO
            uri = pyotp.totp.TOTP(self._totp_secret).provisioning_uri(
                name="TMapp", issuer_name="TMapp")
            img = qrcode.make(uri)
            buf = BytesIO()
            img.save(buf, format="PNG")
            pix = QPixmap()
            pix.loadFromData(buf.getvalue())
            self._qr_label.setPixmap(
                pix.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation))
        except ImportError:
            self._qr_label.setText("Install 'qrcode[pil]' to see QR code.\nUse the manual key below.")
            self._qr_label.setStyleSheet("color:#8faa88; font-size:11px;")

    def _on_totp_verify_changed(self, code: str):
        if len(code) < 6:
            self._totp_status.setText("")
            self._finish_btn.setEnabled(False)
            return
        try:
            import pyotp
            valid = pyotp.TOTP(self._totp_secret).verify(code.strip(), valid_window=1)
        except Exception:
            valid = False
        if valid:
            self._totp_status.setText("✓ Code verified")
            self._totp_status.setStyleSheet("color:#3fb950;")
            self._finish_btn.setEnabled(True)
        else:
            self._totp_status.setText("✗ Invalid code — check your app and try again")
            self._totp_status.setStyleSheet("color:#f85149;")
            self._finish_btn.setEnabled(False)

    @staticmethod
    def _bold_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        return lbl

    @staticmethod
    def _req_lbl(text: str) -> QLabel:
        lbl = QLabel(f"○ {text}")
        lbl.setObjectName("requirement")
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setMinimumHeight(20)
        return lbl

    # ── validation ────────────────────────────────────────────────────────────
    def _validate_password(self, password: str):
        self.requirements_met['length']    = len(password) >= 12
        self.requirements_met['uppercase'] = any(c.isupper() for c in password)
        self.requirements_met['lowercase'] = any(c.islower() for c in password)
        self.requirements_met['digit']     = any(c.isdigit() for c in password)
        self.requirements_met['special']   = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password)

        self._upd_req(self.req_length,    self.requirements_met['length'])
        self._upd_req(self.req_uppercase, self.requirements_met['uppercase'])
        self._upd_req(self.req_lowercase, self.requirements_met['lowercase'])
        self._upd_req(self.req_digit,     self.requirements_met['digit'])
        self._upd_req(self.req_special,   self.requirements_met['special'])

        strength = self._calc_strength(password)
        self.strength_bar.setValue(strength)
        if strength < 40:
            self.strength_text.setText("Weak");     self.strength_text.setStyleSheet("color:#f85149;")
            self.strength_bar.setStyleSheet("QProgressBar::chunk{background:#f85149;}")
        elif strength < 60:
            self.strength_text.setText("Fair");     self.strength_text.setStyleSheet("color:#d29922;")
            self.strength_bar.setStyleSheet("QProgressBar::chunk{background:#d29922;}")
        elif strength < 80:
            self.strength_text.setText("Good");     self.strength_text.setStyleSheet("color:#e3b341;")
            self.strength_bar.setStyleSheet("QProgressBar::chunk{background:#e3b341;}")
        elif strength < 90:
            self.strength_text.setText("Strong");   self.strength_text.setStyleSheet("color:#3fb950;")
            self.strength_bar.setStyleSheet("QProgressBar::chunk{background:#3fb950;}")
        else:
            self.strength_text.setText("Excellent");self.strength_text.setStyleSheet("color:#1ed794;")
            self.strength_bar.setStyleSheet("QProgressBar::chunk{background:#1ed794;}")

        self.password_valid = all(self.requirements_met.values())
        self._validate_confirmation(self.confirm_input.text())
        self._update_continue_button()

    @staticmethod
    def _upd_req(label: QLabel, met: bool):
        text = label.text()[2:]
        label.setText(f"✓ {text}" if met else f"○ {text}")
        label.setStyleSheet("color:#3fb950;" if met else "color:#8B949E;")

    @staticmethod
    def _calc_strength(pw: str) -> int:
        s = 0
        if len(pw) >= 8:  s += 15
        if len(pw) >= 12: s += 20
        if len(pw) >= 16: s += 15
        if len(pw) >= 20: s += 10
        if any(c.islower() for c in pw):    s += 10
        if any(c.isupper() for c in pw):    s += 10
        if any(c.isdigit() for c in pw):    s += 10
        if any(not c.isalnum() for c in pw):s += 10
        return min(s, 100)

    def _validate_confirmation(self, confirm: str):
        pw = self.password_input.text()
        if not confirm:
            self.match_label.setText("")
            return
        if pw == confirm:
            self.match_label.setText("✓ Passwords match")
            self.match_label.setStyleSheet("color:#3fb950;")
        else:
            self.match_label.setText("✗ Passwords do not match")
            self.match_label.setStyleSheet("color:#f85149;")
        self._update_continue_button()

    def _update_continue_button(self):
        pw = self.password_input.text()
        cf = self.confirm_input.text()
        self.continue_btn.setEnabled(
            self.password_valid and pw == cf and len(cf) > 0 and self.acknowledge_cb.isChecked()
        )

    def _toggle_password_visibility(self):
        m = QLineEdit.EchoMode
        self.password_input.setEchoMode(
            m.Normal if self.password_input.echoMode() == m.Password else m.Password)

    def _toggle_confirm_visibility(self):
        m = QLineEdit.EchoMode
        self.confirm_input.setEchoMode(
            m.Normal if self.confirm_input.echoMode() == m.Password else m.Password)

    def _on_continue(self):
        pw = self.password_input.text()
        if not self.password_valid or pw != self.confirm_input.text():
            return
        logger.info(f"Setup completed — mode: {self._selected_mode}")
        self.wizard_completed.emit(pw, self._selected_mode, self._totp_secret)
        self.accept()

    # ── QDialog shim ──────────────────────────────────────────────────────────
    def exec(self) -> int:
        self.show()
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

    def closeEvent(self, event):
        event.accept()
        if hasattr(self, '_event_loop'):
            self._event_loop.quit()
        QApplication.quit()

    def field(self, name: str) -> str:
        if name == "password": return self.password_input.text()
        if name == "mode":     return self._selected_mode
        return ""
