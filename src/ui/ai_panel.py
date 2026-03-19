"""AI Assistant panel for the right sidebar."""
import logging
import os
import threading
import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTextEdit, QLineEdit, QFrame,
                              QSizePolicy, QCheckBox)
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class _Worker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, model: str, messages: list):
        super().__init__()
        self.model = model
        self.messages = messages

    def run(self):
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            self.error.emit("OPENAI_API_KEY environment variable is not set.")
            return
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"},
                json={"model": self.model, "messages": self.messages},
                timeout=30,
            )
            resp.raise_for_status()
            self.finished.emit(resp.json()["choices"][0]["message"]["content"])
        except requests.exceptions.HTTPError as e:
            self.error.emit(f"API error: {e.response.status_code} — {e.response.text[:120]}")
        except Exception as e:
            self.error.emit(str(e))


class AIPanel(QWidget):
    """Sidebar AI assistant panel."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("aiPanel")
        self._history: list[dict] = []
        self._note_title = ""
        self._note_content = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # header
        hdr = QWidget()
        hdr.setObjectName("rightPanelHeader")
        hdr.setFixedHeight(44)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(14, 0, 10, 0)
        lbl = QLabel("AI ASSISTANT")
        lbl.setObjectName("sidebarSectionLabel")
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        hdr_l.addWidget(lbl)
        hdr_l.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("iconButton")
        clear_btn.setFixedHeight(24)
        clear_btn.setToolTip("Clear chat history")
        clear_btn.clicked.connect(self._clear_chat)
        hdr_l.addWidget(clear_btn)
        layout.addWidget(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("sidebarSep")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # chat display
        self.chat_area = QTextEdit()
        self.chat_area.setObjectName("aiChatArea")
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Segoe UI", 11))
        self.chat_area.setSizePolicy(QSizePolicy.Policy.Expanding,
                                     QSizePolicy.Policy.Expanding)
        layout.addWidget(self.chat_area, stretch=1)

        # context toggle
        ctx_row = QWidget()
        ctx_l = QHBoxLayout(ctx_row)
        ctx_l.setContentsMargins(10, 4, 10, 0)
        ctx_l.setSpacing(6)
        self.ctx_check = QCheckBox()
        self.ctx_check.setChecked(True)
        ctx_lbl = QLabel("Include current note as context")
        ctx_lbl.setObjectName("aiCtxLabel")
        ctx_lbl.setFont(QFont("Segoe UI", 9))
        ctx_l.addWidget(self.ctx_check)
        ctx_l.addWidget(ctx_lbl)
        ctx_l.addStretch()
        layout.addWidget(ctx_row)

        # input row
        input_row = QWidget()
        input_row.setObjectName("aiInputRow")
        in_l = QHBoxLayout(input_row)
        in_l.setContentsMargins(10, 6, 10, 10)
        in_l.setSpacing(6)
        self.prompt_input = QLineEdit()
        self.prompt_input.setObjectName("aiPromptInput")
        self.prompt_input.setPlaceholderText("Ask anything…")
        self.prompt_input.setFixedHeight(32)
        self.prompt_input.returnPressed.connect(self._send)
        in_l.addWidget(self.prompt_input)
        self.send_btn = QPushButton("Ask")
        self.send_btn.setObjectName("aiAskBtn")
        self.send_btn.setFixedSize(48, 32)
        self.send_btn.clicked.connect(self._send)
        in_l.addWidget(self.send_btn)
        layout.addWidget(input_row)

    def set_note_context(self, title: str, content: str):
        self._note_title = title
        self._note_content = content

    def _clear_chat(self):
        self._history.clear()
        self.chat_area.clear()

    def _send(self):
        prompt = self.prompt_input.text().strip()
        if not prompt:
            return

        self.prompt_input.clear()
        self._append("You", prompt)
        self.send_btn.setEnabled(False)
        self.send_btn.setText("…")

        messages = [{"role": "system",
                     "content": "You are a helpful assistant embedded in a secure note-taking app."}]

        if self.ctx_check.isChecked() and self._note_content:
            messages.append({
                "role": "system",
                "content": f"Current note — '{self._note_title}': {self._note_content[:3000]}"
            })

        messages += self._history
        messages.append({"role": "user", "content": prompt})
        self._history.append({"role": "user", "content": prompt})

        worker = _Worker(self.config.get("openai_model", "gpt-4o-mini"), messages)
        worker.finished.connect(self._on_response)
        worker.error.connect(self._on_error)
        self._worker = worker
        self._worker_thread = threading.Thread(target=worker.run, daemon=True)
        self._worker_thread.start()

    def _on_response(self, text: str):
        self._history.append({"role": "assistant", "content": text})
        self._append("AI", text)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Ask")

    def _on_error(self, msg: str):
        self._append("Error", msg)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Ask")

    def _append(self, role: str, text: str):
        colors = {"You": "#58a6ff", "AI": "#3fb950", "Error": "#f85149"}
        color = colors.get(role, "#8B949E")
        self.chat_area.append(
            f'<span style="color:{color};font-weight:700;">{role}:</span> '
            f'<span style="color:#F0F6FC;">{text.replace(chr(10), "<br>")}</span><br>'
        )
