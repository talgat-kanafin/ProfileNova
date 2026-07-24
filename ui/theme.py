"""
ui/theme.py
===========
Дизайн-система ProfileNova.

Dark engineering UI. Minimal. High contrast. Accent orange.
Шрифт: Inter → IBM Plex Sans → DIN → System fallback
"""

from PySide6.QtGui import QFont, QFontDatabase, QPalette, QColor
from PySide6.QtWidgets import QApplication


# ════════════════════════════════════════════════════════════
# ЦВЕТА
# ════════════════════════════════════════════════════════════

class Colors:
    # Фоны
    BG_BASE       = "#0F0F0F"   # основной фон
    BG_SURFACE    = "#1A1A1A"   # карточки, панели
    BG_ELEVATED   = "#242424"   # приподнятые элементы
    BG_OVERLAY    = "#2E2E2E"   # попапы, дропдауны

    # Границы
    BORDER        = "#333333"
    BORDER_FOCUS  = "#FF6B00"   # акцент при фокусе

    # Акцент (оранжевый)
    ACCENT        = "#FF6B00"
    ACCENT_HOVER  = "#FF8533"
    ACCENT_PRESS  = "#CC5500"
    ACCENT_DIM    = "#FF6B0033"  # прозрачный акцент

    # Текст
    TEXT_PRIMARY   = "#F0F0F0"
    TEXT_SECONDARY = "#A0A0A0"
    TEXT_DISABLED  = "#505050"
    TEXT_ON_ACCENT = "#FFFFFF"

    # Статусы
    SUCCESS   = "#22C55E"
    WARNING   = "#F59E0B"
    ERROR     = "#EF4444"
    INFO      = "#3B82F6"

    # Статус синхронизации
    SYNC_OK      = "#22C55E"
    SYNC_OFFLINE = "#F59E0B"
    SYNC_SYNCING = "#3B82F6"
    SYNC_ERROR   = "#EF4444"

    # Таблицы
    TABLE_HEADER   = "#1E1E1E"
    TABLE_ROW_ALT  = "#161616"
    TABLE_SELECTED = "#FF6B0022"
    TABLE_GRID     = "#2A2A2A"


# ════════════════════════════════════════════════════════════
# ТИПОГРАФИКА
# ════════════════════════════════════════════════════════════

class Typography:
    # Приоритет шрифтов
    FONT_FAMILY = "Inter, IBM Plex Sans, DIN, Segoe UI, Arial, sans-serif"
    FONT_MONO   = "IBM Plex Mono, Consolas, Courier New, monospace"

    # Размеры
    SIZE_XS  = 10
    SIZE_SM  = 11
    SIZE_MD  = 13
    SIZE_LG  = 15
    SIZE_XL  = 18
    SIZE_2XL = 24
    SIZE_3XL = 32

    @staticmethod
    def get_font(size: int = 13, bold: bool = False, mono: bool = False) -> QFont:
        candidates = (
            ["IBM Plex Mono", "Consolas"] if mono
            else ["Inter", "IBM Plex Sans", "Segoe UI", "Arial"]
        )
        available = QFontDatabase.families()
        family    = next((f for f in candidates if f in available), "Arial")
        font = QFont(family, size)
        if bold:
            font.setWeight(QFont.Weight.Bold)
        return font


# ════════════════════════════════════════════════════════════
# РАЗМЕРЫ И ОТСТУПЫ
# ════════════════════════════════════════════════════════════

class Spacing:
    XS  = 4
    SM  = 8
    MD  = 12
    LG  = 16
    XL  = 24
    XXL = 32

class Radius:
    SM = 3
    MD = 5
    LG = 8

class Sizes:
    NAV_WIDTH       = 220
    TOOLBAR_HEIGHT  = 48
    STATUSBAR_HEIGHT= 28
    INPUT_HEIGHT    = 36
    BTN_HEIGHT      = 36
    BTN_HEIGHT_LG   = 44
    ICON_SM         = 16
    ICON_MD         = 20
    ICON_LG         = 24


# ════════════════════════════════════════════════════════════
# ГЛОБАЛЬНЫЙ STYLESHEET
# ════════════════════════════════════════════════════════════

