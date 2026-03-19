"""Diagram editor — full-screen QMainWindow, app theme, rich toolbar."""
import base64
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QApplication)
from PyQt6.QtCore import Qt, QEventLoop
from PyQt6.QtGui import QFont, QIcon
import os, sys

logger = logging.getLogger(__name__)

def _resource_path(rel):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base, rel)

_LOGO_PATH = _resource_path('src/logo.png')


class DiagramDialog(QMainWindow):
    """Full-screen diagram editor with app theme."""

    class DialogCode:
        Accepted = 1
        Rejected = 0

    def __init__(self, existing_data: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("TMapp — Diagram Editor")
        self.setMinimumSize(900, 600)
        if os.path.exists(_LOGO_PATH):
            self.setWindowIcon(QIcon(_LOGO_PATH))

        self._result = self.DialogCode.Rejected
        self._png_b64: str = ""
        self._diagram_json: str = existing_data

        self._setup_ui()
        self._apply_theme()

        if existing_data:
            self.canvas.load_diagram_data(existing_data)

        self.showMaximized()

    def _setup_ui(self):
        from src.ui.drawing_canvas import DrawingCanvas

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── header bar ────────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("editorTopBar")
        header.setFixedHeight(52)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.setSpacing(10)

        title = QLabel("Diagram Editor")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("panelTitle")
        hl.addWidget(title)

        hint = QLabel("Draw shapes · connect with arrows · add labels · Scroll to zoom")
        hint.setObjectName("breadcrumb")
        hint.setFont(QFont("Segoe UI", 11))
        hl.addWidget(hint)
        hl.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("secondaryButton")
        btn_cancel.setFixedHeight(34)
        btn_cancel.clicked.connect(self.reject)
        hl.addWidget(btn_cancel)

        btn_insert = QPushButton("Insert into Note")
        btn_insert.setFixedHeight(34)
        btn_insert.clicked.connect(self._accept)
        hl.addWidget(btn_insert)

        layout.addWidget(header)

        # ── canvas ────────────────────────────────────────────────────────────
        self.canvas = DrawingCanvas(self)
        layout.addWidget(self.canvas, stretch=1)

    def _apply_theme(self):
        from src.ui.theme_manager import ThemeManager
        self.setStyleSheet(ThemeManager().get_stylesheet())

    def _accept(self):
        try:
            png_bytes = self.canvas.export_image()
            self._png_b64 = base64.b64encode(png_bytes).decode("utf-8")
            self._diagram_json = self.canvas.get_diagram_data()
            self.accept()
        except Exception as e:
            logger.error(f"Failed to export diagram: {e}")
            self.reject()

    # ── QDialog-compatible shim ───────────────────────────────────────────────
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

    def get_png_base64(self) -> str:
        return self._png_b64

    def get_diagram_json(self) -> str:
        return self._diagram_json
