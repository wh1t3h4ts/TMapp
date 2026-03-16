"""Drawing canvas for flowcharts and diagrams."""
import json
import logging
from enum import Enum
from typing import Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QToolButton,
                              QGraphicsView, QGraphicsScene, QGraphicsItem,
                              QGraphicsRectItem, QGraphicsEllipseItem,
                              QGraphicsLineItem, QGraphicsTextItem,
                              QGraphicsPathItem, QColorDialog, QInputDialog,
                              QLabel, QButtonGroup, QSizePolicy, QGraphicsPolygonItem)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QLineF
from PyQt6.QtGui import (QPen, QBrush, QColor, QPainter, QPainterPath,
                          QFont, QPolygonF, QTransform)

logger = logging.getLogger(__name__)


class Tool(Enum):
    SELECT = "select"
    RECT = "rect"
    ELLIPSE = "ellipse"
    DIAMOND = "diamond"
    TEXT = "text"
    ARROW = "arrow"
    LINE = "line"
    ERASER = "eraser"


class ArrowItem(QGraphicsPathItem):
    """Arrow/connector between nodes."""

    def __init__(self, start: QPointF, end: QPointF, color: QColor = QColor("#2563EB")):
        super().__init__()
        self.start = start
        self.end = end
        self.arrow_color = color
        self._build()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

    def _build(self):
        path = QPainterPath()
        path.moveTo(self.start)
        # Bezier curve for smooth arrow
        cx = (self.start.x() + self.end.x()) / 2
        path.cubicTo(QPointF(cx, self.start.y()), QPointF(cx, self.end.y()), self.end)

        # Arrowhead
        dx = self.end.x() - self.start.x()
        dy = self.end.y() - self.start.y()
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length > 0:
            ux, uy = dx / length, dy / length
            size = 12
            p1 = QPointF(self.end.x() - size * ux + size * 0.4 * uy,
                         self.end.y() - size * uy - size * 0.4 * ux)
            p2 = QPointF(self.end.x() - size * ux - size * 0.4 * uy,
                         self.end.y() - size * uy + size * 0.4 * ux)
            path.moveTo(self.end)
            path.lineTo(p1)
            path.moveTo(self.end)
            path.lineTo(p2)

        self.setPath(path)
        pen = QPen(self.arrow_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)

    def update_endpoints(self, start: QPointF, end: QPointF):
        self.start = start
        self.end = end
        self._build()


