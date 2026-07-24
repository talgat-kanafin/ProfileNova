"""
ui/screens/login_screen.py
==========================
Экран входа в систему.

Функции:
- Логин / пароль с показом пароля
- Чекбокс "Запомнить меня"
- Автовход если сессия сохранена
- Переключатель языка (ru / kk)
- Сигнал login_success(user) → главное окно открывается
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QFrame,
    QSizePolicy, QToolButton, QComboBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon, QFont

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import Colors, Typography, Spacing, Sizes
from ui.i18n  import tr, set_language, on_language_change, available_languages, get_language


RESOURCES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "resources"
)


class LoginScreen(QWidget):
    """
    Экран входа.
    Сигнал login_success(user_dict) — испускается при успешном входе.
    """
    login_success = Signal(dict)

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self._auth = auth_manager
        self._build_ui()
        on_language_change(self._retranslate)

        # Попытка автовхода
        if self._auth.restore_session():
            self.login_success.emit(self._auth.current_user)

    # ── Построение UI ────────────────────────────────────────

    def _build_ui(self):
        self.setObjectName("LoginScreen")

        # Полноэкранный фон
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Левая декоративная панель
        left = self._build_left_panel()
        root.addWidget(left, 1)

        # Правая панель с формой
        right = self._build_right_panel()
        root.addWidget(right, 0)

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border-right: 1px solid {Colors.BORDER};
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(0)

        # Логотип
        logo_row = QHBoxLayout()
        logo_row.setSpacing(12)

        icon_path = os.path.join(RESOURCES_DIR, "app_icon.png")
        if os.path.exists(icon_path):
            logo_lbl = QLabel()
            pixmap   = QPixmap(icon_path).scaled(
                40, 40,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_lbl.setPixmap(pixmap)
            logo_row.addWidget(logo_lbl)

        app_name = QLabel("ProfileNova")
        app_name.setFont(Typography.get_font(22, bold=True))
        app_name.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        logo_row.addWidget(app_name)
        logo_row.addStretch()
        layout.addLayout(logo_row)

        layout.addSpacing(Spacing.XXL * 2)

        # Слоган
        tagline = QLabel()
        tagline.setObjectName("tagline")
        tagline.setText(tr("login.subtitle"))
        tagline.setFont(Typography.get_font(15))
        tagline.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        tagline.setWordWrap(True)
        layout.addWidget(tagline)
        self._tagline_lbl = tagline

        layout.addSpacing(Spacing.LG)

        # Оранжевая линия-акцент
        line = QFrame()
        line.setFixedHeight(3)
        line.setFixedWidth(48)
        line.setStyleSheet(f"background-color: {Colors.ACCENT}; border: none;")
        layout.addWidget(line)

        layout.addStretch()

        # Версия внизу
        ver = QLabel("v2.0")
        ver.setProperty("role", "caption")
        ver.setStyleSheet(f"color: {Colors.TEXT_DISABLED}; font-size: 11px;")
        layout.addWidget(ver)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(420)
        panel.setStyleSheet(f"background-color: {Colors.BG_BASE};")

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)

        # Переключатель языка — правый верхний угол
        lang_row = QHBoxLayout()
        lang_row.addStretch()
        self._lang_combo = QComboBox()
        self._lang_combo.setFixedWidth(110)
        self._lang_combo.setFixedHeight(30)
        for code, name in available_languages():
            self._lang_combo.addItem(name, code)
        # Установить текущий язык
        idx = self._lang_combo.findData(get_language())
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        lang_row.setContentsMargins(0, 16, 16, 0)
        lang_row.addWidget(self._lang_combo)
        outer.addLayout(lang_row)

        # Центрируем форму по вертикали
        outer.addStretch(1)

        # Карточка формы
        card = QFrame()
        card.setProperty("role", "card")
        card.setFixedWidth(360)
        card.setStyleSheet(f"""
            QFrame[role="card"] {{
                background-color: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(Spacing.MD)

        # Заголовок формы
        self._title_lbl = QLabel(tr("login.title"))
        self._title_lbl.setProperty("role", "title")
        self._title_lbl.setFont(Typography.get_font(18, bold=True))
        self._title_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        card_layout.addWidget(self._title_lbl)
        card_layout.addSpacing(Spacing.SM)

        # Поле логина
        self._username_lbl = QLabel(tr("login.username"))
        self._username_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        card_layout.addWidget(self._username_lbl)

        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("login")
        self._username_input.setFixedHeight(Sizes.INPUT_HEIGHT)
        self._username_input.returnPressed.connect(self._on_login_clicked)
        card_layout.addWidget(self._username_input)
        card_layout.addSpacing(Spacing.SM)

        # Поле пароля
        self._password_lbl = QLabel(tr("login.password"))
        self._password_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        card_layout.addWidget(self._password_lbl)

        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(0)
        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setFixedHeight(Sizes.INPUT_HEIGHT)
        self._password_input.setStyleSheet(f"""
            QLineEdit {{
                border-right: none;
                border-top-right-radius: 0;
                border-bottom-right-radius: 0;
            }}
        """)
        self._password_input.returnPressed.connect(self._on_login_clicked)
        pwd_row.addWidget(self._password_input)

        self._show_pwd_btn = QToolButton()
        self._show_pwd_btn.setText("👁")
        self._show_pwd_btn.setFixedSize(Sizes.INPUT_HEIGHT, Sizes.INPUT_HEIGHT)
        self._show_pwd_btn.setCheckable(True)
        self._show_pwd_btn.setStyleSheet(f"""
            QToolButton {{
                background-color: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER};
                border-left: none;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                font-size: 14px;
                color: {Colors.TEXT_SECONDARY};
            }}
            QToolButton:hover {{ color: {Colors.TEXT_PRIMARY}; }}
            QToolButton:checked {{ color: {Colors.ACCENT}; }}
        """)
        self._show_pwd_btn.toggled.connect(self._toggle_password_visibility)
        pwd_row.addWidget(self._show_pwd_btn)
        card_layout.addLayout(pwd_row)
        card_layout.addSpacing(Spacing.SM)

        # Запомнить меня
        self._remember_cb = QCheckBox(tr("login.remember"))
        self._remember_cb.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        card_layout.addWidget(self._remember_cb)
        card_layout.addSpacing(Spacing.LG)

        # Сообщение об ошибке
        self._error_lbl = QLabel("")
        self._error_lbl.setProperty("role", "error")
        self._error_lbl.setStyleSheet(f"color: {Colors.ERROR}; font-size: 12px;")
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setVisible(False)
        card_layout.addWidget(self._error_lbl)

        # Кнопка входа
        self._login_btn = QPushButton(tr("login.btn"))
        self._login_btn.setProperty("accent", "true")
        self._login_btn.setFixedHeight(Sizes.BTN_HEIGHT_LG)
        self._login_btn.setFont(Typography.get_font(14, bold=True))
        self._login_btn.setStyleSheet(f"""
            QPushButton[accent="true"] {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton[accent="true"]:hover {{
                background-color: {Colors.ACCENT_HOVER};
            }}
            QPushButton[accent="true"]:pressed {{
                background-color: {Colors.ACCENT_PRESS};
            }}
        """)
        self._login_btn.clicked.connect(self._on_login_clicked)
        card_layout.addWidget(self._login_btn)

        # Центрировать карточку
        card_wrapper = QHBoxLayout()
        card_wrapper.addStretch()
        card_wrapper.addWidget(card)
        card_wrapper.addStretch()
        outer.addLayout(card_wrapper)
        outer.addStretch(1)

        return panel

    # ── Логика ───────────────────────────────────────────────

    def _on_login_clicked(self):
        self._set_error("")
        username = self._username_input.text().strip()
        password = self._password_input.text()

        if not username or not password:
            self._set_error(tr("login.error.empty"))
            return

        self._login_btn.setEnabled(False)
        self._login_btn.setText("...")

        ok, msg = self._auth.login(username, password)

        self._login_btn.setEnabled(True)
        self._login_btn.setText(tr("login.btn"))

        if ok:
            if self._remember_cb.isChecked():
                self._auth.save_session()
            self.login_success.emit(self._auth.current_user)
        else:
            if "не найден" in msg or "not found" in msg.lower():
                self._set_error(tr("login.error.wrong"))
            elif "отключен" in msg or "inactive" in msg.lower():
                self._set_error(tr("login.error.inactive"))
            else:
                self._set_error(tr("login.error.wrong"))
            self._password_input.clear()
            self._password_input.setFocus()

    def _set_error(self, message: str):
        if message:
            self._error_lbl.setText(message)
            self._error_lbl.setVisible(True)
            self._username_input.setProperty("error", "true")
            self._username_input.style().unpolish(self._username_input)
            self._username_input.style().polish(self._username_input)
        else:
            self._error_lbl.setVisible(False)
            self._username_input.setProperty("error", "false")
            self._username_input.style().unpolish(self._username_input)
            self._username_input.style().polish(self._username_input)

    def _toggle_password_visibility(self, checked: bool):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self._password_input.setEchoMode(mode)

    def _on_lang_changed(self):
        code = self._lang_combo.currentData()
        if code:
            set_language(code)

    # ── Перевод при смене языка ──────────────────────────────

    def _retranslate(self, lang: str = None):
        self._title_lbl.setText(tr("login.title"))
        self._tagline_lbl.setText(tr("login.subtitle"))
        self._username_lbl.setText(tr("login.username"))
        self._password_lbl.setText(tr("login.password"))
        self._remember_cb.setText(tr("login.remember"))
        self._login_btn.setText(tr("login.btn"))

    def showEvent(self, event):
        super().showEvent(event)
        self._username_input.setFocus()
