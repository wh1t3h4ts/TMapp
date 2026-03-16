"""Modern sidebar with collapsible sections and icons."""
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QScrollArea, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon

logger = logging.getLogger(__name__)


class SidebarButton(QPushButton):
    """Custom sidebar button with icon and count."""
    
    def __init__(self, text: str, icon: str = "", count: int = 0, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.icon_text = icon
        self.count = count
        self.setObjectName("sidebarButton")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup button UI."""
        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_text()
    
    def update_text(self):
        """Update button text with icon and count."""
        text = f"{self.icon_text}  {self.text()}"
        if self.count > 0:
            text += f"  ({self.count})"
        super().setText(text)
    
    def set_count(self, count: int):
        """Set count badge."""
        self.count = count
        self.update_text()


class CollapsibleSection(QWidget):
    """Collapsible section for sidebar."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.is_collapsed = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup section UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Header
        self.header = QPushButton(f"▼ {self.title}")
        self.header.setObjectName("sectionHeader")
        self.header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.header.clicked.connect(self.toggle_collapse)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.header)
        
        # Content container
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 4, 0, 4)
        self.content_layout.setSpacing(4)
        layout.addWidget(self.content_widget)
    
    def toggle_collapse(self):
        """Toggle section collapse."""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.header.setText(f"▶ {self.title}")
            self.content_widget.hide()
        else:
            self.header.setText(f"▼ {self.title}")
            self.content_widget.show()
    
    def add_widget(self, widget: QWidget):
        """Add widget to section."""
        self.content_layout.addWidget(widget)


class ModernSidebar(QWidget):
    """Modern sidebar with sections and navigation."""
    
    # Signals
    all_notes_clicked = pyqtSignal()
    recent_clicked = pyqtSignal()
    favorites_clicked = pyqtSignal()
    archived_clicked = pyqtSignal()
    trash_clicked = pyqtSignal()
    notebook_clicked = pyqtSignal(str)  # notebook_id
    tag_clicked = pyqtSignal(str)  # tag_name
    new_notebook_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notebook_buttons = {}
        self.tag_buttons = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup sidebar UI."""
        self.setObjectName("modernSidebar")
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # Logo/Title
        title_layout = QHBoxLayout()
        title = QLabel("Starlex")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)
        
        # Quick Access Section
        self.quick_section = CollapsibleSection("QUICK ACCESS")
        
        self.btn_all_notes = SidebarButton("All Notes", "📝")
        self.btn_all_notes.clicked.connect(self.all_notes_clicked.emit)
        self.quick_section.add_widget(self.btn_all_notes)
        
        self.btn_recent = SidebarButton("Recent", "🕐")
        self.btn_recent.clicked.connect(self.recent_clicked.emit)
        self.quick_section.add_widget(self.btn_recent)
        
        self.btn_favorites = SidebarButton("Favorites", "⭐")
        self.btn_favorites.clicked.connect(self.favorites_clicked.emit)
        self.quick_section.add_widget(self.btn_favorites)
        
        self.btn_archived = SidebarButton("Archived", "📦")
        self.btn_archived.clicked.connect(self.archived_clicked.emit)
        self.quick_section.add_widget(self.btn_archived)
        
        self.btn_trash = SidebarButton("Trash", "🗑️")
        self.btn_trash.clicked.connect(self.trash_clicked.emit)
        self.quick_section.add_widget(self.btn_trash)
        
        scroll_layout.addWidget(self.quick_section)
        
        # Notebooks Section
        self.notebooks_section = CollapsibleSection("NOTEBOOKS")
        
        # Add notebook button
        self.btn_new_notebook = QPushButton("+ New Notebook")
        self.btn_new_notebook.setObjectName("addButton")
        self.btn_new_notebook.clicked.connect(self.new_notebook_clicked.emit)
        self.notebooks_section.add_widget(self.btn_new_notebook)
        
        scroll_layout.addWidget(self.notebooks_section)
        
        # Tags Section
        self.tags_section = CollapsibleSection("TAGS")
        scroll_layout.addWidget(self.tags_section)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Storage info at bottom
        self.storage_label = QLabel("Storage: 0 notes")
        self.storage_label.setObjectName("secondaryLabel")
        self.storage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.storage_label)
    
    def update_note_counts(self, all_count: int, favorites: int, archived: int, trash: int):
        """Update note counts in buttons."""
        self.btn_all_notes.set_count(all_count)
        self.btn_favorites.set_count(favorites)
        self.btn_archived.set_count(archived)
        self.btn_trash.set_count(trash)
        self.storage_label.setText(f"Storage: {all_count} notes")
    
    def add_notebook(self, notebook_id: str, name: str, count: int = 0):
        """Add notebook to sidebar."""
        if notebook_id in self.notebook_buttons:
            self.notebook_buttons[notebook_id].set_count(count)
            return
        
        btn = SidebarButton(name, "📓", count)
        btn.clicked.connect(lambda: self.notebook_clicked.emit(notebook_id))
        self.notebooks_section.add_widget(btn)
        self.notebook_buttons[notebook_id] = btn
    
    def remove_notebook(self, notebook_id: str):
        """Remove notebook from sidebar."""
        if notebook_id in self.notebook_buttons:
            btn = self.notebook_buttons[notebook_id]
            btn.deleteLater()
            del self.notebook_buttons[notebook_id]
    
    def update_notebook_count(self, notebook_id: str, count: int):
        """Update notebook note count."""
        if notebook_id in self.notebook_buttons:
            self.notebook_buttons[notebook_id].set_count(count)
    
    def add_tag(self, tag_name: str, count: int = 0):
        """Add tag to sidebar."""
        if tag_name in self.tag_buttons:
            self.tag_buttons[tag_name].set_count(count)
            return
        
        btn = SidebarButton(tag_name, "#", count)
        btn.clicked.connect(lambda: self.tag_clicked.emit(tag_name))
        self.tags_section.add_widget(btn)
        self.tag_buttons[tag_name] = btn
    
    def clear_tags(self):
        """Clear all tags."""
        for btn in self.tag_buttons.values():
            btn.deleteLater()
        self.tag_buttons.clear()
    
    def set_active_button(self, button_name: str):
        """Set active button style."""
        # Reset all buttons
        for btn in [self.btn_all_notes, self.btn_recent, self.btn_favorites, 
                    self.btn_archived, self.btn_trash]:
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # Set active button
        button_map = {
            "all": self.btn_all_notes,
            "recent": self.btn_recent,
            "favorites": self.btn_favorites,
            "archived": self.btn_archived,
            "trash": self.btn_trash
        }
        
        if button_name in button_map:
            btn = button_map[button_name]
            btn.setProperty("active", True)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