class DiamondItem(QGraphicsPolygonItem):
    """Diamond shape for decision nodes."""

    def __init__(self, rect: QRectF, color: QColor, border: QColor):
        super().__init__()
        cx, cy = rect.center().x(), rect.center().y()
        hw, hh = rect.width() / 2, rect.height() / 2
        poly = QPolygonF([
            QPointF(cx, cy - hh),
            QPointF(cx + hw, cy),
            QPointF(cx, cy + hh),
            QPointF(cx - hw, cy),
        ])
        self.setPolygon(poly)
        self.setBrush(QBrush(color))
        self.setPen(QPen(border, 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)


class DrawingScene(QGraphicsScene):
    """Custom scene handling shape drawing interactions."""

    item_added = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_tool = Tool.SELECT
        self.fill_color = QColor("#2563EB")
        self.border_color = QColor("#1746a2")
        self.text_color = QColor("#FFFFFF")
        self._drawing = False
        self._start = QPointF()
        self._temp_item = None
        self.setSceneRect(0, 0, 2000, 1500)

    def set_tool(self, tool: Tool):
        self.current_tool = tool
        for item in self.items():
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
                         tool == Tool.SELECT)
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
                         tool == Tool.SELECT)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        pos = event.scenePos()

        if self.current_tool == Tool.SELECT:
            super().mousePressEvent(event)
            return

        if self.current_tool == Tool.ERASER:
            item = self.itemAt(pos, QTransform())
            if item:
                self.removeItem(item)
            return

        if self.current_tool == Tool.TEXT:
            text, ok = QInputDialog.getText(None, "Add Text", "Enter text:")
            if ok and text:
                t = QGraphicsTextItem(text)
                t.setDefaultTextColor(self.text_color)
                t.setFont(QFont("Segoe UI", 12))
                t.setPos(pos)
                t.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                t.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                t.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
                self.addItem(t)
                self.item_added.emit()
            return

        self._drawing = True
        self._start = pos

        # Create temporary preview item
        if self.current_tool == Tool.RECT:
            self._temp_item = QGraphicsRectItem(QRectF(pos, pos))
            self._temp_item.setBrush(QBrush(self.fill_color))
            self._temp_item.setPen(QPen(self.border_color, 2))
        elif self.current_tool == Tool.ELLIPSE:
            self._temp_item = QGraphicsEllipseItem(QRectF(pos, pos))
            self._temp_item.setBrush(QBrush(self.fill_color))
            self._temp_item.setPen(QPen(self.border_color, 2))
        elif self.current_tool == Tool.DIAMOND:
            self._temp_item = DiamondItem(QRectF(pos, pos), self.fill_color, self.border_color)
        elif self.current_tool in (Tool.ARROW, Tool.LINE):
            self._temp_item = ArrowItem(pos, pos, self.border_color) if self.current_tool == Tool.ARROW \
                else QGraphicsLineItem(QLineF(pos, pos))
            if self.current_tool == Tool.LINE:
                self._temp_item.setPen(QPen(self.border_color, 2))

        if self._temp_item:
            self.addItem(self._temp_item)

    def mouseMoveEvent(self, event):
        if not self._drawing or not self._temp_item:
            super().mouseMoveEvent(event)
            return

        pos = event.scenePos()
        rect = QRectF(self._start, pos).normalized()

        if self.current_tool == Tool.RECT:
            self._temp_item.setRect(rect)
        elif self.current_tool == Tool.ELLIPSE:
            self._temp_item.setRect(rect)
        elif self.current_tool == Tool.DIAMOND:
            self.removeItem(self._temp_item)
            self._temp_item = DiamondItem(rect, self.fill_color, self.border_color)
            self.addItem(self._temp_item)
        elif self.current_tool == Tool.ARROW:
            self._temp_item.update_endpoints(self._start, pos)
        elif self.current_tool == Tool.LINE:
            self._temp_item.setLine(QLineF(self._start, pos))

    def mouseReleaseEvent(self, event):
        if not self._drawing:
            super().mouseReleaseEvent(event)
            return

        self._drawing = False
        pos = event.scenePos()
        rect = QRectF(self._start, pos).normalized()

        # Discard tiny accidental clicks
        if rect.width() < 5 and rect.height() < 5 and self.current_tool not in (Tool.ARROW, Tool.LINE):
            if self._temp_item:
                self.removeItem(self._temp_item)
            self._temp_item = None
            return

        # Finalize item — make it movable/selectable
        if self._temp_item:
            self._temp_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            self._temp_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
            self._temp_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
            self._temp_item = None
            self.item_added.emit()

    def to_dict(self) -> list:
        """Serialize all items to a list of dicts."""
        data = []
        for item in self.items():
            if isinstance(item, QGraphicsRectItem):
                r = item.rect()
                data.append({"type": "rect", "x": r.x(), "y": r.y(),
                              "w": r.width(), "h": r.height(),
                              "fill": item.brush().color().name(),
                              "border": item.pen().color().name()})
            elif isinstance(item, QGraphicsEllipseItem):
                r = item.rect()
                data.append({"type": "ellipse", "x": r.x(), "y": r.y(),
                              "w": r.width(), "h": r.height(),
                              "fill": item.brush().color().name(),
                              "border": item.pen().color().name()})
            elif isinstance(item, DiamondItem):
                p = item.polygon()
                pts = [{"x": pt.x(), "y": pt.y()} for pt in p]
                data.append({"type": "diamond", "points": pts,
                              "fill": item.brush().color().name(),
                              "border": item.pen().color().name()})
            elif isinstance(item, ArrowItem):
                data.append({"type": "arrow",
                              "sx": item.start.x(), "sy": item.start.y(),
                              "ex": item.end.x(), "ey": item.end.y(),
                              "color": item.arrow_color.name()})
            elif isinstance(item, QGraphicsLineItem):
                ln = item.line()
                data.append({"type": "line",
                              "sx": ln.x1(), "sy": ln.y1(),
                              "ex": ln.x2(), "ey": ln.y2(),
                              "color": item.pen().color().name()})
            elif isinstance(item, QGraphicsTextItem):
                data.append({"type": "text", "x": item.x(), "y": item.y(),
                              "text": item.toPlainText(),
                              "color": item.defaultTextColor().name()})
        return data

    def from_dict(self, data: list):
        """Restore items from serialized data."""
        self.clear()
        for d in data:
            t = d.get("type")
            if t == "rect":
                item = QGraphicsRectItem(QRectF(d["x"], d["y"], d["w"], d["h"]))
                item.setBrush(QBrush(QColor(d["fill"])))
                item.setPen(QPen(QColor(d["border"]), 2))
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                self.addItem(item)
            elif t == "ellipse":
                item = QGraphicsEllipseItem(QRectF(d["x"], d["y"], d["w"], d["h"]))
                item.setBrush(QBrush(QColor(d["fill"])))
                item.setPen(QPen(QColor(d["border"]), 2))
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                self.addItem(item)
            elif t == "diamond":
                pts = [QPointF(p["x"], p["y"]) for p in d["points"]]
                poly = QPolygonF(pts)
                item = QGraphicsPolygonItem(poly)
                item.setBrush(QBrush(QColor(d["fill"])))
                item.setPen(QPen(QColor(d["border"]), 2))
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                self.addItem(item)
            elif t == "arrow":
                item = ArrowItem(QPointF(d["sx"], d["sy"]),
                                 QPointF(d["ex"], d["ey"]),
                                 QColor(d["color"]))
                self.addItem(item)
            elif t == "line":
                item = QGraphicsLineItem(QLineF(d["sx"], d["sy"], d["ex"], d["ey"]))
                item.setPen(QPen(QColor(d["color"]), 2))
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                self.addItem(item)
            elif t == "text":
                item = QGraphicsTextItem(d["text"])
                item.setDefaultTextColor(QColor(d["color"]))
                item.setFont(QFont("Segoe UI", 12))
                item.setPos(d["x"], d["y"])
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
                self.addItem(item)


