"""Theme manager — dark/light mode."""
import logging
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"


class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)

    DARK_THEME = {
        'bg_main':           '#080f0a',
        'bg_panel':          '#080f0a',
        'bg_card':           '#0d1610',
        'bg_elevated':       '#111d13',
        'text_primary':      '#f0f7ee',
        'text_secondary':    '#8faa88',
        'text_dim':          '#4a6044',
        'accent':            '#f45e29',
        'accent_hover':      '#fd742e',
        'accent_active':     '#d94e1f',
        'accent_purple':     '#1ed794',
        'accent_green':      '#1ed794',
        'success':           '#1ed794',
        'error':             '#f85149',
        'warning':           '#f4a429',
        'disabled':          '#162010',
        'disabled_text':     '#4a6044',
        'border':            '#1e2e1a',
        'border_light':      '#2a3d24',
        'border_accent':     'rgba(244,94,41,0.30)',
        'input_bg':          '#162010',
        'input_border':      '#2a3d24',
    }

    LIGHT_THEME = {
        'bg_main':           '#fafdf8',
        'bg_panel':          '#f0f7ee',
        'bg_card':           '#ffffff',
        'bg_elevated':       '#e8f5e4',
        'text_primary':      '#1a2e16',
        'text_secondary':    '#4a6a44',
        'text_dim':          '#7a9a74',
        'accent':            '#f45e29',
        'accent_hover':      '#fd742e',
        'accent_active':     '#d94e1f',
        'accent_purple':     '#17b87e',
        'accent_green':      '#17b87e',
        'success':           '#17b87e',
        'error':             '#d1242f',
        'warning':           '#c47a10',
        'disabled':          '#e0eedc',
        'disabled_text':     '#7a9a74',
        'border':            '#c8dfc4',
        'border_light':      '#d8ecd4',
        'border_accent':     'rgba(244,94,41,0.25)',
        'input_bg':          '#ffffff',
        'input_border':      '#c8dfc4',
    }

    def __init__(self):
        super().__init__()
        self.current_theme = ThemeMode.DARK
        self.colors = self.DARK_THEME.copy()

    def set_theme(self, mode: ThemeMode):
        self.current_theme = mode
        self.colors = (self.DARK_THEME if mode == ThemeMode.DARK else self.LIGHT_THEME).copy()
        self.theme_changed.emit(mode.value)

    def toggle_theme(self):
        self.set_theme(ThemeMode.LIGHT if self.current_theme == ThemeMode.DARK else ThemeMode.DARK)

    def get_color(self, key: str) -> str:
        return self.colors.get(key, '#ffffff')

    def get_stylesheet(self) -> str:
        c = self.colors
        is_dark = self.current_theme == ThemeMode.DARK

        bg0      = c['bg_main']
        bg1      = c['bg_panel']
        bg2      = c['bg_card']
        bg3      = c['bg_elevated']
        text1    = c['text_primary']
        text2    = c['text_secondary']
        text3    = c['text_dim']
        accent   = c['accent']
        acc_h    = c['accent_hover']
        acc_a    = c['accent_active']
        err      = c['error']
        ok       = c['success']
        dis      = c['disabled']
        dis_t    = c['disabled_text']
        brd      = c['border']
        brd_l    = c['border_light']
        brd_acc  = c['border_accent']
        inp_bg   = c['input_bg']
        inp_brd  = c['input_border']

        btn_fg   = '#0f1a14' if is_dark else '#ffffff'
        hover_bg = 'rgba(244,94,41,0.10)' if is_dark else 'rgba(244,94,41,0.08)'
        sel_bg   = 'rgba(244,94,41,0.18)' if is_dark else 'rgba(244,94,41,0.12)'
        note_hover = 'rgba(30,215,148,0.06)' if is_dark else 'rgba(30,215,148,0.05)'
        note_sel   = 'rgba(244,94,41,0.14)' if is_dark else 'rgba(244,94,41,0.10)'
        cred_gen_bg = 'rgba(30,215,148,0.12)' if is_dark else 'rgba(30,215,148,0.10)'
        totp_bg     = 'rgba(30,215,148,0.08)' if is_dark else 'rgba(30,215,148,0.06)'

        return f"""
/* ── Base ── */
QMainWindow, QDialog {{
    background-color: {bg0};
    color: {text1};
}}
QWidget {{
    background-color: {bg0};
    color: {text1};
    font-family: 'Segoe UI', 'Inter', system-ui, sans-serif;
    font-size: 13px;
}}

/* ── Menu bar ── */
QMenuBar {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
    padding: 2px 6px;
    spacing: 2px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 5px 12px;
    border-radius: 6px;
    color: {text2};
}}
QMenuBar::item:selected {{
    background-color: {hover_bg};
    color: {text1};
}}
QMenu {{
    background-color: {bg2};
    border: 1px solid {brd};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{
    padding: 7px 24px 7px 14px;
    border-radius: 5px;
    color: {text1};
    margin: 1px 3px;
}}
QMenu::item:selected {{
    background-color: {hover_bg};
    color: {accent};
}}
QMenu::separator {{
    height: 1px;
    background: {brd};
    margin: 3px 10px;
}}

/* ── Toolbar ── */
QToolBar {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
    spacing: 2px;
    padding: 3px 8px;
}}
QToolBar::separator {{
    background: {brd};
    width: 1px;
    margin: 4px 4px;
}}
QToolBar QToolButton {{
    background: transparent;
    border: none;
    border-radius: 5px;
    padding: 4px 7px;
    min-width: 22px;
}}
QToolBar QToolButton:hover {{
    background-color: {hover_bg};
}}
QToolBar QToolButton:checked {{
    background-color: {sel_bg};
    color: {accent};
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {accent};
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {acc_h};
}}
QPushButton:pressed {{
    background-color: {acc_a};
}}
QPushButton:disabled {{
    background-color: {dis};
    color: {dis_t};
}}
/* Only named/text buttons get the dark fg color */
QPushButton#topBarAction,
QPushButton#credUnlockBtn,
QPushButton#credAddBtn,
QPushButton#pmNavBtn,
QPushButton#pmLockBtn,
QPushButton#unlock_btn,
QPushButton#secondaryButton,
QPushButton#dangerButton,
QPushButton#sidebarButton,
QPushButton#addButton,
QPushButton#sectionHeader,
QPushButton#credGenBtn,
QPushButton#credLockBtn,
QPushButton#aiAskBtn {{
    color: {btn_fg};
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
QPushButton#sidebarButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    text-align: left;
    color: {text2};
    font-size: 13px;
}}
QPushButton#sidebarButton:hover {{
    background-color: {hover_bg};
    color: {text1};
}}
QPushButton#sidebarButton[active="true"] {{
    background-color: {sel_bg};
    color: {accent};
    border-left: 2px solid {accent};
    padding-left: 10px;
}}
QPushButton#sectionHeader {{
    background: transparent;
    border: none;
    padding: 4px 4px;
    text-align: left;
    color: {text3};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QPushButton#addButton {{
    background: transparent;
    border: 1px dashed {brd_l};
    color: {text3};
    padding: 6px;
    font-size: 12px;
    border-radius: 5px;
}}
QPushButton#addButton:hover {{
    border-color: {accent};
    color: {accent};
    background-color: {hover_bg};
}}
QPushButton#iconButton {{
    background-color: transparent;
    border: 1px solid {brd};
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
QPushButton#topBarAction {{
    background-color: {accent};
    color: {btn_fg};
    border: none;
    border-radius: 6px;
    padding: 0 14px;
    font-weight: 600;
    font-size: 12px;
}}
QPushButton#topBarAction:hover {{
    background-color: {acc_h};
}}

/* ── Inputs ── */
QLineEdit {{
    background-color: {inp_bg};
    color: {text1};
    border: 1px solid {inp_brd};
    border-radius: 6px;
    padding: 6px 11px;
    font-size: 13px;
    selection-background-color: {accent};
    selection-color: {btn_fg};
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
QLineEdit#topBarSearch {{
    background-color: {bg2};
    border: 1px solid {brd};
    border-radius: 6px;
    padding: 0 10px;
    color: {text1};
    font-size: 12px;
}}
QLineEdit#topBarSearch:focus {{
    border-color: {accent};
}}
QLineEdit#panelSearch {{
    background-color: {bg2};
    border: 1px solid {brd};
    border-radius: 5px;
    padding: 0 8px;
    color: {text1};
    font-size: 12px;
}}
QLineEdit#panelSearch:focus {{
    border-color: {accent};
}}
QLineEdit#editorTitleInput {{
    background: transparent;
    border: none;
    color: {text1};
    font-size: 15px;
    font-weight: 600;
    padding: 0;
}}
QLineEdit#editorTitleInput:focus {{
    background: transparent;
    border: none;
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

/* ── Text edit ── */
QTextEdit {{
    background-color: {bg0};
    color: {text1};
    border: none;
    padding: 20px 28px;
    font-size: 15px;
    selection-background-color: {accent};
    selection-color: {btn_fg};
}}
QTextEdit:focus {{
    border: none;
    outline: none;
}}
QPlainTextEdit {{
    background-color: {inp_bg};
    color: {text1};
    border: 1px solid {inp_brd};
    border-radius: 6px;
    padding: 12px 16px;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    selection-background-color: {accent};
    selection-color: {btn_fg};
}}
QPlainTextEdit:focus {{
    border-color: {accent};
}}

/* ── Note list ── */
QListWidget {{
    background-color: {bg1};
    border: none;
    outline: none;
    padding: 4px 0;
}}
QListWidget::item {{
    background-color: transparent;
    border: none;
    padding: 0;
    margin: 0;
}}
QListWidget::item:hover {{
    background-color: transparent;
}}
QListWidget::item:selected {{
    background-color: transparent;
}}

/* Note card widget inside list item */
QWidget#noteCard {{
    background-color: transparent;
    border-bottom: 1px solid {brd};
}}
QWidget#noteCard:hover {{
    background-color: {note_hover};
}}
QListWidget::item:selected QWidget#noteCard {{
    background-color: {note_sel};
    border-left: 2px solid {accent};
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
    border-radius: 6px;
    padding: 8px 12px;
    margin: 2px 4px;
    color: {text1};
    font-size: 12px;
}}
QListWidget#credList::item:hover {{
    border-color: {brd_acc};
    background-color: {hover_bg};
}}
QListWidget#credList::item:selected {{
    background-color: {sel_bg};
    border-color: {accent};
    color: {accent};
}}

/* ── Tree widget ── */
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

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {brd};
    border-radius: 6px;
    background-color: {bg2};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {bg1};
    border: 1px solid {brd};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 6px 16px;
    margin-right: 2px;
    color: {text2};
    font-size: 13px;
}}
QTabBar::tab:selected {{
    background-color: {bg2};
    color: {accent};
    border-top: 2px solid {accent};
}}
QTabBar::tab:hover:!selected {{
    background-color: {hover_bg};
    color: {text1};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {brd_l};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {accent};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {brd_l};
    border-radius: 3px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {accent};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* ── Splitters ── */
QSplitter::handle {{
    background-color: {brd};
}}
QSplitter::handle:hover {{
    background-color: {accent};
}}
QSplitter#mainSplitter::handle {{
    width: 1px;
}}
QSplitter#leftSplitter::handle, QSplitter#rightSplitter::handle {{
    height: 1px;
}}

/* ── Status bar ── */
QStatusBar {{
    background-color: {bg1};
    border-top: 1px solid {brd};
    color: {text3};
    font-size: 11px;
}}
QStatusBar QLabel {{
    color: {text3};
    font-size: 11px;
    padding: 2px 4px;
    background: transparent;
}}

/* ── Labels ── */
QLabel {{
    background: transparent;
    color: {text1};
}}
QLabel#secondaryLabel {{
    color: {text3};
    font-size: 11px;
}}
QLabel#sidebarSectionLabel {{
    color: {text3};
    background: transparent;
    letter-spacing: 0.8px;
    font-size: 10px;
    font-weight: 700;
}}
QLabel#panelTitle {{
    color: {text1};
    background: transparent;
    font-weight: 600;
}}
QLabel#breadcrumb {{
    color: {text2};
    background: transparent;
    font-size: 12px;
}}
QLabel#topBarLogo {{
    color: {accent};
    background: transparent;
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
QLabel#watermark {{
    color: {accent};
    font-size: 9px;
    background: transparent;
    letter-spacing: 2px;
    opacity: 0.6;
}}
QLabel#noteCardTitle {{
    color: {text1};
    background: transparent;
    font-size: 13px;
    font-weight: 600;
}}
QLabel#noteCardMeta {{
    color: {text3};
    background: transparent;
    font-size: 11px;
}}
QLabel#noteCardPreview {{
    color: {text2};
    background: transparent;
    font-size: 12px;
}}
QLabel#rightPlaceholder {{
    color: {text3};
    font-size: 12px;
    background: transparent;
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
QLabel#credDialogHeader {{
    color: {accent};
    background: transparent;
}}
QLabel#strengthLabel {{
    color: {text3};
    font-size: 11px;
    background: transparent;
    min-width: 70px;
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

/* ── Checkboxes ── */
QCheckBox {{
    spacing: 8px;
    color: {text1};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
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

/* ── Combo box ── */
QComboBox {{
    background-color: {inp_bg};
    border: 1px solid {inp_brd};
    border-radius: 6px;
    padding: 5px 10px;
    color: {text1};
    font-size: 13px;
    min-width: 80px;
}}
QComboBox:hover {{ border-color: {brd_l}; }}
QComboBox:focus {{ border-color: {accent}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background-color: {bg2};
    border: 1px solid {brd};
    border-radius: 6px;
    color: {text1};
    selection-background-color: {sel_bg};
    selection-color: {accent};
    outline: none;
}}
QComboBox#credField {{
    background-color: {inp_bg};
    border: 1px solid {inp_brd};
    border-radius: 6px;
    padding: 5px 10px;
    color: {text1};
    font-size: 13px;
}}
QComboBox#credField:focus {{ border-color: {accent}; }}

/* ── Spin / font combo ── */
QSpinBox, QDoubleSpinBox {{
    background-color: {inp_bg};
    border: 1px solid {inp_brd};
    border-radius: 5px;
    padding: 4px 8px;
    color: {text1};
    font-size: 13px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {accent}; }}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: transparent; border: none; width: 14px;
}}
QFontComboBox {{
    background-color: {inp_bg};
    border: 1px solid {inp_brd};
    border-radius: 5px;
    padding: 4px 8px;
    color: {text1};
    font-size: 13px;
}}
QFontComboBox:focus {{ border-color: {accent}; }}

/* ── Progress bar ── */
QProgressBar {{
    background-color: {brd};
    border: none;
    border-radius: 3px;
    height: 5px;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {accent};
    border-radius: 3px;
}}
QProgressBar#strengthBar {{
    background-color: {brd};
    border: none;
    border-radius: 3px;
    height: 5px;
}}

/* ── Tooltip ── */
QToolTip {{
    background-color: {bg3};
    color: {text1};
    border: 1px solid {brd};
    border-radius: 5px;
    padding: 4px 9px;
    font-size: 12px;
}}

/* ── Dialogs ── */
QMessageBox {{
    background-color: {bg1};
    color: {text1};
}}
QMessageBox QLabel {{ color: {text1}; font-size: 13px; }}
QMessageBox QPushButton {{ min-width: 76px; padding: 5px 14px; }}
QInputDialog {{ background-color: {bg1}; color: {text1}; }}

/* ── Frames / separators ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {brd};
    background-color: {brd};
}}
QFrame#sidebarSep, QFrame#credSep {{
    background-color: {brd};
    color: {brd};
}}
QFrame#statusSep {{
    background-color: {brd_l};
    color: {brd_l};
}}

/* ── Top bar ── */
QWidget#topBar {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
}}

/* ── Bottom bar ── */
QWidget#bottomBar {{
    background-color: {bg1};
    border-top: 1px solid {brd};
}}

/* ── Left panel / sidebar ── */
QWidget#leftPanel, QWidget#sidebar, QWidget#modernSidebar {{
    background-color: {bg1};
    border-right: 1px solid {brd};
}}
QWidget#sidebarHeader, QWidget#sidebarNav {{
    background-color: {bg1};
}}

/* ── Notes panel ── */
QWidget#notesPanel {{
    background-color: {bg1};
    border-right: 1px solid {brd};
}}
QWidget#notesPanelHeader {{
    background-color: {bg1};
}}
QWidget#searchWrap {{
    background-color: {bg1};
}}
QWidget#noteCard {{
    background-color: transparent;
    border: none;
    border-bottom: 1px solid {brd};
    border-radius: 0px;
}}
QWidget#noteCard:hover {{
    background-color: {note_hover};
}}

/* ── Editor panel ── */
QWidget#editorPanel {{
    background-color: {bg0};
}}
QWidget#editorTopBar {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
}}

/* ── Right panel ── */
QWidget#rightPanel {{
    background-color: {bg1};
    border-left: 1px solid {brd};
}}
QWidget#rightPanelHeader, QWidget#rightSectionHeader {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
}}
QWidget#backlinksPane, QWidget#outgoingPane, QWidget#metadataPane {{
    background-color: {bg1};
}}
QScrollArea#rightSectionScroll {{
    background-color: {bg1};
    border: none;
}}
QScrollArea#rightSectionScroll > QWidget > QWidget {{
    background-color: {bg1};
}}

/* ── Drawing toolbar ── */
QWidget#drawingToolbar {{
    background-color: {bg1};
    border-bottom: 1px solid {brd};
}}

/* ── Vault popup ── */
QFrame#vaultPopup {{
    background-color: {bg1};
    border: 1px solid {brd_l};
    border-radius: 10px;
}}

/* ── AI panel ── */
QWidget#aiPanel {{
    background-color: {bg1};
}}
QWidget#aiInputRow, QWidget#aiKeyRow {{
    background-color: {bg1};
}}
QTextEdit#aiChatArea {{
    background-color: {bg0};
    border: none;
    padding: 10px 12px;
    font-size: 12px;
}}
QLineEdit#aiPromptInput {{
    background-color: {inp_bg};
    border: 1px solid {inp_brd};
    border-radius: 6px;
    padding: 0 10px;
    color: {text1};
    font-size: 13px;
}}
QLineEdit#aiPromptInput:focus {{
    border-color: {accent};
}}
QPushButton#aiAskBtn {{
    background-color: {accent};
    color: {btn_fg};
    border: none;
    border-radius: 6px;
    font-weight: 700;
    font-size: 13px;
}}
QPushButton#aiAskBtn:hover {{
    background-color: {acc_h};
}}
QPushButton#aiAskBtn:pressed {{
    background-color: {acc_a};
}}
QPushButton#aiAskBtn:disabled {{
    background-color: {dis};
    color: {dis_t};
}}
QLabel#aiCtxLabel {{
    color: {text2};
    font-size: 11px;
    background: transparent;
}}

/* ── Credential panel ── */
QWidget#credentialPanel, QWidget#credLockScreen {{
    background-color: {bg1};
}}
QPushButton#credUnlockBtn {{
    background-color: {accent};
    color: {btn_fg};
    border: none;
    border-radius: 6px;
    padding: 8px 0;
    font-weight: 600;
}}
QPushButton#credUnlockBtn:hover {{ background-color: {acc_h}; }}
QPushButton#credAddBtn {{
    background-color: {accent};
    color: {btn_fg};
    border: none;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 600;
    padding: 0 8px;
}}
QPushButton#credAddBtn:hover {{ background-color: {acc_h}; }}
QPushButton#credAddBtn:pressed {{ background-color: {acc_a}; }}
QPushButton#credLockBtn {{
    background-color: transparent;
    border: 1px solid {brd_l};
    border-radius: 5px;
    color: {text2};
    padding: 6px 0;
    margin: 6px 8px;
    font-size: 12px;
}}
QPushButton#credLockBtn:hover {{ border-color: {accent}; color: {accent}; }}
QPushButton#credIconBtn {{
    background-color: transparent;
    border: none;
    font-size: 16px;
}}
QPushButton#credGenBtn {{
    background-color: {cred_gen_bg};
    border: 1px solid {brd_acc};
    border-radius: 5px;
    color: {accent};
    font-size: 12px;
    font-weight: 600;
    padding: 0 10px;
}}
QPushButton#credGenBtn:hover {{ background-color: {sel_bg}; }}
QWidget#totpWidget {{
    background-color: {totp_bg};
    border: 1px solid {brd_acc};
    border-radius: 6px;
    padding: 4px 8px;
}}
"""