STYLESHEET = f"""
/* ── Базовый фон ── */
QMainWindow, QDialog, QWidget {{
    background-color: {Colors.BG_BASE};
    color: {Colors.TEXT_PRIMARY};
    font-family: Inter, "IBM Plex Sans", "Segoe UI", Arial;
    font-size: 13px;
}}

/* ── Кнопки ── */
QPushButton {{
    background-color: {Colors.BG_ELEVATED};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    border-radius: {Radius.SM}px;
    padding: 0 16px;
    height: {Sizes.BTN_HEIGHT}px;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {Colors.BG_OVERLAY};
    border-color: {Colors.TEXT_SECONDARY};
}}
QPushButton:pressed {{
    background-color: {Colors.BG_SURFACE};
}}
QPushButton:disabled {{
    color: {Colors.TEXT_DISABLED};
    border-color: {Colors.BORDER};
}}

/* Акцентная кнопка */
QPushButton[accent="true"] {{
    background-color: {Colors.ACCENT};
    color: {Colors.TEXT_ON_ACCENT};
    border: none;
    font-weight: 600;
}}
QPushButton[accent="true"]:hover {{
    background-color: {Colors.ACCENT_HOVER};
}}
QPushButton[accent="true"]:pressed {{
    background-color: {Colors.ACCENT_PRESS};
}}

/* Кнопка-призрак */
QPushButton[ghost="true"] {{
    background-color: transparent;
    border-color: {Colors.BORDER};
    color: {Colors.TEXT_SECONDARY};
}}
QPushButton[ghost="true"]:hover {{
    color: {Colors.TEXT_PRIMARY};
    border-color: {Colors.TEXT_SECONDARY};
    background-color: {Colors.BG_ELEVATED};
}}

/* ── Поля ввода ── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {Colors.BG_SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    border-radius: {Radius.SM}px;
    padding: 0 10px;
    height: {Sizes.INPUT_HEIGHT}px;
    font-size: 13px;
    selection-background-color: {Colors.ACCENT_DIM};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {Colors.ACCENT};
    background-color: {Colors.BG_ELEVATED};
}}
QLineEdit:disabled {{
    color: {Colors.TEXT_DISABLED};
    background-color: {Colors.BG_BASE};
}}
QLineEdit[error="true"] {{
    border-color: {Colors.ERROR};
}}

/* Placeholder */
QLineEdit[placeholder="true"] {{
    color: {Colors.TEXT_DISABLED};
}}

/* ── Комбобокс ── */
QComboBox {{
    background-color: {Colors.BG_SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    border-radius: {Radius.SM}px;
    padding: 0 10px;
    height: {Sizes.INPUT_HEIGHT}px;
}}
QComboBox:focus {{
    border-color: {Colors.ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {Colors.TEXT_SECONDARY};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {Colors.BG_OVERLAY};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    selection-background-color: {Colors.ACCENT_DIM};
    selection-color: {Colors.TEXT_PRIMARY};
    outline: none;
}}

/* ── Таблицы ── */
QTableView, QTableWidget {{
    background-color: {Colors.BG_BASE};
    color: {Colors.TEXT_PRIMARY};
    gridline-color: {Colors.TABLE_GRID};
    border: 1px solid {Colors.BORDER};
    alternate-background-color: {Colors.TABLE_ROW_ALT};
    selection-background-color: {Colors.TABLE_SELECTED};
    selection-color: {Colors.TEXT_PRIMARY};
    font-size: 12px;
}}
QHeaderView::section {{
    background-color: {Colors.TABLE_HEADER};
    color: {Colors.TEXT_SECONDARY};
    border: none;
    border-right: 1px solid {Colors.BORDER};
    border-bottom: 1px solid {Colors.BORDER};
    padding: 6px 8px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QHeaderView::section:hover {{
    background-color: {Colors.BG_ELEVATED};
    color: {Colors.TEXT_PRIMARY};
}}

/* ── Дерево ── */
QTreeWidget, QTreeView {{
    background-color: {Colors.BG_BASE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    alternate-background-color: {Colors.TABLE_ROW_ALT};
}}
QTreeWidget::item, QTreeView::item {{
    padding: 4px 8px;
    border: none;
}}
QTreeWidget::item:selected, QTreeView::item:selected {{
    background-color: {Colors.ACCENT_DIM};
    color: {Colors.TEXT_PRIMARY};
    border-left: 2px solid {Colors.ACCENT};
}}
QTreeWidget::item:hover, QTreeView::item:hover {{
    background-color: {Colors.BG_ELEVATED};
}}

/* ── Список ── */
QListWidget {{
    background-color: {Colors.BG_BASE};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
}}
QListWidget::item {{
    padding: 10px 12px;
    border-bottom: 1px solid {Colors.BORDER};
}}
QListWidget::item:selected {{
    background-color: {Colors.ACCENT_DIM};
    color: {Colors.TEXT_PRIMARY};
    border-left: 3px solid {Colors.ACCENT};
}}
QListWidget::item:hover {{
    background-color: {Colors.BG_ELEVATED};
}}

/* ── Вкладки ── */
QTabWidget::pane {{
    border: 1px solid {Colors.BORDER};
    background-color: {Colors.BG_BASE};
}}
QTabBar::tab {{
    background-color: transparent;
    color: {Colors.TEXT_SECONDARY};
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 12px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    color: {Colors.TEXT_PRIMARY};
    border-bottom: 2px solid {Colors.ACCENT};
}}
QTabBar::tab:hover {{
    color: {Colors.TEXT_PRIMARY};
    background-color: {Colors.BG_ELEVATED};
}}

/* ── Скроллбар ── */
QScrollBar:vertical {{
    background: {Colors.BG_BASE};
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {Colors.BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Colors.TEXT_DISABLED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {Colors.BG_BASE};
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background: {Colors.BORDER};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {Colors.TEXT_DISABLED};
}}

/* ── Панели ── */
QFrame[role="card"] {{
    background-color: {Colors.BG_SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: {Radius.MD}px;
}}
QFrame[role="divider"] {{
    background-color: {Colors.BORDER};
    max-height: 1px;
}}

/* ── Лейблы ── */
QLabel[role="title"] {{
    font-size: 18px;
    font-weight: 600;
    color: {Colors.TEXT_PRIMARY};
}}
QLabel[role="subtitle"] {{
    font-size: 12px;
    color: {Colors.TEXT_SECONDARY};
}}
QLabel[role="caption"] {{
    font-size: 11px;
    color: {Colors.TEXT_DISABLED};
}}
QLabel[role="error"] {{
    font-size: 11px;
    color: {Colors.ERROR};
}}
QLabel[role="success"] {{
    font-size: 11px;
    color: {Colors.SUCCESS};
}}

/* ── Разделитель (splitter) ── */
QSplitter::handle {{
    background-color: {Colors.BORDER};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* ── Статусбар ── */
QStatusBar {{
    background-color: {Colors.BG_SURFACE};
    color: {Colors.TEXT_SECONDARY};
    border-top: 1px solid {Colors.BORDER};
    font-size: 11px;
}}
QStatusBar::item {{
    border: none;
}}

/* ── Меню ── */
QMenuBar {{
    background-color: {Colors.BG_SURFACE};
    color: {Colors.TEXT_PRIMARY};
    border-bottom: 1px solid {Colors.BORDER};
}}
QMenuBar::item:selected {{
    background-color: {Colors.BG_ELEVATED};
}}
QMenu {{
    background-color: {Colors.BG_OVERLAY};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    padding: 4px 0;
}}
QMenu::item {{
    padding: 8px 20px 8px 12px;
}}
QMenu::item:selected {{
    background-color: {Colors.BG_ELEVATED};
    color: {Colors.TEXT_PRIMARY};
}}
QMenu::separator {{
    height: 1px;
    background: {Colors.BORDER};
    margin: 4px 0;
}}

/* ── Тултип ── */
QToolTip {{
    background-color: {Colors.BG_OVERLAY};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER};
    padding: 6px 10px;
    font-size: 12px;
}}

/* ── Прогрессбар ── */
QProgressBar {{
    background-color: {Colors.BG_SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: {Radius.SM}px;
    height: 6px;
    text-align: center;
    font-size: 0px;
}}
QProgressBar::chunk {{
    background-color: {Colors.ACCENT};
    border-radius: {Radius.SM}px;
}}

/* ── Чекбокс ── */
QCheckBox {{
    color: {Colors.TEXT_PRIMARY};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {Colors.BORDER};
    border-radius: 3px;
    background-color: {Colors.BG_SURFACE};
}}
QCheckBox::indicator:checked {{
    background-color: {Colors.ACCENT};
    border-color: {Colors.ACCENT};
}}
QCheckBox::indicator:hover {{
    border-color: {Colors.ACCENT};
}}

/* ── Навигационная боковая панель ── */
QWidget[role="nav"] {{
    background-color: {Colors.BG_SURFACE};
    border-right: 1px solid {Colors.BORDER};
}}
QPushButton[role="nav-item"] {{
    background-color: transparent;
    color: {Colors.TEXT_SECONDARY};
    border: none;
    border-radius: 0;
    text-align: left;
    padding: 0 16px;
    height: 44px;
    font-size: 13px;
}}
QPushButton[role="nav-item"]:hover {{
    background-color: {Colors.BG_ELEVATED};
    color: {Colors.TEXT_PRIMARY};
}}
QPushButton[role="nav-item"][active="true"] {{
    background-color: {Colors.ACCENT_DIM};
    color: {Colors.ACCENT};
    border-left: 3px solid {Colors.ACCENT};
}}

/* ── Поле пароля (кнопка показать/скрыть) ── */
QToolButton {{
    background-color: transparent;
    border: none;
    color: {Colors.TEXT_SECONDARY};
    padding: 0 6px;
}}
QToolButton:hover {{
    color: {Colors.TEXT_PRIMARY};
}}
"""


def apply_theme(app: QApplication):
    """Применить тему к приложению. Вызывать один раз при старте."""
    app.setStyle("Fusion")

    palette = QPalette()
    c = Colors

    palette.setColor(QPalette.ColorRole.Window,          QColor(c.BG_BASE))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(c.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base,            QColor(c.BG_SURFACE))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(c.TABLE_ROW_ALT))
    palette.setColor(QPalette.ColorRole.Text,            QColor(c.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button,          QColor(c.BG_ELEVATED))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(c.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(c.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(c.TEXT_ON_ACCENT))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor(c.BG_OVERLAY))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor(c.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Link,            QColor(c.ACCENT))
    palette.setColor(QPalette.ColorRole.BrightText,      QColor(c.ACCENT))

    # Disabled
    palette.setColor(QPalette.ColorGroup.Disabled,
                     QPalette.ColorRole.WindowText, QColor(c.TEXT_DISABLED))
    palette.setColor(QPalette.ColorGroup.Disabled,
                     QPalette.ColorRole.Text,       QColor(c.TEXT_DISABLED))
    palette.setColor(QPalette.ColorGroup.Disabled,
                     QPalette.ColorRole.ButtonText, QColor(c.TEXT_DISABLED))

    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