class DrawingCanvas(QWidget):
    """Full drawing canvas widget with toolbar."""

    diagram_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = DrawingScene()
        self.scene.item_added.connect(self.diagram_changed)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        # Canvas view
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view.setBackgroundBrush(QBrush(QColor("#0D1117")))
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        layout.addWidget(self.view)

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("drawingToolbar")
        bar.setStyleSheet("""
            QWidget#drawingToolbar { background: #161B22; border-bottom: 1px solid #21262D; }
            QToolButton { background: transparent; border: none; border-radius: 6px;
                          padding: 6px 10px; color: #F0F6FC; font-size: 13px; min-width: 32px; }
            QToolButton:hover { background: rgba(37,99,235,0.2); }
            QToolButton:checked { background: #2563EB; color: white; }
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        self._tool_group = QButtonGroup(self)
        self._tool_group.setExclusive(True)

        tools = [
            ("↖", Tool.SELECT, "Select / Move (V)"),
            ("▭", Tool.RECT, "Rectangle (R)"),
            ("○", Tool.ELLIPSE, "Ellipse (E)"),
            ("◇", Tool.DIAMOND, "Diamond (D)"),
            ("T", Tool.TEXT, "Text (T)"),
            ("→", Tool.ARROW, "Arrow (A)"),
            ("╱", Tool.LINE, "Line (L)"),
            ("✕", Tool.ERASER, "Eraser (X)"),
        ]

        for label, tool, tip in tools:
            btn = QToolButton()
            btn.setText(label)
            btn.setToolTip(tip)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, t=tool: self._set_tool(t))
            self._tool_group.addButton(btn)
            layout.addWidget(btn)
            if tool == Tool.SELECT:
                btn.setChecked(True)

        layout.addSpacing(16)

        # Color pickers
        self.btn_fill = QToolButton()
        self.btn_fill.setText("Fill")
        self.btn_fill.setToolTip("Fill Color")
        self.btn_fill.clicked.connect(self._pick_fill)
        self._update_color_btn(self.btn_fill, QColor("#2563EB"))
        layout.addWidget(self.btn_fill)

        self.btn_border = QToolButton()
        self.btn_border.setText("Border")
        self.btn_border.setToolTip("Border / Line Color")
        self.btn_border.clicked.connect(self._pick_border)
        self._update_color_btn(self.btn_border, QColor("#1746a2"))
        layout.addWidget(self.btn_border)

        layout.addSpacing(16)

        # Zoom
        btn_zoom_in = QToolButton()
        btn_zoom_in.setText("+")
        btn_zoom_in.setToolTip("Zoom In")
        btn_zoom_in.clicked.connect(lambda: self.view.scale(1.2, 1.2))
        layout.addWidget(btn_zoom_in)

        btn_zoom_out = QToolButton()
        btn_zoom_out.setText("−")
        btn_zoom_out.setToolTip("Zoom Out")
        btn_zoom_out.clicked.connect(lambda: self.view.scale(1 / 1.2, 1 / 1.2))
        layout.addWidget(btn_zoom_out)

        btn_fit = QToolButton()
        btn_fit.setText("Fit")
        btn_fit.setToolTip("Fit to view")
        btn_fit.clicked.connect(self._fit_view)
        layout.addWidget(btn_fit)

        layout.addSpacing(16)

        btn_clear = QToolButton()
        btn_clear.setText("Clear")
        btn_clear.setToolTip("Clear canvas")
        btn_clear.clicked.connect(self._clear)
        layout.addWidget(btn_clear)

        btn_del = QToolButton()
        btn_del.setText("Del")
        btn_del.setToolTip("Delete selected")
        btn_del.clicked.connect(self._delete_selected)
        layout.addWidget(btn_del)

        layout.addStretch()

        # Hint label
        hint = QLabel("Drag to draw • Scroll to zoom • Middle-drag to pan")
        hint.setStyleSheet("color: #8B949E; font-size: 11px;")
        layout.addWidget(hint)

        return bar

    def _update_color_btn(self, btn: QToolButton, color: QColor):
        btn.setStyleSheet(f"""
            QToolButton {{
                background: {color.name()};
                border: 2px solid #30363D;
                border-radius: 4px;
                padding: 4px 8px;
                color: {'white' if color.lightness() < 128 else 'black'};
                font-size: 11px;
            }}
            QToolButton:hover {{ border-color: #2563EB; }}
        """)

    def _set_tool(self, tool: Tool):
        self.scene.set_tool(tool)
        if tool == Tool.SELECT:
            self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def _pick_fill(self):
        color = QColorDialog.getColor(self.scene.fill_color, self, "Fill Color")
        if color.isValid():
            self.scene.fill_color = color
            self._update_color_btn(self.btn_fill, color)

    def _pick_border(self):
        color = QColorDialog.getColor(self.scene.border_color, self, "Border Color")
        if color.isValid():
            self.scene.border_color = color
            self.scene.text_color = color
            self._update_color_btn(self.btn_border, color)

    def _fit_view(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isEmpty():
            self.view.fitInView(rect.adjusted(-20, -20, 20, 20),
                                Qt.AspectRatioMode.KeepAspectRatio)

    def _clear(self):
        self.scene.clear()
        self.diagram_changed.emit()

    def _delete_selected(self):
        for item in self.scene.selectedItems():
            self.scene.removeItem(item)
        self.diagram_changed.emit()

    def keyPressEvent(self, event):
        shortcuts = {
            Qt.Key.Key_V: Tool.SELECT, Qt.Key.Key_R: Tool.RECT,
            Qt.Key.Key_E: Tool.ELLIPSE, Qt.Key.Key_D: Tool.DIAMOND,
            Qt.Key.Key_T: Tool.TEXT, Qt.Key.Key_A: Tool.ARROW,
            Qt.Key.Key_L: Tool.LINE, Qt.Key.Key_X: Tool.ERASER,
        }
        if event.key() in shortcuts:
            self._set_tool(shortcuts[event.key()])
        elif event.key() == Qt.Key.Key_Delete:
            self._delete_selected()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.view.scale(factor, factor)

    def get_diagram_data(self) -> str:
        return json.dumps(self.scene.to_dict())

    def load_diagram_data(self, data: str):
        try:
            self.scene.from_dict(json.loads(data))
        except Exception as e:
            logger.error(f"Failed to load diagram: {e}")

    def export_image(self) -> bytes:
        """Export canvas as PNG bytes."""
        from PyQt6.QtGui import QImage
        rect = self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20)
        if rect.isEmpty():
            rect = QRectF(0, 0, 800, 600)
        img = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
        img.fill(QColor("#0D1117"))
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter, source=rect)
        painter.end()
        from PyQt6.QtCore import QBuffer, QIODevice
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buf, "PNG")
        return bytes(buf.data())
