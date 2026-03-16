"""Enhanced rich text editor — images embedded as base64, diagram support."""
import base64
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                              QToolBar, QToolButton, QFontComboBox, QSpinBox,
                              QColorDialog, QLabel, QFileDialog, QInputDialog,
                              QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (QFont, QTextCharFormat, QColor, QTextCursor,
                          QTextListFormat, QKeySequence, QAction,
                          QTextImageFormat, QImage)

logger = logging.getLogger(__name__)


class EnhancedEditor(QWidget):
    """Rich text editor with inline image embedding and diagram support."""

    textChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_toolbar())

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.setFont(QFont("Segoe UI", 14))
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.cursorPositionChanged.connect(self._sync_format_actions)
        layout.addWidget(self.editor)

        layout.addWidget(self._build_status_bar())

    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar()
        tb.setMovable(False)

        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Segoe UI"))
        self.font_combo.currentFontChanged.connect(
            lambda f: self._apply_fmt(lambda fmt: fmt.setFontFamily(f.family())))
        tb.addWidget(self.font_combo)

        tb.addSeparator()

        # Font size
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(14)
        self.font_size.setSuffix(" pt")
        self.font_size.valueChanged.connect(
            lambda s: self._apply_fmt(lambda fmt: fmt.setFontPointSize(s)))
        tb.addWidget(self.font_size)

        tb.addSeparator()

        # Bold / Italic / Underline / Strike
        self.act_bold = self._checkable_action("B", "Bold (Ctrl+B)",
                                                lambda: self._toggle_weight())
        self.act_bold.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        tb.addAction(self.act_bold)

        self.act_italic = self._checkable_action("I", "Italic (Ctrl+I)",
                                                  lambda: self._apply_fmt(
                                                      lambda f: f.setFontItalic(self.act_italic.isChecked())))
        f = QFont("Segoe UI", 10); f.setItalic(True)
        self.act_italic.setFont(f)
        tb.addAction(self.act_italic)

        self.act_underline = self._checkable_action("U", "Underline (Ctrl+U)",
                                                     lambda: self._apply_fmt(
                                                         lambda f: f.setFontUnderline(self.act_underline.isChecked())))
        f = QFont("Segoe UI", 10); f.setUnderline(True)
        self.act_underline.setFont(f)
        tb.addAction(self.act_underline)

        self.act_strike = self._checkable_action("S̶", "Strikethrough",
                                                  lambda: self._apply_fmt(
                                                      lambda f: f.setFontStrikeOut(self.act_strike.isChecked())))
        tb.addAction(self.act_strike)

        tb.addSeparator()

        # Colors
        act_color = QAction("A", self)
        act_color.setToolTip("Text Color")
        act_color.triggered.connect(self._pick_text_color)
        tb.addAction(act_color)

        act_highlight = QAction("H", self)
        act_highlight.setToolTip("Highlight")
        act_highlight.triggered.connect(self._pick_highlight)
        tb.addAction(act_highlight)

        tb.addSeparator()

        # Alignment
        for symbol, tip, align in [
            ("≡L", "Align Left", Qt.AlignmentFlag.AlignLeft),
            ("≡C", "Center", Qt.AlignmentFlag.AlignCenter),
            ("≡R", "Align Right", Qt.AlignmentFlag.AlignRight),
        ]:
            a = QAction(symbol, self)
            a.setToolTip(tip)
            a.triggered.connect(lambda _, al=align: self.editor.setAlignment(al))
            tb.addAction(a)

        tb.addSeparator()

        # Lists
        act_bullet = QAction("•", self)
        act_bullet.setToolTip("Bullet List")
        act_bullet.triggered.connect(
            lambda: self.editor.textCursor().insertList(QTextListFormat.Style.ListDisc))
        tb.addAction(act_bullet)

        act_num = QAction("1.", self)
        act_num.setToolTip("Numbered List")
        act_num.triggered.connect(
            lambda: self.editor.textCursor().insertList(QTextListFormat.Style.ListDecimal))
        tb.addAction(act_num)

        tb.addSeparator()

        # Insert: link, image, diagram, table, code
        act_link = QAction("🔗", self)
        act_link.setToolTip("Insert Link")
        act_link.triggered.connect(self._insert_link)
        tb.addAction(act_link)

        act_img = QAction("🖼", self)
        act_img.setToolTip("Insert Image (Ctrl+Shift+I)")
        act_img.triggered.connect(self.insert_image)
        tb.addAction(act_img)

        act_diagram = QAction("✏", self)
        act_diagram.setToolTip("Insert Diagram / Flowchart (Ctrl+Shift+D)")
        act_diagram.triggered.connect(self.insert_diagram)
        tb.addAction(act_diagram)

        act_table = QAction("⊞", self)
        act_table.setToolTip("Insert Table")
        act_table.triggered.connect(self._insert_table)
        tb.addAction(act_table)

        act_code = QAction("</>", self)
        act_code.setToolTip("Code Block")
        act_code.triggered.connect(self._insert_code_block)
        tb.addAction(act_code)

        return tb

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 4, 8, 4)

        self.lbl_words = QLabel("0 words")
        self.lbl_words.setObjectName("secondaryLabel")
        layout.addWidget(self.lbl_words)

        layout.addStretch()

        self.lbl_chars = QLabel("0 chars")
        self.lbl_chars.setObjectName("secondaryLabel")
        layout.addWidget(self.lbl_chars)

        return bar

    def _setup_shortcuts(self):
        self.act_bold.setShortcut(QKeySequence.StandardKey.Bold)
        self.act_italic.setShortcut(QKeySequence.StandardKey.Italic)
        self.act_underline.setShortcut(QKeySequence.StandardKey.Underline)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _checkable_action(self, label: str, tip: str, slot) -> QAction:
        a = QAction(label, self)
        a.setCheckable(True)
        a.setToolTip(tip)
        a.triggered.connect(slot)
        return a

    def _apply_fmt(self, mutate):
        fmt = QTextCharFormat()
        mutate(fmt)
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_weight(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(
            QFont.Weight.Bold if not self.act_bold.isChecked() else QFont.Weight.Normal)
        self._apply_fmt(lambda f: f.setFontWeight(fmt.fontWeight()))

    def _pick_text_color(self):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self._apply_fmt(lambda f: f.setForeground(color))

    def _pick_highlight(self):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self._apply_fmt(lambda f: f.setBackground(color))

    def _sync_format_actions(self):
        fmt = self.editor.textCursor().charFormat()
        self.act_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.act_italic.setChecked(fmt.fontItalic())
        self.act_underline.setChecked(fmt.fontUnderline())
        self.act_strike.setChecked(fmt.fontStrikeOut())
        self.font_combo.setCurrentFont(fmt.font())
        if fmt.fontPointSize() > 0:
            self.font_size.setValue(int(fmt.fontPointSize()))

    def _on_text_changed(self):
        text = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        self.lbl_words.setText(f"{words} words")
        self.lbl_chars.setText(f"{len(text)} chars")
        self.textChanged.emit()

    # ── insert actions ────────────────────────────────────────────────────────

    def _insert_link(self):
        url, ok = QInputDialog.getText(self, "Insert Link", "URL:")
        if ok and url:
            cursor = self.editor.textCursor()
            text = cursor.selectedText() or url
            cursor.insertHtml(f'<a href="{url}">{text}</a>')

    def insert_image(self):
        """Open file dialog and embed image as base64 inline."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp)")
        if not path:
            return
        self._embed_image_from_path(path)

    def _embed_image_from_path(self, path: str):
        """Read image file and insert as base64 data URI into the document."""
        try:
            img = QImage(path)
            if img.isNull():
                logger.warning(f"Could not load image: {path}")
                return

            # Scale down very large images to keep document manageable
            max_w = 800
            if img.width() > max_w:
                img = img.scaledToWidth(max_w, Qt.TransformationMode.SmoothTransformation)

            # Encode to base64 PNG
            from PyQt6.QtCore import QBuffer, QIODevice
            buf = QBuffer()
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            img.save(buf, "PNG")
            b64 = base64.b64encode(bytes(buf.data())).decode()

            # Insert via QTextImageFormat so it lives inside the document
            fmt = QTextImageFormat()
            fmt.setName(f"data:image/png;base64,{b64}")
            fmt.setWidth(img.width())
            fmt.setHeight(img.height())

            cursor = self.editor.textCursor()
            cursor.insertImage(fmt)
            logger.info(f"Embedded image: {path} ({img.width()}×{img.height()})")
        except Exception as e:
            logger.error(f"Image embed failed: {e}")

    def insert_diagram(self):
        """Open diagram editor and embed result as base64 PNG."""
        from src.ui.diagram_dialog import DiagramDialog
        dlg = DiagramDialog(parent=self)
        if dlg.exec() == DiagramDialog.DialogCode.Accepted:
            b64 = dlg.get_png_base64()
            if b64:
                self._embed_base64_png(b64)
                logger.info("Diagram inserted into note")

    def _embed_base64_png(self, b64: str):
        """Insert a base64 PNG string as an inline image."""
        try:
            raw = base64.b64decode(b64)
            img = QImage()
            img.loadFromData(raw, "PNG")
            if img.isNull():
                return
            fmt = QTextImageFormat()
            fmt.setName(f"data:image/png;base64,{b64}")
            fmt.setWidth(min(img.width(), 800))
            fmt.setHeight(int(img.height() * min(img.width(), 800) / max(img.width(), 1)))
            self.editor.textCursor().insertImage(fmt)
        except Exception as e:
            logger.error(f"Failed to embed diagram PNG: {e}")

    def _insert_table(self):
        rows, ok1 = QInputDialog.getInt(self, "Insert Table", "Rows:", 3, 1, 20)
        if not ok1:
            return
        cols, ok2 = QInputDialog.getInt(self, "Insert Table", "Columns:", 3, 1, 10)
        if not ok2:
            return
        html = '<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">'
        for _ in range(rows):
            html += "<tr>" + "<td>&nbsp;</td>" * cols + "</tr>"
        html += "</table>"
        self.editor.textCursor().insertHtml(html)

    def _insert_code_block(self):
        self.editor.textCursor().insertHtml(
            '<pre style="background:#161B22;color:#F0F6FC;padding:12px;'
            'border-radius:6px;font-family:Consolas,monospace;font-size:13px;">'
            '<code> </code></pre>')

    # ── public API (used by MainWindow) ──────────────────────────────────────

    def toPlainText(self) -> str:
        return self.editor.toPlainText()

    def toHtml(self) -> str:
        return self.editor.toHtml()

    def setHtml(self, html: str):
        self.editor.setHtml(html)

    def setText(self, text: str):
        self.editor.setText(text)

    def clear(self):
        self.editor.clear()

    def setPlaceholderText(self, text: str):
        self.editor.setPlaceholderText(text)

    def setFont(self, font: QFont):
        self.editor.setFont(font)
