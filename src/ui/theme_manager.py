"""Professional theme manager with dark/light mode support."""
import logging
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"


class ThemeManager(QObject):
    """
    Manages application theming.
    Dark  = cyberpunk / futuristic neon (2026 aesthetic)
    Light = clean modern professional
    """

    theme_changed = pyqtSignal(str)

    # ── Dark palette ──────────────────────────────────────────────────────────
    DARK_THEME = {
        # backgrounds — deep navy/charcoal hierarchy
        'bg_main':          '#0e1117',
        'bg_panel':         '#161b27',
        'bg_card':          '#1c2333',
        'bg_elevated':      '#212840',
        # text
        'text_primary':     '#e6edf3',
        'text_secondary':   '#8b949e',
        'text_dim':         '#484f58',
        # accents — electric indigo + teal
        'accent':           '#58a6ff',
        'accent_hover':     '#79b8ff',
        'accent_active':    '#388bfd',
        'accent_purple':    '#bc8cff',
        'accent_magenta':   '#f778ba',
        'accent_green':     '#3fb950',
        # semantic
        'success':          '#3fb950',
        'success_bg':       'rgba(63,185,80,0.10)',
        'error':            '#f85149',
        'error_bg':         'rgba(248,81,73,0.10)',
        'warning':          '#d29922',
        'warning_bg':       'rgba(210,153,34,0.10)',
        # surfaces / borders
        'disabled':         '#21262d',
        'disabled_text':    '#484f58',
        'border':           '#21262d',
        'border_light':     '#30363d',
        'border_neon':      'rgba(88,166,255,0.20)',
        'border_purple':    'rgba(188,140,255,0.18)',
        # inputs
        'input_bg':         '#0d1117',
        'input_border':     '#30363d',
        'input_placeholder':'#484f58',
        # glass
        'glass_bg':         'rgba(22,27,39,0.85)',
        'glass_border':     'rgba(88,166,255,0.15)',
        # shadows (unused in QSS but kept for reference)
        'glow_cyan':        '0 0 0 3px rgba(88,166,255,0.25)',
        'glow_purple':      '0 0 0 3px rgba(188,140,255,0.25)',
        'glow_subtle':      '0 4px 16px rgba(0,0,0,0.40)',
        'glow_green':       '0 0 0 3px rgba(63,185,80,0.30)',
        'glow_red':         '0 0 0 3px rgba(248,81,73,0.30)',
    }

    # ── Clean light palette ───────────────────────────────────────────────────
    LIGHT_THEME = {
        'bg_main':          '#f8fafc',
        'bg_panel':         '#f1f5f9',
        'bg_card':          '#ffffff',
        'bg_elevated':      '#ffffff',
        'text_primary':     '#0f172a',
        'text_secondary':   '#475569',
        'text_dim':         '#94a3b8',
        'accent':           '#2563eb',
        'accent_hover':     '#3b82f6',
        'accent_active':    '#1d4ed8',
        'accent_purple':    '#7c3aed',
        'accent_magenta':   '#db2777',
        'accent_green':     '#16a34a',
        'success':          '#16a34a',
        'success_bg':       'rgba(22,163,74,0.08)',
        'error':            '#dc2626',
        'error_bg':         'rgba(220,38,38,0.08)',
        'warning':          '#d97706',
        'warning_bg':       'rgba(217,119,6,0.08)',
        'disabled':         '#e2e8f0',
        'disabled_text':    '#94a3b8',
        'border':           '#e2e8f0',
        'border_light':     '#cbd5e1',
        'border_neon':      'rgba(37,99,235,0.30)',
        'border_purple':    'rgba(124,58,237,0.20)',
        'input_bg':         '#ffffff',
        'input_border':     '#cbd5e1',
        'input_placeholder':'#94a3b8',
        'glass_bg':         'rgba(255,255,255,0.80)',
        'glass_border':     'rgba(37,99,235,0.15)',
        'glow_cyan':        '0 0 0 2px rgba(37,99,235,0.20)',
        'glow_purple':      '0 0 0 2px rgba(124,58,237,0.20)',
        'glow_subtle':      '0 2px 8px rgba(0,0,0,0.06)',
    }

    def __init__(self):
        super().__init__()
        self.current_theme = ThemeMode.DARK
        self.colors = self.DARK_THEME.copy()
        logger.info("ThemeManager initialised — cyberpunk dark")

    def set_theme(self, theme_mode: ThemeMode):
        self.current_theme = theme_mode
        self.colors = (self.DARK_THEME if theme_mode == ThemeMode.DARK
                       else self.LIGHT_THEME).copy()
        logger.info(f"Theme → {theme_mode.value}")
        self.theme_changed.emit(theme_mode.value)

    def toggle_theme(self):
        self.set_theme(ThemeMode.LIGHT if self.current_theme == ThemeMode.DARK
                       else ThemeMode.DARK)

    def get_color(self, key: str) -> str:
        return self.colors.get(key, '#ffffff')

    # ─────────────────────────────────────────────────────────────────────────
    def get_stylesheet(self) -> str:
        """Return the complete QSS for the current theme."""
        c = self.colors
        is_dark = self.current_theme == ThemeMode.DARK

        neon_border = c['border_neon']
        accent      = c['accent']
        accent_h    = c['accent_hover']
        accent_a    = c['accent_active']
        text1       = c['text_primary']
        text2       = c['text_secondary']
        text3       = c['text_dim']
        bg0         = c['bg_main']
        bg1         = c['bg_panel']
        bg2         = c['bg_card']
        bg3         = c['bg_elevated']
        brd         = c['border']
        brd_l       = c['border_light']
        inp_bg      = c['input_bg']
        inp_brd     = c['input_border']
        err         = c['error']
        ok          = c['success']
        dis         = c['disabled']
        dis_t       = c['disabled_text']

        hover_bg  = ('rgba(88,166,255,0.08)'  if is_dark else 'rgba(37,99,235,0.06)')
        sel_bg    = ('rgba(88,166,255,0.15)'  if is_dark else 'rgba(37,99,235,0.12)')
        sel_border = accent
        sidebar_sep = (f'1px solid {brd}' if is_dark else f'1px solid {brd}')

        btn_fg = '#0d1117' if is_dark else '#ffffff'
        cred_gen_bg = 'rgba(88,166,255,0.10)' if is_dark else 'rgba(37,99,235,0.08)'
        totp_bg = 'rgba(88,166,255,0.07)' if is_dark else 'rgba(37,99,235,0.05)'

        return f"""

/* ── Base ─────────────────────────────────────────────────────────────────── */
QMainWindow, QDialog {{
    background-color: {bg0};
    color: {text1};
}}

QWidget {{
    background-color: {bg0};
    color: {text1};
    font-family: 'Segoe UI', 'Inter', 'SF Pro Text', system-ui, sans-serif;
    font-size: 13px;
}}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
QWidget#sidebar, QWidget#modernSidebar, QWidget#leftPanel {{
    background-color: {bg1};
    border-right: 1px solid {brd};
}}

/* ── Splitter ─────────────────────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {brd};
    width: 1px;
    height: 1px;
}}
QSplitter::handle:hover {{
    background-color: {accent};
}}

/* ── Menu bar ─────────────────────────────────────────────────────────────── */
QMenuBar {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
    padding: 2px 4px;
    spacing: 2px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 5px 12px;
    border-radius: 5px;
    color: {text2};
    font-size: 13px;
}}
QMenuBar::item:selected {{
    background-color: {hover_bg};
    color: {text1};
}}
QMenuBar::item:pressed {{
    background-color: {sel_bg};
    color: {accent};
}}

QMenu {{
    background-color: {bg2};
    border: 1px solid {neon_border};
    border-radius: 10px;
    padding: 6px 4px;
}}
QMenu::item {{
    padding: 8px 28px 8px 16px;
    border-radius: 6px;
    color: {text1};
    font-size: 13px;
    margin: 1px 4px;
}}
QMenu::item:selected {{
    background-color: {hover_bg};
    color: {accent};
}}
QMenu::separator {{
    height: 1px;
    background: {brd};
    margin: 4px 12px;
}}

/* ── Toolbar ──────────────────────────────────────────────────────────────── */
QToolBar {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
    spacing: 4px;
    padding: 4px 8px;
}}
QToolBar::separator {{
    background: {brd_l};
    width: 1px;
    margin: 4px 6px;
}}
QToolBar QToolButton {{
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 5px 8px;
    color: {text2};
    font-size: 13px;
    min-width: 24px;
}}
QToolBar QToolButton:hover {{
    background-color: {hover_bg};
    color: {accent};
}}
QToolBar QToolButton:checked {{
    background-color: {sel_bg};
    color: {accent};
    border: 1px solid {neon_border};
}}
QToolBar QToolButton:pressed {{
    background-color: {sel_bg};
    color: {accent_a};
}}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {accent};
    color: {'#05070f' if is_dark else '#ffffff'};
    border: none;
    border-radius: 7px;
    padding: 7px 18px;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background-color: {accent_h};
}}
QPushButton:pressed {{
    background-color: {accent_a};
}}
QPushButton:disabled {{
    background-color: {dis};
    color: {dis_t};
    border: 1px solid {brd};
}}

QPushButton#secondaryButton {{
    background-color: transparent;
    border: 1px solid {brd_l};
    color: {text1};
}}
QPushButton#secondaryButton:hover {{
    border-color: {accent};
    color: {accent};
    background-color: {hover_bg};
}}

QPushButton#dangerButton {{
    background-color: {err};
    color: #ffffff;
}}
QPushButton#dangerButton:hover {{
    background-color: #ff4d6a;
}}

/* Sidebar nav buttons */
QPushButton#secondaryButton[text-align="left"] {{
    text-align: left;
    padding-left: 14px;
}}

QPushButton#sidebarButton {{
    background-color: transparent;
    border: none;
    border-radius: 7px;
    padding: 9px 14px;
    text-align: left;
    color: {text2};
    font-size: 13px;
    font-weight: 400;
}}
QPushButton#sidebarButton:hover {{
    background-color: {hover_bg};
    color: {text1};
}}
QPushButton#sidebarButton[active="true"] {{
    background-color: {sel_bg};
    color: {accent};
    border-left: 2px solid {accent};
    padding-left: 12px;
}}

QPushButton#sectionHeader {{
    background: transparent;
    border: none;
    padding: 6px 4px;
    text-align: left;
    color: {text3};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}}
QPushButton#sectionHeader:hover {{
    color: {text2};
}}

QPushButton#addButton {{
    background: transparent;
    border: 1px dashed {brd_l};
    color: {text3};
    padding: 7px;
    font-size: 12px;
    border-radius: 6px;
}}
QPushButton#addButton:hover {{
    border-color: {accent};
    color: {accent};
    background-color: {hover_bg};
}}

/* ── Line edit ────────────────────────────────────────────────────────────── */
QLineEdit {{
    background-color: {inp_bg};
    color: {text1};
    border: 1px solid {inp_brd};
    border-radius: 7px;
    padding: 7px 12px;
    font-size: 13px;
    selection-background-color: {accent};
    selection-color: {'#05070f' if is_dark else '#ffffff'};
}}
QLineEdit:focus {{
    border-color: {accent};
    background-color: {bg2};
}}
QLineEdit:hover {{
    border-color: {brd_l};
}}
QLineEdit[readOnly="true"] {{
    color: {text2};
    background-color: {bg1};
}}

/* ── Text edit / editor ───────────────────────────────────────────────────── */
QTextEdit {{
    background-color: {inp_bg};
    color: {text1};
    border: 1px solid {inp_brd};
    border-radius: 8px;
    padding: 16px 20px;
    font-size: 15px;
    line-height: 1.7;
    selection-background-color: {accent};
    selection-color: {'#05070f' if is_dark else '#ffffff'};
}}
QTextEdit:focus {{
    border-color: {accent};
    background-color: {bg2};
}}

/* ── Plain text edit ──────────────────────────────────────────────────────── */
QPlainTextEdit {{
    background-color: {inp_bg};
    color: {text1};
    border: 1px solid {inp_brd};
    border-radius: 8px;
    padding: 14px 18px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    selection-background-color: {accent};
    selection-color: {'#05070f' if is_dark else '#ffffff'};
}}
QPlainTextEdit:focus {{
    border-color: {accent};
}}

/* ── List widget (note list) ──────────────────────────────────────────────── */
QListWidget {{
    background-color: {bg1};
    border: none;
    outline: none;
    padding: 4px;
}}
QListWidget::item {{
    background-color: {bg2};
    border: 1px solid {brd};
    border-radius: 8px;
    padding: 11px 14px;
    margin: 3px 6px;
    color: {text1};
}}
QListWidget::item:hover {{
    background-color: {hover_bg};
    border-color: {brd_l};
    color: {text1};
}}
QListWidget::item:selected {{
    background-color: {sel_bg};
    border-color: {sel_border};
    color: {accent};
}}

/* ── Tree widget ──────────────────────────────────────────────────────────── */
QTreeWidget {{
    background-color: {bg1};
    border: none;
    outline: none;
}}
QTreeWidget::item {{
    padding: 5px 8px;
    border-radius: 5px;
    color: {text2};
}}
QTreeWidget::item:hover {{
    background-color: {hover_bg};
    color: {text1};
}}
QTreeWidget::item:selected {{
    background-color: {sel_bg};
    color: {accent};
}}
QTreeWidget::branch {{
    background: transparent;
}}

/* ── Tab widget ───────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {brd};
    border-radius: 8px;
    background-color: {bg2};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {bg1};
    border: 1px solid {brd};
    border-bottom: none;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    padding: 7px 18px;
    margin-right: 2px;
    color: {text2};
    font-size: 13px;
}}
QTabBar::tab:selected {{
    background-color: {bg2};
    color: {accent};
    border-bottom-color: {bg2};
    border-top: 2px solid {accent};
}}
QTabBar::tab:hover:!selected {{
    background-color: {hover_bg};
    color: {text1};
}}

/* ── Scrollbars ───────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {brd_l};
    border-radius: 4px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {accent};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {brd_l};
    border-radius: 4px;
    min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {accent};
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* ── Status bar ───────────────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {bg1};
    border-top: 1px solid {brd};
    color: {text3};
    font-size: 11px;
    padding: 0 8px;
}}
QStatusBar QLabel {{
    color: {text3};
    font-size: 11px;
    padding: 2px 6px;
    background: transparent;
}}

/* ── Labels ───────────────────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    color: {text1};
}}
QLabel#secondaryLabel {{
    color: {text3};
    font-size: 11px;
}}

/* ── Checkboxes ───────────────────────────────────────────────────────────── */
QCheckBox {{
    spacing: 8px;
    color: {text1};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border: 1px solid {brd_l};
    border-radius: 4px;
    background-color: {inp_bg};
}}
QCheckBox::indicator:hover {{
    border-color: {accent};
}}
QCheckBox::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}

/* ── Combo box ────────────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {inp_bg};
    border: 1px solid {inp_brd};
    border-radius: 7px;
    padding: 5px 12px;
    color: {text1};
    font-size: 13px;
    min-width: 90px;
}}
QComboBox:hover {{
    border-color: {brd_l};
}}
QComboBox:focus {{
    border-color: {accent};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background-color: {bg2};
    border: 1px solid {neon_border};
    border-radius: 7px;
    color: {text1};
    selection-background-color: {sel_bg};
    selection-color: {accent};
    outline: none;
}}

/* ── Spin box ─────────────────────────────────────────────────────────────── */
QSpinBox, QDoubleSpinBox {{
    background-color: {inp_bg};
    border: 1px solid {inp_brd};
    border-radius: 6px;
    padding: 4px 8px;
    color: {text1};
    font-size: 13px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {accent};
}}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: transparent;
    border: none;
    width: 16px;
}}

/* ── Font combo box ───────────────────────────────────────────────────────── */
QFontComboBox {{
    background-color: {inp_bg};
    border: 1px solid {inp_brd};
    border-radius: 6px;
    padding: 4px 8px;
    color: {text1};
    font-size: 13px;
}}
QFontComboBox:focus {{
    border-color: {accent};
}}

/* ── Progress bar ─────────────────────────────────────────────────────────── */
QProgressBar {{
    background-color: {brd};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {accent};
    border-radius: 4px;
}}

/* ── Tooltip ──────────────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {bg3};
    color: {text1};
    border: 1px solid {neon_border};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
}}

/* ── Dialogs / message boxes ──────────────────────────────────────────────── */
QMessageBox {{
    background-color: {bg1};
    color: {text1};
}}
QMessageBox QLabel {{
    color: {text1};
    font-size: 13px;
}}
QMessageBox QPushButton {{
    min-width: 80px;
    padding: 6px 16px;
}}

QInputDialog {{
    background-color: {bg1};
    color: {text1};
}}

/* ── Frame / separator ────────────────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {brd};
    background-color: {brd};
}}

/* ── Drawing toolbar (drawing_canvas.py) ─────────────────────────────────── */
QWidget#drawingToolbar {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
}}

/* ── Top bar ────────────────────────────────────────────────────────────────── */
QWidget#topBar {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
}}
QLabel#topBarLogo {{
    color: {accent};
    background: transparent;
    letter-spacing: 1px;
}}
QLabel#breadcrumb {{
    color: {text2};
    background: transparent;
    font-size: 12px;
}}
QLineEdit#topBarSearch {{
    background-color: {bg2};
    border: 1px solid {brd_l};
    border-radius: 6px;
    padding: 0 10px;
    color: {text1};
    font-size: 12px;
}}
QLineEdit#topBarSearch:focus {{
    border-color: {accent};
}}
QPushButton#topBarAction {{
    background-color: {accent};
    color: {'#05070f' if is_dark else '#ffffff'};
    border: none;
    border-radius: 6px;
    padding: 0 14px;
    font-weight: 600;
    font-size: 12px;
}}
QPushButton#topBarAction:hover {{
    background-color: {accent_h};
}}

/* ── Bottom bar ─────────────────────────────────────────────────────────────── */
QWidget#bottomBar {{
    background-color: {bg1};
    border-top: 1px solid {brd};
}}
QLabel#statusItem {{
    color: {text3};
    font-size: 11px;
    background: transparent;
}}
QLabel#statusItemAccent {{
    color: {accent};
    font-size: 11px;
    background: transparent;
}}
QFrame#statusSep {{
    background-color: {brd_l};
    color: {brd_l};
}}

/* ── Sidebar layout ─────────────────────────────────────────────────────────── */
QWidget#sidebarHeader, QWidget#sidebarNav {{
    background-color: {bg1};
}}
QLabel#sidebarSectionLabel {{
    color: {text3};
    background: transparent;
    letter-spacing: 1px;
    font-size: 9px;
}}
QFrame#sidebarSep {{
    background-color: {brd};
    color: {brd};
}}

/* ── Notes panel layout ──────────────────────────────────────────────────────── */
QWidget#notesPanel {{
    background-color: {bg1};
    border-right: 1px solid {brd};
}}
QWidget#notesPanelHeader {{
    background-color: {bg1};
}}
QLabel#panelTitle {{
    color: {text1};
    background: transparent;
}}
QWidget#searchWrap {{
    background-color: {bg1};
}}
QLineEdit#panelSearch {{
    background-color: {bg2};
    border: 1px solid {brd_l};
    border-radius: 5px;
    padding: 0 8px;
    color: {text1};
    font-size: 12px;
}}
QLineEdit#panelSearch:focus {{
    border-color: {accent};
}}
QPushButton#iconButton {{
    background-color: transparent;
    border: 1px solid {brd_l};
    border-radius: 5px;
    color: {text2};
    font-size: 14px;
    font-weight: 600;
}}
QPushButton#iconButton:hover {{
    background-color: {hover_bg};
    border-color: {accent};
    color: {accent};
}}

/* ── Editor panel layout ──────────────────────────────────────────────────────── */
QWidget#editorPanel {{
    background-color: {bg0};
}}
QWidget#editorTopBar {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
}}
QLineEdit#editorTitleInput {{
    background: transparent;
    border: none;
    color: {text1};
    font-size: 13px;
    padding: 0;
}}
QLineEdit#editorTitleInput:focus {{
    background: transparent;
    border: none;
}}

/* ── Splitter handle glow ─────────────────────────────────────────────────────── */
QSplitter#mainSplitter::handle {{
    background-color: {brd};
    width: 2px;
}}
QSplitter#mainSplitter::handle:hover {{
    background-color: {accent};
    width: 2px;
}}

/* inner left/right vertical splitters */
QSplitter#leftSplitter::handle,
QSplitter#rightSplitter::handle {{
    background-color: {brd};
    height: 2px;
}}
QSplitter#leftSplitter::handle:hover,
QSplitter#rightSplitter::handle:hover {{
    background-color: {accent};
    height: 2px;
}}

/* ── Left panel ──────────────────────────────────────────────────────────────── */
QWidget#leftPanel {{
    background-color: {bg1};
    border-right: 1px solid {brd};
}}

/* ── Right panel ─────────────────────────────────────────────────────────────── */
QWidget#rightPanel {{
    background-color: {bg1};
    border-left: 1px solid {brd};
}}
QWidget#rightPanelHeader {{
    background-color: {bg1};
}}
QWidget#rightSectionHeader {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
}}
QWidget#backlinksPane,
QWidget#outgoingPane,
QWidget#metadataPane {{
    background-color: {bg1};
}}
QScrollArea#rightSectionScroll {{
    background-color: {bg1};
    border: none;
}}
QScrollArea#rightSectionScroll > QWidget > QWidget {{
    background-color: {bg1};
}}
QLabel#rightPlaceholder {{
    color: {text3};
    font-size: 12px;
    background: transparent;
}}

/* ── Credential panel ─────────────────────────────────────────────────────────────── */
QWidget#credentialPanel {{
    background-color: {bg1};
}}
QWidget#credLockScreen {{
    background-color: {bg1};
}}
QLabel#credLockMsg {{
    color: {text2};
    font-size: 12px;
    background: transparent;
}}
QLabel#credLockError {{
    color: {err};
    font-size: 11px;
    background: transparent;
}}
QPushButton#credUnlockBtn {{
    background-color: {accent};
    color: {'#05070f' if is_dark else '#ffffff'};
    border: none;
    border-radius: 7px;
    padding: 8px 0;
    font-weight: 600;
}}
QPushButton#credUnlockBtn:hover {{
    background-color: {accent_h};
}}
QPushButton#credLockBtn {{
    background-color: transparent;
    border: 1px solid {brd_l};
    border-radius: 6px;
    color: {text2};
    padding: 6px 0;
    margin: 6px 8px;
    font-size: 12px;
}}
QPushButton#credLockBtn:hover {{
    border-color: {accent};
    color: {accent};
}}
QListWidget#credList {{
    background-color: {bg1};
    border: none;
    outline: none;
    padding: 4px;
}}
QListWidget#credList::item {{
    background-color: {bg2};
    border: 1px solid {brd};
    border-radius: 7px;
    padding: 8px 12px;
    margin: 2px 4px;
    color: {text1};
    font-size: 12px;
}}
QListWidget#credList::item:hover {{
    border-color: {neon_border};
    background-color: {hover_bg};
}}
QListWidget#credList::item:selected {{
    background-color: {sel_bg};
    border-color: {accent};
    color: {accent};
}}

/* Credential dialog */
QLabel#credDialogHeader {{
    color: {accent};
    background: transparent;
}}
QFrame#credSep {{
    background-color: {brd};
    color: {brd};
}}
QLineEdit#credField {{
    background-color: {inp_bg};
    border: 1px solid {inp_brd};
    border-radius: 6px;
    padding: 5px 10px;
    color: {text1};
    font-size: 13px;
}}
QLineEdit#credField:focus {{
    border-color: {accent};
}}
QComboBox#credField {{
    background-color: {inp_bg};
    border: 1px solid {inp_brd};
    border-radius: 6px;
    padding: 5px 10px;
    color: {text1};
    font-size: 13px;
}}
QComboBox#credField:focus {{
    border-color: {accent};
}}
QPushButton#credIconBtn {{
    background-color: transparent;
    border: 1px solid {brd_l};
    border-radius: 5px;
    color: {text2};
    font-size: 13px;
}}
QPushButton#credIconBtn:hover {{
    background-color: {hover_bg};
    border-color: {accent};
    color: {accent};
}}
QPushButton#credGenBtn {{
    background-color: {'rgba(0,212,255,0.12)' if is_dark else 'rgba(37,99,235,0.10)'};
    border: 1px solid {neon_border};
    border-radius: 5px;
    color: {accent};
    font-size: 12px;
    font-weight: 600;
    padding: 0 10px;
}}
QPushButton#credGenBtn:hover {{
    background-color: {sel_bg};
}}
QProgressBar#strengthBar {{
    background-color: {brd};
    border: none;
    border-radius: 3px;
    height: 6px;
}}
QLabel#strengthLabel {{
    color: {text3};
    font-size: 11px;
    background: transparent;
    min-width: 70px;
}}
QWidget#totpWidget {{
    background-color: {'rgba(0,212,255,0.06)' if is_dark else 'rgba(37,99,235,0.05)'};
    border: 1px solid {neon_border};
    border-radius: 8px;
    padding: 4px 8px;
}}
QLabel#totpCode {{
    color: {accent};
    background: transparent;
    letter-spacing: 4px;
}}
QLabel#totpTimer {{
    color: {text3};
    font-size: 11px;
    background: transparent;
}}
"""

    def get_color(self, key: str) -> str:
        """Return a single colour token from the active palette."""
        return self.colors.get(key, '#ffffff')

