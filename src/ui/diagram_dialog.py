"""Diagram editor dialog — wraps DrawingCanvas, returns base64 PNG on accept."""
import base64
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.ui.drawing_canvas import DrawingCanvas

logger = logging.getLogger(__name__)


class DiagramDialog(QDialog):
    """Modal dialog for creating / editing diagrams."""

    def __init__(self, existing_data: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("TMapp — Diagram Editor")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 750)
        self._png_b64: str = ""
        self._diagram_json: str = existing_data
        self._setup_ui()
        if existing_data:
            self.canvas.load_diagram_data(existing_data)

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog { background: #0D1117; color: #F0F6FC; }
            QPushButton {
                background: #2563EB; color: white; border: none;
                border-radius: 6px; padding: 8px 20px; font-size: 13px;
            }
            QPushButton:hover { background: #3973f7; }
            QPushButton#cancel {
                background: transparent; border: 1px solid #30363D; color: #8B949E;
            }
            QPushButton#cancel:hover { border-color: #2563EB; color: #F0F6FC; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: #161B22; border-bottom: 1px solid #21262D;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 10, 16, 10)

        title = QLabel("Diagram Editor")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #F0F6FC; background: transparent;")
        hl.addWidget(title)

        hint = QLabel("Draw shapes, connect with arrows, add labels")
        hint.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent;")
        hl.addWidget(hint)
        hl.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("cancel")
        btn_cancel.clicked.connect(self.reject)
        hl.addWidget(btn_cancel)

        btn_insert = QPushButton("Insert into Note")
        btn_insert.clicked.connect(self._accept)
        hl.addWidget(btn_insert)

        layout.addWidget(header)

        # Canvas
        self.canvas = DrawingCanvas(self)
        layout.addWidget(self.canvas)

    def _accept(self):
        try:
            png_bytes = self.canvas.export_image()
            self._png_b64 = base64.b64encode(png_bytes).decode("utf-8")
            self._diagram_json = self.canvas.get_diagram_data()
            self.accept()
        except Exception as e:
            logger.error(f"Failed to export diagram: {e}")
            self.reject()

    def get_png_base64(self) -> str:
        return self._png_b64

    def get_diagram_json(self) -> str:
        return self._diagram_json


# Make QWidget importable at module level for type hints
from PyQt6.QtWidgets import QWidget
