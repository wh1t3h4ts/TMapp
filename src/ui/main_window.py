"""Professional main window — futuristic workstation layout."""
import logging
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QSplitter, QStatusBar, QLabel, QMessageBox,
                              QListWidget, QListWidgetItem, QPushButton,
                              QToolButton, QMenu, QLineEdit, QSizePolicy,
                              QFileDialog, QInputDialog, QFrame, QScrollArea,
                              QDockWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction, QKeySequence, QFont, QShortcut, QPixmap, QIcon

import sys as _sys
import os as _os

def _resource_path(relative: str) -> str:
    """Resolve path whether running normally or bundled by PyInstaller."""
    base = getattr(_sys, '_MEIPASS', _os.path.dirname(_os.path.dirname(__file__)))
    return _os.path.join(base, relative)

_LOGO_PATH = _resource_path('src/logo.png')

from src.core.config import AppConfig
from src.core.encryption import EncryptionService
from src.controllers.note_controller import NoteController
from src.controllers.notebook_controller import NotebookController
from src.controllers.credential_controller import CredentialController
from src.ui.theme_manager import ThemeManager, ThemeMode
from src.ui.enhanced_editor import EnhancedEditor
from src.ui.credential_panel import CredentialPanel
from src.ui.ai_panel import AIPanel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Professional main window with modern UI."""
    
    locked = pyqtSignal()
    unlocked = pyqtSignal()
    
    def __init__(self, config: AppConfig, encryption_service: EncryptionService,
                 note_controller: NoteController, notebook_controller: NotebookController):
        super().__init__()
        
        self.config = config
        self.encryption_service = encryption_service
        self.note_controller = note_controller
        self.notebook_controller = notebook_controller
        self.credential_controller = CredentialController(note_controller.db)
        self.is_locked = False
        self.current_note_id = None
        self.current_note = None
        self.is_modified = False
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        
        self._compact_mode = False   # responsive state flag

        self._setup_ui()
        self._apply_theme()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_shortcuts()
        self._setup_auto_save()
        self._setup_auto_lock()
        self._load_data()
        
        logger.info("Main window initialized with professional UI")
    
    # ── RESPONSIVE BREAKPOINT ─────────────────────────────────────────────────
    _COMPACT_BREAKPOINT = 1024   # px — below this width sidebars auto-hide

    def resizeEvent(self, event):
        """Switch between desktop (3-col) and compact (editor-only) layouts."""
        super().resizeEvent(event)
        w = event.size().width()
        if w < self._COMPACT_BREAKPOINT and not self._compact_mode:
            self._set_compact_mode(True)
        elif w >= self._COMPACT_BREAKPOINT and self._compact_mode:
            self._set_compact_mode(False)

    def _set_compact_mode(self, compact: bool):
        """Hide/show side panels based on viewport width — layout only."""
        self._compact_mode = compact
        # Animate left panel width to 0 or restore
        self._animate_panel_width(self.left_panel,  0 if compact else 300)
        self._animate_panel_width(self.right_panel, 0 if compact else 320)
        # Tag root widget so QSS data-attribute rules apply
        root = self.centralWidget()
        root.setProperty("compactMode", "true" if compact else "false")
        root.style().unpolish(root)
        root.style().polish(root)

    def _animate_panel_width(self, panel: QWidget, target_width: int):
        """Smoothly animate a panel's maximum width (layout-only, no logic)."""
        anim = QPropertyAnimation(panel, b"maximumWidth", self)
        anim.setDuration(220)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(panel.width())
        anim.setEndValue(target_width)
        # Hide completely once collapsed so it takes no splitter space
        if target_width == 0:
            anim.finished.connect(lambda: panel.setVisible(False))
        else:
            panel.setVisible(True)
            panel.setMaximumWidth(target_width)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _setup_ui(self):
        """Full-viewport 3-column workstation layout."""
        self.setWindowTitle("TMapp — Secure Notes")
        self.setMinimumSize(760, 560)   # allow compact/tablet sizes
        # Set window icon
        if _os.path.exists(_LOGO_PATH):
            self.setWindowIcon(QIcon(_LOGO_PATH))

        # ── root widget fills the entire window ──────────────────────────────
        root = QWidget()
        root.setObjectName("rootWidget")
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── 1. TOP BAR (fixed height 52 px) ──────────────────────────────────
        self.top_bar = self._create_top_bar()
        root_layout.addWidget(self.top_bar)

        # ── 2. MAIN CONTENT (fills remaining height) ─────────────────────────
        # 3-column grid: left panel | editor | right panel
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setHandleWidth(2)
        self.main_splitter.setChildrenCollapsible(False)

        # col-1  left panel: sidebar nav + notes list stacked vertically
        self.left_panel = self._create_left_panel()
        self.left_panel.setMinimumWidth(240)
        self.left_panel.setMaximumWidth(400)

        # col-2  editor (flex-grow)
        self.editor_panel = self._create_editor_panel()
        self.editor_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # col-3  right panel: backlinks / properties / outline
        self.right_panel = self._create_right_panel()
        self.right_panel.setMinimumWidth(280)
        self.right_panel.setMaximumWidth(480)

        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.editor_panel)
        self.main_splitter.addWidget(self.right_panel)

        # initial column widths  (left | editor | right)
        self.main_splitter.setSizes([300, 9999, 320])
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 0)

        root_layout.addWidget(self.main_splitter, stretch=1)

        # ── 3. BOTTOM STATUS BAR (fixed height 28 px) ────────────────────────
        self.bottom_bar = self._create_bottom_bar()
        root_layout.addWidget(self.bottom_bar)

    # ── TOP BAR ───────────────────────────────────────────────────────────────
    def _create_top_bar(self) -> QWidget:
        """Sticky top bar: logo+search | breadcrumb | actions."""
        bar = QWidget()
        bar.setObjectName("topBar")
        bar.setFixedHeight(52)
        bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        outer = QHBoxLayout(bar)
        outer.setContentsMargins(12, 0, 12, 0)
        outer.setSpacing(0)

        # ── LEFT: toggle buttons + logo + search ─────────────────────────────
        left = QHBoxLayout()
        left.setSpacing(6)

        # left panel toggle (Ctrl+\)
        self.btn_toggle_sidebar = QToolButton()
        self.btn_toggle_sidebar.setText("☰")
        self.btn_toggle_sidebar.setToolTip("Toggle left panel (Ctrl+\\)")
        self.btn_toggle_sidebar.setFixedSize(32, 32)
        self.btn_toggle_sidebar.clicked.connect(self._toggle_sidebar)
        left.addWidget(self.btn_toggle_sidebar)

        # right panel toggle (Ctrl+B)
        self.btn_toggle_right = QToolButton()
        self.btn_toggle_right.setText("⊟")
        self.btn_toggle_right.setToolTip("Toggle right panel (Ctrl+B)")
        self.btn_toggle_right.setFixedSize(32, 32)
        self.btn_toggle_right.clicked.connect(self._toggle_right_panel)
        left.addWidget(self.btn_toggle_right)

        # logo image
        logo = QLabel()
        logo.setObjectName("topBarLogo")
        pix = QPixmap(_LOGO_PATH) if _os.path.exists(_LOGO_PATH) else QPixmap()
        if not pix.isNull():
            logo.setPixmap(pix.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("TMapp")
            logo.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        logo.setContentsMargins(8, 0, 12, 0)
        left.addWidget(logo)

        # global search
        self.search_box = QLineEdit()
        self.search_box.setObjectName("topBarSearch")
        self.search_box.setPlaceholderText("Search notes...")
        self.search_box.setFixedHeight(32)
        self.search_box.setMinimumWidth(180)
        self.search_box.setMaximumWidth(340)
        self.search_box.textChanged.connect(self._on_search)
        left.addWidget(self.search_box)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # ── CENTER: current note breadcrumb ───────────────────────────────────
        self.breadcrumb_label = QLabel("")
        self.breadcrumb_label.setObjectName("breadcrumb")
        self.breadcrumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.breadcrumb_label.setFont(QFont("Segoe UI", 11))
        self.breadcrumb_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # ── RIGHT: quick actions ──────────────────────────────────────────────
        right = QHBoxLayout()
        right.setSpacing(4)

        btn_new = QPushButton("+ New")
        btn_new.setObjectName("topBarAction")
        btn_new.setFixedHeight(32)
        btn_new.setToolTip("New note (Ctrl+N)")
        btn_new.clicked.connect(self._new_note)
        right.addWidget(btn_new)

        self.btn_theme_toggle = QToolButton()
        self.btn_theme_toggle.setText("☽")
        self.btn_theme_toggle.setToolTip("Toggle theme (Ctrl+T)")
        self.btn_theme_toggle.setFixedSize(32, 32)
        self.btn_theme_toggle.clicked.connect(self._toggle_theme)
        right.addWidget(self.btn_theme_toggle)

        self.vault_btn = QToolButton()
        self.vault_btn.setText("🔑")
        self.vault_btn.setToolTip("Password Manager (Ctrl+Shift+V)")
        self.vault_btn.setFixedSize(32, 32)
        self.vault_btn.clicked.connect(self._toggle_vault_popup)
        right.addWidget(self.vault_btn)

        self.lock_btn = QToolButton()
        self.lock_btn.setText("🔒")
        self.lock_btn.setToolTip("Lock vault (Ctrl+L)")
        self.lock_btn.setFixedSize(32, 32)
        self.lock_btn.clicked.connect(self._toggle_lock)
        right.addWidget(self.lock_btn)

        settings_btn = QToolButton()
        settings_btn.setText("⚙")
        settings_btn.setToolTip("Settings")
        settings_btn.setFixedSize(32, 32)
        settings_btn.clicked.connect(self._open_settings)
        right.addWidget(settings_btn)

        right_widget = QWidget()
        right_widget.setLayout(right)
        right_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        outer.addWidget(left_widget)
        outer.addWidget(self.breadcrumb_label, stretch=1)
        outer.addWidget(right_widget)

        return bar

    # ── BOTTOM STATUS BAR ─────────────────────────────────────────────────────
    def _create_bottom_bar(self) -> QWidget:
        """Fixed 28 px status bar: counts | timestamp | save state."""
        bar = QWidget()
        bar.setObjectName("bottomBar")
        bar.setFixedHeight(28)
        bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(0)

        # left: word / char count
        self.sb_words = QLabel("0 words")
        self.sb_words.setObjectName("statusItem")
        layout.addWidget(self.sb_words)

        self._sb_sep(layout)

        self.sb_chars = QLabel("0 chars")
        self.sb_chars.setObjectName("statusItem")
        layout.addWidget(self.sb_chars)

        self._sb_sep(layout)

        self.sb_read = QLabel("< 1 min read")
        self.sb_read.setObjectName("statusItem")
        layout.addWidget(self.sb_read)

        layout.addStretch(1)

        # center: last edited + sync
        self.sb_edited = QLabel("")
        self.sb_edited.setObjectName("statusItem")
        self.sb_edited.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sb_edited)

        self._sb_sep(layout)

        self.sb_sync = QLabel("[Enc] Encrypted")
        self.sb_sync.setObjectName("statusItemAccent")
        layout.addWidget(self.sb_sync)

        self._sb_sep(layout)

        self.sb_creds = QLabel("")
        self.sb_creds.setObjectName("statusItem")
        self.sb_creds.setToolTip("Secure credentials stored")
        layout.addWidget(self.sb_creds)

        layout.addStretch(1)

        # right: autosave state
        self.autosave_label = QLabel("All changes saved")
        self.autosave_label.setObjectName("statusItem")
        self.autosave_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.autosave_label)

        self._sb_sep(layout)

        watermark = QLabel("starlex")
        watermark.setObjectName("watermark")
        watermark.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        watermark.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(watermark)

        return bar

    @staticmethod
    def _sb_sep(layout: QHBoxLayout):
        """Insert a thin vertical separator into a status-bar layout."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(14)
        sep.setObjectName("statusSep")
        layout.addSpacing(8)
        layout.addWidget(sep)
        layout.addSpacing(8)

    # ── PANEL TOGGLES ─────────────────────────────────────────────────────────
    def _toggle_sidebar(self):
        """Show / hide the left panel."""
        self.left_panel.setVisible(not self.left_panel.isVisible())

    def _toggle_notes_panel(self):
        """Show / hide the notes list within the left panel inner splitter."""
        visible = self.notes_panel.isVisible()
        self.notes_panel.setVisible(not visible)

    def _toggle_right_panel(self):
        """Show / hide the right panel."""
        self.right_panel.setVisible(not self.right_panel.isVisible())

    # ── LEFT PANEL (sidebar nav + notes list) ─────────────────────────────────
    def _create_left_panel(self) -> QWidget:
        """Left column: sidebar nav on top, notes list below — inner splitter."""
        container = QWidget()
        container.setObjectName("leftPanel")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # inner vertical splitter: nav section | notes list
        self.left_splitter = QSplitter(Qt.Orientation.Vertical)
        self.left_splitter.setObjectName("leftSplitter")
        self.left_splitter.setHandleWidth(2)
        self.left_splitter.setChildrenCollapsible(False)

        self.sidebar = self._create_sidebar()
        self.notes_panel = self._create_notes_panel()

        self.left_splitter.addWidget(self.sidebar)
        self.left_splitter.addWidget(self.notes_panel)
        self.left_splitter.setSizes([220, 9999])
        self.left_splitter.setStretchFactor(0, 0)
        self.left_splitter.setStretchFactor(1, 1)

        layout.addWidget(self.left_splitter)
        return container

    def _create_sidebar(self) -> QWidget:
        """Left column: navigation + notebooks."""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ─ section header
        hdr = QWidget()
        hdr.setObjectName("sidebarHeader")
        hdr.setFixedHeight(44)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(14, 0, 10, 0)
        vault_lbl = QLabel("VAULT")
        vault_lbl.setObjectName("sidebarSectionLabel")
        vault_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        hdr_l.addWidget(vault_lbl)
        hdr_l.addStretch()
        layout.addWidget(hdr)

        # ─ nav buttons
        nav = QWidget()
        nav.setObjectName("sidebarNav")
        nav_l = QVBoxLayout(nav)
        nav_l.setContentsMargins(8, 6, 8, 6)
        nav_l.setSpacing(2)

        self._nav_buttons = []

        self.btn_all_notes = self._create_sidebar_button("📋  All Notes")
        self.btn_all_notes.clicked.connect(self._show_all_notes)
        nav_l.addWidget(self.btn_all_notes)
        self._nav_buttons.append(self.btn_all_notes)

        self.btn_recent = self._create_sidebar_button("🕐  Recent")
        self.btn_recent.clicked.connect(self._show_recent)
        nav_l.addWidget(self.btn_recent)
        self._nav_buttons.append(self.btn_recent)

        self.btn_favorites = self._create_sidebar_button("⭐  Favorites")
        self.btn_favorites.clicked.connect(self._show_favorites)
        nav_l.addWidget(self.btn_favorites)
        self._nav_buttons.append(self.btn_favorites)

        self.btn_trash = self._create_sidebar_button("🗑  Trash")
        self.btn_trash.clicked.connect(self._show_trash)
        nav_l.addWidget(self.btn_trash)
        self._nav_buttons.append(self.btn_trash)

        layout.addWidget(nav)

        # ─ separator
        layout.addWidget(self._make_hsep())

        # ─ notebooks section label + New button
        nb_hdr = QWidget()
        nb_hdr.setFixedHeight(32)
        nb_hdr_l = QHBoxLayout(nb_hdr)
        nb_hdr_l.setContentsMargins(14, 0, 10, 0)
        nb_lbl = QLabel("NOTEBOOKS")
        nb_lbl.setObjectName("sidebarSectionLabel")
        nb_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        nb_hdr_l.addWidget(nb_lbl)
        nb_hdr_l.addStretch()
        btn_new_nb = QToolButton()
        btn_new_nb.setText("+")
        btn_new_nb.setFixedSize(20, 20)
        btn_new_nb.setToolTip("New notebook")
        btn_new_nb.clicked.connect(self._new_notebook)
        nb_hdr_l.addWidget(btn_new_nb)
        layout.addWidget(nb_hdr)

        # ─ notebooks list
        self.notebooks_container = QWidget()
        self.notebooks_layout = QVBoxLayout(self.notebooks_container)
        self.notebooks_layout.setContentsMargins(8, 0, 8, 0)
        self.notebooks_layout.setSpacing(2)
        layout.addWidget(self.notebooks_container)

        layout.addStretch()
        return sidebar
    
    def _create_sidebar_button(self, text: str) -> QPushButton:
        """Sidebar nav button — full-width, left-aligned."""
        btn = QPushButton(text)
        btn.setObjectName("sidebarButton")
        btn.setFixedHeight(34)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return btn

    @staticmethod
    def _make_hsep() -> QFrame:
        """Thin horizontal separator line."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("sidebarSep")
        sep.setFixedHeight(1)
        return sep
    
    def _create_notes_panel(self) -> QWidget:
        """Center-left column: note list with header + search."""
        panel = QWidget()
        panel.setObjectName("notesPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ─ panel header (44 px)
        hdr = QWidget()
        hdr.setObjectName("notesPanelHeader")
        hdr.setFixedHeight(44)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(12, 0, 8, 0)
        hdr_l.setSpacing(6)

        self.notes_title = QLabel("All Notes")
        self.notes_title.setObjectName("panelTitle")
        self.notes_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hdr_l.addWidget(self.notes_title)
        hdr_l.addStretch()

        btn_new_note = QPushButton("+")
        btn_new_note.setObjectName("iconButton")
        btn_new_note.setFixedSize(28, 28)
        btn_new_note.setToolTip("New note (Ctrl+N)")
        btn_new_note.clicked.connect(self._new_note)
        hdr_l.addWidget(btn_new_note)

        self.btn_empty_trash = QPushButton("Empty")
        self.btn_empty_trash.setObjectName("dangerButton")
        self.btn_empty_trash.setFixedSize(28, 28)
        self.btn_empty_trash.setToolTip("Empty trash")
        self.btn_empty_trash.clicked.connect(self._empty_trash)
        self.btn_empty_trash.setVisible(False)
        hdr_l.addWidget(self.btn_empty_trash)

        layout.addWidget(hdr)
        layout.addWidget(self._make_hsep())

        # ─ search (inside panel, below header)
        search_wrap = QWidget()
        search_wrap.setObjectName("searchWrap")
        sw_l = QHBoxLayout(search_wrap)
        sw_l.setContentsMargins(8, 6, 8, 6)

        # NOTE: self.search_box is created in _create_top_bar; here we add a
        # local panel search that also calls _on_search so both work.
        self.panel_search = QLineEdit()
        self.panel_search.setObjectName("panelSearch")
        self.panel_search.setPlaceholderText("Filter…")
        self.panel_search.setFixedHeight(28)
        self.panel_search.textChanged.connect(self._on_search)
        sw_l.addWidget(self.panel_search)
        layout.addWidget(search_wrap)

        # ─ note list (fills remaining space)
        self.notes_list = QListWidget()
        self.notes_list.setObjectName("notesList")
        self.notes_list.itemClicked.connect(self._on_note_selected)
        self.notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.notes_list.customContextMenuRequested.connect(self._show_note_context_menu)
        self.notes_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.notes_list, stretch=1)

        return panel
    
    # ── RIGHT PANEL (backlinks / properties / outline) ───────────────────────
    def _create_right_panel(self) -> QWidget:
        """Right column: properties, backlinks, outline — layout only."""
        panel = QWidget()
        panel.setObjectName("rightPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # header
        hdr = QWidget()
        hdr.setObjectName("rightPanelHeader")
        hdr.setFixedHeight(44)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(14, 0, 10, 0)
        lbl = QLabel("DETAILS")
        lbl.setObjectName("sidebarSectionLabel")
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        hdr_l.addWidget(lbl)
        hdr_l.addStretch()
        layout.addWidget(hdr)
        layout.addWidget(self._make_hsep())

        # inner vertical splitter for resizable panes
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_splitter.setObjectName("rightSplitter")
        self.right_splitter.setHandleWidth(2)
        self.right_splitter.setChildrenCollapsible(True)

        self.ai_panel = AIPanel(self.config)
        self.right_splitter.addWidget(self.ai_panel)
        self.right_splitter.setSizes([9999])

        layout.addWidget(self.right_splitter, stretch=1)
        return panel

    def _create_right_section(self, title: str, obj_name: str) -> QWidget:
        """A titled, scrollable pane with a detach button for the right panel."""
        pane = QWidget()
        pane.setObjectName(obj_name)

        v = QVBoxLayout(pane)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        sec_hdr = QWidget()
        sec_hdr.setObjectName("rightSectionHeader")
        sec_hdr.setFixedHeight(32)
        sh_l = QHBoxLayout(sec_hdr)
        sh_l.setContentsMargins(14, 0, 6, 0)
        sh_l.setSpacing(4)
        sec_lbl = QLabel(title)
        sec_lbl.setObjectName("sidebarSectionLabel")
        sec_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        sh_l.addWidget(sec_lbl)
        sh_l.addStretch()

        # detach button — pops section into a floating QDockWidget
        detach_btn = QToolButton()
        detach_btn.setText("⧉")
        detach_btn.setObjectName("detachButton")
        detach_btn.setFixedSize(20, 20)
        detach_btn.setToolTip(f"Float {title.title()} panel")
        detach_btn.clicked.connect(
            lambda _checked, t=title, o=obj_name, p=pane:
                self._detach_right_section(t, o, p))
        sh_l.addWidget(detach_btn)
        v.addWidget(sec_hdr)

        scroll = QScrollArea()
        scroll.setObjectName("rightSectionScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        placeholder = QLabel("—")
        placeholder.setObjectName("rightPlaceholder")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        placeholder.setContentsMargins(14, 8, 14, 8)
        scroll.setWidget(placeholder)
        v.addWidget(scroll, stretch=1)
        return pane

    def _detach_right_section(self, title: str, obj_name: str, source_pane: QWidget):
        """Float a right-panel section as a draggable overlay QDockWidget."""
        dock = QDockWidget(title, self)
        dock.setObjectName("floatingPane")
        dock.setAllowedAreas(Qt.DockWidgetArea.NoDockWidgetArea)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable)
        # Wrap a fresh placeholder so source_pane stays in the splitter
        proxy = QWidget()
        proxy.setObjectName(obj_name + "Float")
        pl = QVBoxLayout(proxy)
        pl.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("—")
        lbl.setObjectName("rightPlaceholder")
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        lbl.setContentsMargins(14, 8, 14, 8)
        pl.addWidget(lbl)
        dock.setWidget(proxy)
        dock.setFloating(True)
        dock.resize(320, 400)
        # Position near the right edge of the window
        geo = self.geometry()
        dock.move(geo.right() - 340, geo.top() + 80)
        dock.show()

    def _create_editor_panel(self) -> QWidget:
        """Center column: title bar + rich editor, edge-to-edge."""
        panel = QWidget()
        panel.setObjectName("editorPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ─ editor top bar (44 px): title input + theme toggle
        ebar = QWidget()
        ebar.setObjectName("editorTopBar")
        ebar.setFixedHeight(44)
        eb_l = QHBoxLayout(ebar)
        eb_l.setContentsMargins(20, 0, 12, 0)
        eb_l.setSpacing(8)

        self.editor_title = QLineEdit()
        self.editor_title.setObjectName("editorTitleInput")
        self.editor_title.setPlaceholderText("Untitled note…")
        self.editor_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.editor_title.setFrame(False)
        self.editor_title.textChanged.connect(self._on_title_changed)
        eb_l.addWidget(self.editor_title, stretch=1)

        layout.addWidget(ebar)
        layout.addWidget(self._make_hsep())

        # ─ rich editor (fills all remaining space)
        self.editor_content = EnhancedEditor()
        self.editor_content.setPlaceholderText(
            "Start writing...\n\nTip: use Edit menu to insert image or draw diagram")
        self.editor_content.textChanged.connect(self._on_content_changed)
        self.editor_content.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.editor_content, stretch=1)

        return panel
    
    def _create_formatting_toolbar(self) -> QWidget:
        """Stub — toolbar is now inside EnhancedEditor."""
        return QWidget()

    def _setup_menu_bar(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # ── File ──────────────────────────────────────────────────────────────
        file_menu = menubar.addMenu("File")

        new_action = QAction("New Note", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self._new_note)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        # Export submenu
        export_menu = file_menu.addMenu("Export")

        export_json = QAction("Export as JSON…", self)
        export_json.triggered.connect(lambda: self._export_notes("json"))
        export_menu.addAction(export_json)

        export_md = QAction("Export as Markdown…", self)
        export_md.triggered.connect(lambda: self._export_notes("markdown"))
        export_menu.addAction(export_md)

        export_txt = QAction("Export as Plain Text…", self)
        export_txt.triggered.connect(lambda: self._export_notes("text"))
        export_menu.addAction(export_txt)

        export_pdf = QAction("Export as PDF…", self)
        export_pdf.triggered.connect(lambda: self._export_notes("pdf"))
        export_menu.addAction(export_pdf)

        # Import submenu
        import_menu = file_menu.addMenu("Import")

        import_json = QAction("Import from JSON…", self)
        import_json.triggered.connect(lambda: self._import_notes("json"))
        import_menu.addAction(import_json)

        import_md = QAction("Import Markdown files…", self)
        import_md.triggered.connect(lambda: self._import_notes("markdown"))
        import_menu.addAction(import_md)

        import_txt = QAction("Import Text files…", self)
        import_txt.triggered.connect(lambda: self._import_notes("text"))
        import_menu.addAction(import_txt)

        file_menu.addSeparator()

        clear_db_action = QAction("Clear All Notes…", self)
        clear_db_action.triggered.connect(self._clear_all_notes)
        file_menu.addAction(clear_db_action)

        file_menu.addSeparator()

        self.lock_action = QAction("Lock", self)
        self.lock_action.setShortcut(QKeySequence("Ctrl+L"))
        self.lock_action.triggered.connect(self._toggle_lock)
        file_menu.addAction(self.lock_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ── Edit ──────────────────────────────────────────────────────────────
        edit_menu = menubar.addMenu("Edit")

        insert_image_action = QAction("Insert Image…", self)
        insert_image_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        insert_image_action.triggered.connect(self._insert_image)
        edit_menu.addAction(insert_image_action)

        insert_diagram_action = QAction("Insert Diagram…", self)
        insert_diagram_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
        insert_diagram_action.triggered.connect(self._insert_diagram)
        edit_menu.addAction(insert_diagram_action)

        edit_menu.addSeparator()

        new_cred_action = QAction("New Secure Credential…", self)
        new_cred_action.setShortcut(QKeySequence("Ctrl+Shift+K"))
        new_cred_action.triggered.connect(self._new_credential)
        edit_menu.addAction(new_cred_action)

        # ── View ──────────────────────────────────────────────────────────────
        view_menu = menubar.addMenu("View")

        theme_action = QAction("Toggle Theme", self)
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(theme_action)

        settings_action = QAction("Settings…", self)
        settings_action.triggered.connect(self._open_settings)
        view_menu.addAction(settings_action)

        # ── Help ──────────────────────────────────────────────────────────────
        menubar.addMenu("Help")
    
    def _setup_toolbar(self):
        """No separate QToolBar — actions live in the top bar."""
        pass
    
    def _setup_statusbar(self):
        """Native QStatusBar kept for showMessage() compatibility."""
        self.statusbar = QStatusBar()
        self.statusbar.setFixedHeight(0)
        self.setStatusBar(self.statusbar)
        self.encryption_label = QLabel("Encrypted")
        self.encryption_label.setObjectName("secondaryLabel")
        self.statusbar.addPermanentWidget(self.encryption_label)
    
    def _setup_shortcuts(self):
        """Keyboard shortcuts for panel visibility."""
        QShortcut(QKeySequence("Ctrl+\\"), self).activated.connect(self._toggle_sidebar)
        QShortcut(QKeySequence("Ctrl+B"),  self).activated.connect(self._toggle_right_panel)
        QShortcut(QKeySequence("Ctrl+Shift+K"), self).activated.connect(self._new_credential)
        QShortcut(QKeySequence("Ctrl+Shift+V"), self).activated.connect(self._toggle_vault_popup)
    
    def _setup_auto_save(self):
        """Setup auto-save timer."""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(2000)  # 2 seconds
    
    def _setup_auto_lock(self):
        """Setup auto-lock timer."""
        timeout = self.config.get("auto_lock_timeout", 300) * 1000
        self.auto_lock_timer = QTimer()
        self.auto_lock_timer.timeout.connect(self._lock_application)
        if timeout > 0:
            self.auto_lock_timer.start(timeout)

    def _reset_auto_lock_timer(self):
        """Restart the auto-lock countdown on any user activity."""
        if self.auto_lock_timer.isActive():
            self.auto_lock_timer.start()  # start() on an active QTimer restarts it

    def mousePressEvent(self, event):
        self._reset_auto_lock_timer()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self._reset_auto_lock_timer()
        super().keyPressEvent(event)
    
    def _apply_theme(self):
        """Apply current theme stylesheet."""
        self.setStyleSheet(self.theme_manager.get_stylesheet())
        is_dark = self.theme_manager.current_theme == ThemeMode.DARK
        if hasattr(self, 'btn_theme_toggle'):
            self.btn_theme_toggle.setText("☽" if is_dark else "☀")
            self.btn_theme_toggle.setToolTip(
                "Switch to light theme" if is_dark else "Switch to dark theme")
    
    def _toggle_theme(self):
        """Toggle between dark and light themes."""
        self.theme_manager.toggle_theme()
        self.config.set("theme", self.theme_manager.current_theme.value)
        self.config.save()
    
    def _on_theme_changed(self, theme_mode: str):
        """Handle theme change."""
        self._apply_theme()
        logger.info(f"Theme changed to: {theme_mode}")
    
    def _load_data(self):
        """Load initial data."""
        try:
            self._refresh_notebooks()
            self._show_all_notes()
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load data:\n{str(e)}")

    def _refresh_notebooks(self):
        """Rebuild the notebooks list in the sidebar."""
        # Clear existing buttons
        while self.notebooks_layout.count():
            child = self.notebooks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        notebooks = self.notebook_controller.get_all_notebooks()
        for notebook in notebooks:
            btn = self._create_sidebar_button(notebook.name)
            btn.clicked.connect(lambda checked, nb_id=notebook.id: self._show_notebook_notes(nb_id))
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, nb=notebook: self._show_notebook_context_menu(pos, nb))
            self.notebooks_layout.addWidget(btn)

    def _new_notebook(self):
        """Create a new notebook via input dialog."""
        name, ok = QInputDialog.getText(self, "New Notebook", "Notebook name:")
        if ok and name.strip():
            nb = self.notebook_controller.create_notebook(name.strip())
            if nb:
                self._refresh_notebooks()
                self.statusbar.showMessage(f"Created notebook '{nb.name}'", 3000)
            else:
                QMessageBox.warning(self, "Error", "Failed to create notebook.")

    def _show_notebook_context_menu(self, pos, notebook):
        """Right-click menu for a notebook button."""
        menu = QMenu(self)
        rename_action = menu.addAction("Rename")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        action = menu.exec(self.sender().mapToGlobal(pos))

        if action == rename_action:
            new_name, ok = QInputDialog.getText(
                self, "Rename Notebook", "New name:", text=notebook.name)
            if ok and new_name.strip():
                notebook.name = new_name.strip()
                if self.notebook_controller.update_notebook(notebook):
                    self._refresh_notebooks()
                    self.statusbar.showMessage(f"Renamed to '{new_name.strip()}'", 3000)
                else:
                    QMessageBox.warning(self, "Error", "Failed to rename notebook.")

        elif action == delete_action:
            reply = QMessageBox.question(
                self, "Delete Notebook",
                f"Delete '{notebook.name}'?\nNotes inside will not be deleted.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self.notebook_controller.delete_notebook(notebook.id):
                    self._refresh_notebooks()
                    self._show_all_notes()
                    self.statusbar.showMessage(f"Deleted notebook '{notebook.name}'", 3000)
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete notebook.")
    
    # ===== NOTE DISPLAY METHODS =====
    
    def _set_active_nav(self, active_btn: QPushButton):
        """Highlight the active sidebar nav button, clear the rest."""
        for btn in self._nav_buttons:
            btn.setProperty("active", btn is active_btn)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _show_all_notes(self):
        """Show all notes."""
        self._set_active_nav(self.btn_all_notes)
        self.notes_title.setText("All Notes")
        notes = self.note_controller.get_all_notes()
        self._populate_notes_list(notes)
        self.btn_empty_trash.setVisible(False)

    def _show_recent(self):
        """Show recent notes."""
        self._set_active_nav(self.btn_recent)
        self.notes_title.setText("Recent")
        notes = self.note_controller.get_all_notes()
        self._populate_notes_list(notes[:20])
        self.btn_empty_trash.setVisible(False)

    def _show_favorites(self):
        """Show favorite notes."""
        self._set_active_nav(self.btn_favorites)
        self.notes_title.setText("Favorites")
        notes = self.note_controller.get_favorite_notes()
        self._populate_notes_list(notes)
        self.btn_empty_trash.setVisible(False)

    def _show_trash(self):
        """Show deleted notes."""
        self._set_active_nav(self.btn_trash)
        self.notes_title.setText("Trash")
        notes = self.note_controller.get_trashed_notes()
        self._populate_notes_list(notes)
        self.btn_empty_trash.setVisible(len(notes) > 0)
        if notes:
            self.statusbar.showMessage(f"{len(notes)} notes in trash — right-click for options", 5000)
    
    def _show_notebook_notes(self, notebook_id: str):
        """Show notes from specific notebook."""
        notebook = self.notebook_controller.get_notebook(notebook_id)
        if notebook:
            self.notes_title.setText(notebook.name)
            notes = self.note_controller.get_notes_by_notebook(notebook_id)
            self._populate_notes_list(notes)
            self.btn_empty_trash.setVisible(False)
    
    def _populate_notes_list(self, notes):
        """Populate notes list with card widgets."""
        self.notes_list.clear()
        for note in notes:
            card = self._make_note_card(note)
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            item.setSizeHint(card.sizeHint())
            self.notes_list.addItem(item)
            self.notes_list.setItemWidget(item, card)

    def _make_note_card(self, note) -> QWidget:
        """Build a note list card: pin indicator + title + date + preview."""
        card = QWidget()
        card.setObjectName("noteCard")
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        # ── row 1: pin/fav badge + title ─────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(4)
        top.setContentsMargins(0, 0, 0, 0)

        if note.is_pinned:
            pin = QLabel("📌")
            pin.setFixedWidth(16)
            top.addWidget(pin)
        if note.is_favorite:
            fav = QLabel("⭐")
            fav.setFixedWidth(16)
            top.addWidget(fav)

        title_lbl = QLabel(note.title or "Untitled")
        title_lbl.setObjectName("noteCardTitle")
        title_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        title_lbl.setWordWrap(False)
        top.addWidget(title_lbl, stretch=1)

        # date — right-aligned
        try:
            date_str = note.modified_at.strftime("%b %d")
        except Exception:
            date_str = ""
        date_lbl = QLabel(date_str)
        date_lbl.setObjectName("noteCardMeta")
        date_lbl.setFont(QFont("Segoe UI", 10))
        top.addWidget(date_lbl)

        layout.addLayout(top)

        # ── row 2: preview text ───────────────────────────────────────────────
        preview = note.get_plain_text()[:80].replace("\n", " ").strip()
        if preview:
            prev_lbl = QLabel(preview)
            prev_lbl.setObjectName("noteCardPreview")
            prev_lbl.setFont(QFont("Segoe UI", 11))
            prev_lbl.setWordWrap(False)
            layout.addWidget(prev_lbl)

        return card
    
    def _on_note_selected(self, item: QListWidgetItem):
        """Handle note selection."""
        note_id = item.data(Qt.ItemDataRole.UserRole)
        self._load_note(note_id)
    
    def _load_note(self, note_id: str):
        """Load note into editor."""
        try:
            if self.is_modified and self.current_note:
                self._save_current_note()

            note = self.note_controller.get_note(note_id)
            if note:
                self.current_note = note
                self.current_note_id = note_id

                self.editor_title.setText(note.title or "")
                # content is stored as Qt HTML — load it directly
                if note.content and note.content.strip():
                    self.editor_content.setHtml(note.content)
                else:
                    self.editor_content.clear()

                self.is_modified = False
                self._update_word_count()
                if hasattr(self, 'breadcrumb_label'):
                    self.breadcrumb_label.setText(note.title or "Untitled")
                if hasattr(self, 'ai_panel'):
                    self.ai_panel.set_note_context(
                        note.title or "", note.get_plain_text())
                logger.info(f"Loaded note: {note_id}")

        except Exception as e:
            logger.error(f"Failed to load note: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load note:\n{str(e)}")
    
    # ===== NOTE EDITING METHODS =====
    
    def _new_note(self):
        """Create a new note."""
        try:
            if self.is_modified and self.current_note:
                self._save_current_note()
            
            default_notebook = self.notebook_controller.get_default_notebook()
            note = self.note_controller.create_note(
                title="Untitled Note",
                content="",
                notebook_id=default_notebook.id if default_notebook else None
            )
            
            if note:
                self.current_note = note
                self.current_note_id = note.id
                self.editor_title.setText(note.title)
                self.editor_content.clear()
                self.is_modified = False
                
                self._show_all_notes()
                
                self.statusbar.showMessage(f"Created new note", 3000)
                logger.info(f"Created note: {note.id}")
            else:
                self.statusbar.showMessage("Failed to create note", 3000)
        
        except Exception as e:
            logger.error(f"Failed to create note: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create note:\n{str(e)}")
    
    def _on_title_changed(self, text: str):
        """Handle title change — also update top-bar breadcrumb."""
        self.is_modified = True
        self.autosave_label.setText("Unsaved changes…")
        if hasattr(self, 'breadcrumb_label'):
            self.breadcrumb_label.setText(text or "Untitled")
    
    def _on_content_changed(self):
        """Handle content change — update bottom-bar counts."""
        self.is_modified = True
        self.autosave_label.setText("Unsaved changes…")
        self._update_word_count()

    def _update_word_count(self):
        """Refresh bottom-bar word / char / reading-time labels."""
        text = self.editor_content.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        mins  = max(1, words // 200)
        if hasattr(self, 'sb_words'):
            self.sb_words.setText(f"{words} words")
            self.sb_chars.setText(f"{chars} chars")
            self.sb_read.setText(f"{mins} min read")
    
    def _auto_save(self):
        """Auto-save current note."""
        if self.is_modified and self.current_note:
            self._save_current_note()
    
    def _save_current_note(self):
        """Save current note."""
        try:
            if not self.current_note:
                return
            
            self.current_note.title = self.editor_title.text() or "Untitled"
            
            content = self.editor_content.toHtml()
            self.current_note.content = content
            
            self.current_note.updated_at = datetime.now()
            
            if self.note_controller.update_note(self.current_note):
                self.is_modified = False
                self.autosave_label.setText("All changes saved")
                if hasattr(self, 'sb_edited'):
                    ts = datetime.now().strftime("%H:%M")
                    self.sb_edited.setText(f"Saved {ts}")
                
                for i in range(self.notes_list.count()):
                    item = self.notes_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == self.current_note.id:
                        item.setText(self.current_note.title)
                        break
                
                logger.info(f"Saved note: {self.current_note.id}")
            else:
                self.autosave_label.setText("Save failed!")
        
        except Exception as e:
            logger.error(f"Failed to save note: {e}", exc_info=True)
            self.autosave_label.setText(f"Save error!")
    
    def _on_search(self, query: str):
        """Handle search."""
        if not query:
            self._show_all_notes()
            return
        
        notes = self.note_controller.search_notes(query)
        self._populate_notes_list(notes)
    
    def _show_note_context_menu(self, position):
        """Show context menu for note list item."""
        item = self.notes_list.itemAt(position)
        if not item:
            return
        
        note_id = item.data(Qt.ItemDataRole.UserRole)
        note = self.note_controller.get_note(note_id)
        
        if not note:
            return
        
        menu = QMenu(self)
        
        if note.is_trashed:
            # Trash context menu
            restore_action = menu.addAction("Restore")
            restore_action.triggered.connect(lambda: self._restore_note(note_id))
            
            menu.addSeparator()
            
            delete_action = menu.addAction("Delete Permanently")
            delete_action.triggered.connect(lambda: self._permanent_delete_note(note_id))
        else:
            # Normal note context menu
            favorite_text = "Remove from Favorites" if note.is_favorite else "Add to Favorites"
            favorite_action = menu.addAction(favorite_text)
            favorite_action.triggered.connect(lambda: self._toggle_favorite(note_id))
            
            pin_text = "Unpin" if note.is_pinned else "Pin"
            pin_action = menu.addAction(pin_text)
            pin_action.triggered.connect(lambda: self._toggle_pin(note_id))
            
            menu.addSeparator()
            
            delete_action = menu.addAction("Move to Trash")
            delete_action.triggered.connect(lambda: self._delete_note_by_id(note_id))
        
        menu.exec(self.notes_list.mapToGlobal(position))
    
    def _restore_note(self, note_id: str):
        """Restore a note from trash."""
        try:
            if self.note_controller.restore_note(note_id):
                self.statusbar.showMessage("Note restored", 3000)
                logger.info(f"Restored note: {note_id}")
                self._show_trash()  # Refresh trash view
            else:
                QMessageBox.warning(self, "Error", "Failed to restore note.")
        except Exception as e:
            logger.error(f"Failed to restore note: {e}")
            QMessageBox.critical(self, "Error", f"Failed to restore note:\n{str(e)}")
    
    def _permanent_delete_note(self, note_id: str):
        """Permanently delete a note."""
        reply = QMessageBox.warning(
            self,
            "Permanent Delete",
            "Are you sure you want to permanently delete this note?\n\n⚠️ This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.note_controller.delete_note(note_id, permanent=True):
                    self.statusbar.showMessage("Note permanently deleted", 3000)
                    logger.info(f"Permanently deleted note: {note_id}")
                    
                    # Clear editor if this was the current note
                    if self.current_note_id == note_id:
                        self.editor_title.clear()
                        self.editor_content.clear()
                        self.current_note = None
                        self.current_note_id = None
                        self.is_modified = False
                    
                    self._show_trash()  # Refresh trash view
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete note.")
            except Exception as e:
                logger.error(f"Failed to permanently delete note: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete note:\n{str(e)}")
    
    def _delete_note_by_id(self, note_id: str):
        """Delete a note by ID (soft delete)."""
        try:
            note = self.note_controller.get_note(note_id)
            if note:
                reply = QMessageBox.question(
                    self,
                    "Delete Note",
                    f"Move '{note.title}' to trash?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    if self.note_controller.delete_note(note_id, permanent=False):
                        self.statusbar.showMessage(f"Moved to trash", 3000)
                        logger.info(f"Deleted note: {note_id}")
                        
                        # Clear editor if this was the current note
                        if self.current_note_id == note_id:
                            self.editor_title.clear()
                            self.editor_content.clear()
                            self.current_note = None
                            self.current_note_id = None
                            self.is_modified = False
                        
                        self._show_all_notes()  # Refresh view
                    else:
                        QMessageBox.warning(self, "Error", "Failed to delete note.")
        except Exception as e:
            logger.error(f"Failed to delete note: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete note:\n{str(e)}")
    
    def _toggle_favorite(self, note_id: str):
        """Toggle favorite status."""
        try:
            if self.note_controller.toggle_favorite(note_id):
                self.statusbar.showMessage("Favorite status updated", 2000)
                self._show_all_notes()  # Refresh view
        except Exception as e:
            logger.error(f"Failed to toggle favorite: {e}")
    
    def _toggle_pin(self, note_id: str):
        """Toggle pin status."""
        try:
            if self.note_controller.toggle_pin(note_id):
                self.statusbar.showMessage("Pin status updated", 2000)
                self._show_all_notes()  # Refresh view
        except Exception as e:
            logger.error(f"Failed to toggle pin: {e}")
    
    def _empty_trash(self):
        """Empty all notes from trash permanently."""
        trashed_notes = self.note_controller.get_trashed_notes()
        
        if not trashed_notes:
            QMessageBox.information(self, "Trash Empty", "Trash is already empty.")
            return
        
        reply = QMessageBox.warning(
            self,
            "Empty Trash",
            f"Are you sure you want to permanently delete all {len(trashed_notes)} notes in trash?\n\n⚠️ This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.note_controller.empty_trash():
                    self.statusbar.showMessage(f"Permanently deleted {len(trashed_notes)} notes", 3000)
                    logger.info(f"Emptied trash: {len(trashed_notes)} notes deleted")
                    
                    # Clear editor if current note was in trash
                    if self.current_note and self.current_note.is_trashed:
                        self.editor_title.clear()
                        self.editor_content.clear()
                        self.current_note = None
                        self.current_note_id = None
                        self.is_modified = False
                    
                    self._show_trash()  # Refresh trash view
                else:
                    QMessageBox.warning(self, "Error", "Failed to empty trash.")
            except Exception as e:
                logger.error(f"Failed to empty trash: {e}")
                QMessageBox.critical(self, "Error", f"Failed to empty trash:\n{str(e)}")
    
    def _clear_all_notes(self):
        """Clear all notes from the database (nuclear option)."""
        reply = QMessageBox.warning(
            self,
            "Clear All Notes",
            "⚠️ DANGER: This will permanently delete ALL notes in the database!\n\n"
            "This includes:\n"
            "• All active notes\n"
            "• All trashed notes\n"
            "• All notebooks\n\n"
            "This action CANNOT be undone!\n\n"
            "Type 'DELETE ALL' to confirm:",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Additional confirmation with text input
            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(
                self,
                "Final Confirmation",
                "Type 'DELETE ALL' to confirm:"
            )
            
            if ok and text == "DELETE ALL":
                try:
                    # Delete all notes
                    self.note_controller.db.execute("DELETE FROM notes")
                    
                    # Delete all custom notebooks
                    self.note_controller.db.execute("DELETE FROM notebooks WHERE is_default = 0")
                    
                    # Reset default notebook
                    self.note_controller.db.execute("UPDATE notebooks SET note_count = 0 WHERE is_default = 1")
                    
                    # Vacuum database
                    self.note_controller.db.execute("VACUUM")
                    
                    logger.info("Cleared all notes from database")
                    
                    # Clear editor
                    self.editor_title.clear()
                    self.editor_content.clear()
                    self.current_note = None
                    self.current_note_id = None
                    self.is_modified = False
                    
                    # Refresh view
                    self._show_all_notes()
                    
                    QMessageBox.information(
                        self,
                        "Database Cleared",
                        "All notes have been permanently deleted.\n\n"
                        "The database has been reset and is ready for new notes."
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to clear database: {e}")
                    QMessageBox.critical(self, "Error", f"Failed to clear database:\n{str(e)}")
            else:
                self.statusbar.showMessage("Clear cancelled", 2000)
    
    # ===== FORMATTING METHODS =====
    # (Formatting is handled inside EnhancedEditor — these are kept for
    #  any legacy callers and delegate to the editor widget.)

    def _insert_image(self):
        """Delegate image insertion to EnhancedEditor."""
        self.editor_content.insert_image()

    def _insert_diagram(self):
        """Delegate diagram insertion to EnhancedEditor."""
        self.editor_content.insert_diagram()
    
    def _delete_current_note(self):
        """Delete the current note."""
        if not self.current_note:
            QMessageBox.warning(self, "No Note", "No note is currently open.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Note",
            f"Are you sure you want to delete '{self.current_note.title}'?\n\nThis will move the note to trash.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete note (soft delete - move to trash)
                if self.note_controller.delete_note(self.current_note.id, permanent=False):
                    logger.info(f"Deleted note: {self.current_note.id}")
                    self.statusbar.showMessage(f"Moved '{self.current_note.title}' to trash", 3000)
                    
                    # Clear editor
                    self.editor_title.clear()
                    self.editor_content.clear()
                    self.current_note = None
                    self.current_note_id = None
                    self.is_modified = False
                    
                    # Refresh notes list
                    self._show_all_notes()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete note.")
            
            except Exception as e:
                logger.error(f"Failed to delete note: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete note:\n{str(e)}")
    # ===== SECURITY METHODS =====
    
    def _toggle_lock(self):
        """Toggle lock state."""
        if self.is_locked:
            self._unlock_application()
        else:
            self._lock_application()
    
    def _toggle_vault_popup(self):
        """Show/hide the credential vault as a centered dialog."""
        if not hasattr(self, '_vault_popup'):
            self._vault_popup = QFrame(self, Qt.WindowType.Dialog)
            self._vault_popup.setObjectName("vaultPopup")
            self._vault_popup.setFixedSize(380, 560)
            self._vault_popup.setWindowTitle("Password Manager")
            layout = QVBoxLayout(self._vault_popup)
            layout.setContentsMargins(0, 0, 0, 0)
            self.credential_panel = CredentialPanel(self.credential_controller)
            self.credential_panel.count_changed.connect(self._on_credential_count_changed)
            layout.addWidget(self.credential_panel)

        if self._vault_popup.isVisible():
            self._vault_popup.hide()
            return

        # Center over main window
        geo = self.geometry()
        x = geo.x() + (geo.width() - self._vault_popup.width()) // 2
        y = geo.y() + (geo.height() - self._vault_popup.height()) // 2
        self._vault_popup.move(x, y)
        self._vault_popup.show()

    def _new_credential(self):
        """Open new credential dialog; opens vault popup if needed."""
        if not self.credential_controller.is_unlocked:
            self._toggle_vault_popup()
            self.statusbar.showMessage(
                "Unlock the Password Manager first.", 4000)
            return
        from src.ui.credential_dialog import CredentialDialog
        dlg = CredentialDialog(self.credential_controller, parent=self)
        if dlg.exec():
            self.credential_panel.refresh()

    def _on_credential_count_changed(self, count: int):
        """Update status bar credential count label."""
        if hasattr(self, 'sb_creds'):
            self.sb_creds.setText(f"[Key] {count} creds" if count else "")

    def _import_notes(self, fmt: str):
        """Import notes from file(s)."""
        from src.utils.export_import import ExportImportManager
        mgr = ExportImportManager(self.note_controller, self.encryption_service)

        if fmt == "json":
            path, _ = QFileDialog.getOpenFileName(
                self, "Import from JSON", "", "JSON files (*.json)")
            if not path:
                return
            count, err = mgr.import_from_json(path)
        elif fmt == "markdown":
            paths, _ = QFileDialog.getOpenFileNames(
                self, "Import Markdown files", "", "Markdown files (*.md *.markdown)")
            if not paths:
                return
            count, err = mgr.import_from_markdown(paths)
        elif fmt == "text":
            paths, _ = QFileDialog.getOpenFileNames(
                self, "Import Text files", "", "Text files (*.txt)")
            if not paths:
                return
            count, err = mgr.import_from_text(paths)
        else:
            return

        if err:
            QMessageBox.warning(self, "Import Failed", err)
            return

        self._show_all_notes()

        if count:
            QMessageBox.information(
                self, "Import Complete",
                f"Successfully imported {count} note(s).\n"
                "They are now visible in All Notes."
            )
            # Select the first imported note so user can see it immediately
            if self.notes_list.count() > 0:
                first_item = self.notes_list.item(0)
                self.notes_list.setCurrentItem(first_item)
                self._on_note_selected(first_item)
        else:
            QMessageBox.warning(self, "Import", "No notes were imported.")

    def _export_notes(self, fmt: str):
        """Export all non-trashed notes in the chosen format."""
        from src.utils.export_import import ExportImportManager
        notes = self.note_controller.get_all_notes()
        if not notes:
            QMessageBox.information(self, "Export", "No notes to export.")
            return

        mgr = ExportImportManager(self.note_controller, self.encryption_service)

        # get_all_notes() omits content for performance — fetch full notes for export
        if fmt in ("pdf", "json", "markdown", "text"):
            notes = [self.note_controller.get_note(n.id) for n in notes]
            notes = [n for n in notes if n]  # drop any None

        if fmt == "json":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export as JSON", "notes_export.json", "JSON files (*.json)")
            if path:
                ok = mgr.export_notes_to_json(notes, path)
        elif fmt == "markdown":
            path = QFileDialog.getExistingDirectory(self, "Select folder for Markdown files")
            if path:
                ok = mgr.export_to_markdown(notes, path)
        elif fmt == "text":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export as Plain Text", "notes_export.txt", "Text files (*.txt)")
            if path:
                ok = mgr.export_to_text(notes, path)
        elif fmt == "pdf":
            path, _ = QFileDialog.getSaveFileName(
                self, "Export as PDF", "notes_export.pdf", "PDF files (*.pdf)")
            if path:
                ok = mgr.export_to_pdf(notes, path)
        else:
            return

        if path:
            if ok:
                self.statusbar.showMessage(f"Exported {len(notes)} notes", 4000)
            else:
                QMessageBox.warning(self, "Export Failed", "Export could not be completed.")

    def _open_settings(self):
        """Open the settings dialog."""
        from src.ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self.config, parent=self)
        dlg.exec()

    def _lock_application(self):
        """Lock the application."""
        if not self.is_locked:
            if self.is_modified and self.current_note:
                self._save_current_note()

            self.is_locked = True
            self.encryption_service.clear_cached_key()
            self.credential_controller.lock()
            self.lock_action.setText("Unlock")
            if hasattr(self, 'lock_btn'):
                self.lock_btn.setText("🔓")
                self.lock_btn.setToolTip("Unlock vault (Ctrl+L)")
            self.statusbar.showMessage("Application locked")
            self.locked.emit()

            self.editor_title.clear()
            self.editor_content.clear()
            self.current_note = None
            self.current_note_id = None
            if hasattr(self, 'breadcrumb_label'):
                self.breadcrumb_label.setText("")
            logger.info("Application locked")

    def _unlock_application(self):
        """Unlock the application."""
        self.is_locked = False
        self.lock_action.setText("Lock")
        if hasattr(self, 'lock_btn'):
            self.lock_btn.setText("🔒")
            self.lock_btn.setToolTip("Lock vault (Ctrl+L)")
        self.statusbar.showMessage("Application unlocked")
        self.unlocked.emit()
        logger.info("Application unlocked")
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.is_modified and self.current_note:
            self._save_current_note()
        sizes = self.main_splitter.sizes()
        if len(sizes) >= 3:
            self.config.set("left_panel_width",  sizes[0])
            self.config.set("right_panel_width", sizes[2])
        self.config.save()

        self.encryption_service.clear_cached_key()
        logger.info("Application closing")
        event.accept()