"""Advanced search bar with filtering and suggestions."""
import logging
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, 
                              QMenu, QLabel, QVBoxLayout, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class AdvancedSearchBar(QWidget):
    """Advanced search bar with filters."""
    
    # Signals
    search_requested = pyqtSignal(str, dict)  # query, filters
    search_cleared = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = {
            'in_title': True,
            'in_content': True,
            'in_tags': False,
            'favorites_only': False,
            'archived': False
        }
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup search bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Search icon
        search_icon = QLabel("🔍")
        search_icon.setFixedWidth(24)
        layout.addWidget(search_icon)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search notes...")
        self.search_input.textChanged.connect(self.on_text_changed)
        self.search_input.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_input, 1)
        
        # Filter button
        self.filter_btn = QPushButton("⚙️")
        self.filter_btn.setObjectName("secondaryButton")
        self.filter_btn.setToolTip("Search Filters")
        self.filter_btn.setFixedWidth(40)
        self.filter_btn.clicked.connect(self.show_filter_menu)
        layout.addWidget(self.filter_btn)
        
        # Clear button
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.setToolTip("Clear Search")
        self.clear_btn.setFixedWidth(40)
        self.clear_btn.clicked.connect(self.clear_search)
        self.clear_btn.setVisible(False)
        layout.addWidget(self.clear_btn)
    
    def on_text_changed(self, text: str):
        """Handle text change with debounce."""
        self.clear_btn.setVisible(bool(text))
        
        # Debounce search
        self.search_timer.stop()
        if text:
            self.search_timer.start(300)  # 300ms delay
        else:
            self.search_cleared.emit()
    
    def perform_search(self):
        """Perform search with current query and filters."""
        query = self.search_input.text().strip()
        if query:
            self.search_requested.emit(query, self.filters.copy())
    
    def clear_search(self):
        """Clear search."""
        self.search_input.clear()
        self.search_cleared.emit()
    
    def show_filter_menu(self):
        """Show filter options menu."""
        menu = QMenu(self)
        
        # Search in title
        action_title = menu.addAction("Search in Title")
        action_title.setCheckable(True)
        action_title.setChecked(self.filters['in_title'])
        action_title.triggered.connect(lambda: self.toggle_filter('in_title'))
        
        # Search in content
        action_content = menu.addAction("Search in Content")
        action_content.setCheckable(True)
        action_content.setChecked(self.filters['in_content'])
        action_content.triggered.connect(lambda: self.toggle_filter('in_content'))
        
        # Search in tags
        action_tags = menu.addAction("Search in Tags")
        action_tags.setCheckable(True)
        action_tags.setChecked(self.filters['in_tags'])
        action_tags.triggered.connect(lambda: self.toggle_filter('in_tags'))
        
        menu.addSeparator()
        
        # Favorites only
        action_favorites = menu.addAction("Favorites Only")
        action_favorites.setCheckable(True)
        action_favorites.setChecked(self.filters['favorites_only'])
        action_favorites.triggered.connect(lambda: self.toggle_filter('favorites_only'))
        
        # Include archived
        action_archived = menu.addAction("Include Archived")
        action_archived.setCheckable(True)
        action_archived.setChecked(self.filters['archived'])
        action_archived.triggered.connect(lambda: self.toggle_filter('archived'))
        
        menu.exec(self.filter_btn.mapToGlobal(self.filter_btn.rect().bottomLeft()))
    
    def toggle_filter(self, filter_name: str):
        """Toggle filter and re-search."""
        self.filters[filter_name] = not self.filters[filter_name]
        if self.search_input.text():
            self.perform_search()
    
    def set_focus(self):
        """Set focus to search input."""
        self.search_input.setFocus()
    
    def get_query(self) -> str:
        """Get current search query."""
        return self.search_input.text().strip()
