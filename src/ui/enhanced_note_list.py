"""Enhanced note list with rich previews and metadata."""
import logging
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                              QListWidgetItem, QLabel, QFrame, QPushButton, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger(__name__)


class NoteListItem(QWidget):
    """Custom note list item with rich preview."""
    
    def __init__(self, note_id: str, title: str, preview: str, 
                 modified_at: datetime, is_favorite: bool = False, 
                 is_pinned: bool = False, tags: list = None, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.title_text = title
        self.preview_text = preview
        self.modified_at = modified_at
        self.is_favorite = is_favorite
        self.is_pinned = is_pinned
        self.tags = tags or []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup item UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Header row (title + badges)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Pin indicator
        if self.is_pinned:
            pin_label = QLabel("📌")
            pin_label.setFixedWidth(20)
            header_layout.addWidget(pin_label)
        
        # Title
        title = QLabel(self.title_text or "Untitled")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setWordWrap(False)
        title_text = title.text()
        if len(title_text) > 40:
            title.setText(title_text[:40] + "...")
        header_layout.addWidget(title, 1)
        
        # Favorite indicator
        if self.is_favorite:
            fav_label = QLabel("⭐")
            fav_label.setFixedWidth(20)
            header_layout.addWidget(fav_label)
        
        layout.addLayout(header_layout)
        
        # Preview text
        if self.preview_text:
            preview = QLabel(self.preview_text)
            preview.setObjectName("secondaryLabel")
            preview.setFont(QFont("Segoe UI", 11))
            preview.setWordWrap(True)
            preview.setMaximumHeight(40)
            preview_text = preview.text()
            if len(preview_text) > 100:
                preview.setText(preview_text[:100] + "...")
            layout.addWidget(preview)
        
        # Footer row (date + tags)
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)
        
        # Modified date
        date_label = QLabel(self.format_date(self.modified_at))
        date_label.setObjectName("secondaryLabel")
        date_label.setFont(QFont("Segoe UI", 10))
        footer_layout.addWidget(date_label)
        
        footer_layout.addStretch()
        
        # Tags
        if self.tags:
            tags_text = " ".join([f"#{tag}" for tag in self.tags[:3]])
            if len(self.tags) > 3:
                tags_text += f" +{len(self.tags) - 3}"
            tags_label = QLabel(tags_text)
            tags_label.setObjectName("secondaryLabel")
            tags_label.setFont(QFont("Segoe UI", 10))
            footer_layout.addWidget(tags_label)
        
        layout.addLayout(footer_layout)
    
    def format_date(self, dt: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now()
        diff = now - dt
        
        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes}m ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks}w ago"
        else:
            return dt.strftime("%b %d, %Y")


class EnhancedNoteList(QWidget):
    """Enhanced note list with rich previews."""
    
    # Signals
    note_selected = pyqtSignal(str)  # note_id
    note_context_menu = pyqtSignal(str, object)  # note_id, position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.note_items = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup list UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(4)
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.on_context_menu)
        layout.addWidget(self.list_widget)
    
    def add_note(self, note_id: str, title: str, preview: str, 
                 modified_at: datetime, is_favorite: bool = False,
                 is_pinned: bool = False, tags: list = None):
        """Add note to list."""
        # Create custom widget
        item_widget = NoteListItem(
            note_id, title, preview, modified_at, 
            is_favorite, is_pinned, tags
        )
        
        # Create list item
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(item_widget.sizeHint())
        item.setData(Qt.ItemDataRole.UserRole, note_id)
        
        # Add to list
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, item_widget)
        
        self.note_items[note_id] = item
    
    def remove_note(self, note_id: str):
        """Remove note from list."""
        if note_id in self.note_items:
            item = self.note_items[note_id]
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            del self.note_items[note_id]
    
    def clear(self):
        """Clear all notes."""
        self.list_widget.clear()
        self.note_items.clear()
    
    def update_note(self, note_id: str, title: str, preview: str, 
                    modified_at: datetime, is_favorite: bool = False,
                    is_pinned: bool = False, tags: list = None):
        """Update existing note."""
        if note_id in self.note_items:
            self.remove_note(note_id)
        self.add_note(note_id, title, preview, modified_at, 
                     is_favorite, is_pinned, tags)
    
    def set_notes(self, notes: list):
        """Set all notes at once."""
        self.clear()
        for note in notes:
            self.add_note(
                note.id,
                note.title,
                note.get_plain_text()[:100] if hasattr(note, 'get_plain_text') else "",
                note.modified_at,
                note.is_favorite,
                note.is_pinned,
                note.tags if hasattr(note, 'tags') else []
            )
    
    def get_selected_note_id(self) -> str:
        """Get selected note ID."""
        items = self.list_widget.selectedItems()
        if items:
            return items[0].data(Qt.ItemDataRole.UserRole)
        return None
    
    def select_note(self, note_id: str):
        """Select note by ID."""
        if note_id in self.note_items:
            item = self.note_items[note_id]
            self.list_widget.setCurrentItem(item)
    
    def on_item_clicked(self, item: QListWidgetItem):
        """Handle item click."""
        note_id = item.data(Qt.ItemDataRole.UserRole)
        self.note_selected.emit(note_id)
    
    def on_context_menu(self, position):
        """Handle context menu request."""
        item = self.list_widget.itemAt(position)
        if item:
            note_id = item.data(Qt.ItemDataRole.UserRole)
            global_pos = self.list_widget.mapToGlobal(position)
            self.note_context_menu.emit(note_id, global_pos)
    
    def count(self) -> int:
        """Get note count."""
        return self.list_widget.count()
