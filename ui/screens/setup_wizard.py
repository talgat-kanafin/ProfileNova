"""
ui/screens/setup_wizard.py
==========================
Визард первоначальной настройки — появляется при первом запуске.

Шаг 1: Подключение к облаку (Supabase) — или пропустить
Шаг 2: Создание учётной записи администратора
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QStackedWidget,
    QCheckBox, QProgressBar, QWidget
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import Colors, Typography, Spacing, Sizes
from ui.i18n  import tr


class ConnectionTestThread(QThread):
    result = Signal(bool, str)

    def __init__(self, db_url: str):
        super().__init__()
        self._url = db_url

    def run(self):
        try:
            import psycopg2
            conn = psycopg2.connect(self._url, connect_timeout=5)
            conn.close()
            self.result.emit(True, "OK")
        except ImportError:
            self.result.emit(False, "psycopg2 не установлен")
        except Exception as e:
            self.result.emit(False, str(e))


class SetupWizard(QDialog):
    """
    Диалог первоначальной настройки.
    Запускается если config/setup_done не существует.
    """
    setup_complete = Signal()

    def __init__(self, local_db, parent=None):
        super().__init__(parent)
        self._db          = local_db
        self._cloud_url   = ""
        self._cloud_key   = ""
        self._cloud_db_url= ""
        self._test_thread = None

        self.setWindowTitle(tr("setup.title"))
        self.setFixedSize(560, 500)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self._build_ui()

    # ── Построение UI ────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Заголовок
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"""
            background-color: {Colors.ACCENT};
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(32, 0, 32, 0)

        title = QLabel(tr("setup.welcome"))
        title.setFont(Typography.get_font(20, bold=True))
        title.setStyleSheet("color: white;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        # Индикатор шагов
        self._step_lbl = QLabel("1 / 2")
        self._step_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px;")
        h_layout.addWidget(self._step_lbl)

        layout.addWidget(header)

        # Прогрессбар шагов
        self._progress = QProgressBar()
        self._progress.setRange(0, 2)
        self._progress.setValue(1)
        self._progress.setFixedHeight(3)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Colors.BG_ELEVATED};
                border: none;
                border-radius: 0;
            }}
            QProgressBar::chunk {{
                background-color: {Colors.ACCENT};
            }}
        """)
        layout.addWidget(self._progress)

        # Стек страниц
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_step1())
        self._stack.addWidget(self._build_step2())
        layout.addWidget(self._stack, 1)

        # Кнопки навигации
        nav = QFrame()
        nav.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border-top: 1px solid {Colors.BORDER};
        """)
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(32, 16, 32, 16)

        self._back_btn = QPushButton(tr("btn.back"))
        self._back_btn.setProperty("ghost", "true")
        self._back_btn.setFixedHeight(Sizes.BTN_HEIGHT)
        self._back_btn.setFixedWidth(100)
        self._back_btn.setVisible(False)
        self._back_btn.clicked.connect(self._go_back)
        nav_layout.addWidget(self._back_btn)

        nav_layout.addStretch()

        self._next_btn = QPushButton(tr("btn.confirm"))
        self._next_btn.setProperty("accent", "true")
        self._next_btn.setFixedHeight(Sizes.BTN_HEIGHT)
        self._next_btn.setFixedWidth(160)
        self._next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {Colors.ACCENT_HOVER}; }}
            QPushButton:disabled {{ background-color: {Colors.BG_OVERLAY}; color: {Colors.TEXT_DISABLED}; }}
        """)
        self._next_btn.clicked.connect(self._go_next)
        nav_layout.addWidget(self._next_btn)

        layout.addWidget(nav)

    def _build_step1(self) -> QWidget:
        """Шаг 1 — Настройка облака."""
        w = QWidget()
        w.setStyleSheet(f"background-color: {Colors.BG_BASE};")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(32, 32, 32, 16)
        layout.setSpacing(Spacing.MD)

        title = QLabel(tr("setup.step_cloud"))
        title.setFont(Typography.get_font(15, bold=True))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)

        desc = QLabel(
            "Подключите облачный сервер Supabase для синхронизации данных между пользователями.\n"
            "Если сервер недоступен сейчас — можно настроить позже."
        )
        desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addWidget(self._divider())

        # Supabase URL
        layout.addWidget(self._field_label(tr("setup.supabase_url")))
        self._supabase_url = QLineEdit()
        self._supabase_url.setPlaceholderText("https://xxxx.supabase.co")
        self._supabase_url.setFixedHeight(Sizes.INPUT_HEIGHT)
        layout.addWidget(self._supabase_url)

        # Supabase Key
        layout.addWidget(self._field_label(tr("setup.supabase_key")))
        self._supabase_key = QLineEdit()
        self._supabase_key.setPlaceholderText("eyJ...")
        self._supabase_key.setFixedHeight(Sizes.INPUT_HEIGHT)
        layout.addWidget(self._supabase_key)

        # DB URL
        layout.addWidget(self._field_label(tr("setup.db_url")))
        self._db_url = QLineEdit()
        self._db_url.setPlaceholderText("postgresql://postgres:password@db.xxxx.supabase.co:5432/postgres")
        self._db_url.setFixedHeight(Sizes.INPUT_HEIGHT)
        layout.addWidget(self._db_url)

        # Кнопка проверки + статус
        test_row = QHBoxLayout()
        self._test_btn = QPushButton(tr("settings.cloud_test"))
        self._test_btn.setFixedHeight(34)
        self._test_btn.setFixedWidth(200)
        self._test_btn.clicked.connect(self._test_connection)
        test_row.addWidget(self._test_btn)

        self._test_status = QLabel("")
        self._test_status.setStyleSheet(f"font-size: 12px; padding-left: 8px;")
        test_row.addWidget(self._test_status)
        test_row.addStretch()
        layout.addLayout(test_row)

        layout.addStretch()

        # Пропустить
        skip_row = QHBoxLayout()
        skip_row.addStretch()
        self._skip_btn = QPushButton(tr("setup.skip_cloud"))
        self._skip_btn.setProperty("ghost", "true")
        self._skip_btn.setFixedHeight(32)
        self._skip_btn.clicked.connect(self._skip_cloud)
        skip_row.addWidget(self._skip_btn)
        layout.addLayout(skip_row)

        return w

    def _build_step2(self) -> QWidget:
        """Шаг 2 — Учётная запись администратора."""
        w = QWidget()
        w.setStyleSheet(f"background-color: {Colors.BG_BASE};")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(32, 32, 32, 16)
        layout.setSpacing(Spacing.MD)

        title = QLabel(tr("setup.step_admin"))
        title.setFont(Typography.get_font(15, bold=True))
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)

        desc = QLabel("Создайте учётную запись главного администратора системы.")
        desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(desc)

        layout.addWidget(self._divider())

        layout.addWidget(self._field_label(tr("setup.admin_fullname") + " *"))
        self._admin_fullname = QLineEdit()
        self._admin_fullname.setPlaceholderText("Иванов Иван Иванович")
        self._admin_fullname.setFixedHeight(Sizes.INPUT_HEIGHT)
        layout.addWidget(self._admin_fullname)

        layout.addWidget(self._field_label(tr("setup.admin_username") + " *"))
        self._admin_username = QLineEdit()
        self._admin_username.setPlaceholderText("admin")
        self._admin_username.setFixedHeight(Sizes.INPUT_HEIGHT)
        layout.addWidget(self._admin_username)

        layout.addWidget(self._field_label(tr("setup.admin_password") + " *"))
        self._admin_password = QLineEdit()
        self._admin_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._admin_password.setPlaceholderText("Минимум 8 символов")
        self._admin_password.setFixedHeight(Sizes.INPUT_HEIGHT)
        layout.addWidget(self._admin_password)

        layout.addWidget(self._field_label(tr("setup.admin_password2") + " *"))
        self._admin_password2 = QLineEdit()
        self._admin_password2.setEchoMode(QLineEdit.EchoMode.Password)
        self._admin_password2.setFixedHeight(Sizes.INPUT_HEIGHT)
        layout.addWidget(self._admin_password2)

        self._step2_error = QLabel("")
        self._step2_error.setStyleSheet(f"color: {Colors.ERROR}; font-size: 12px;")
        self._step2_error.setVisible(False)
        layout.addWidget(self._step2_error)

        layout.addStretch()
        return w

    # ── Навигация по шагам ───────────────────────────────────

    def _go_next(self):
        step = self._stack.currentIndex()
        if step == 0:
            self._finish_step1()
        elif step == 1:
            self._finish_step2()

    def _go_back(self):
        self._stack.setCurrentIndex(0)
        self._step_lbl.setText("1 / 2")
        self._progress.setValue(1)
        self._back_btn.setVisible(False)
        self._next_btn.setText(tr("btn.confirm"))

    def _finish_step1(self):
        """Сохранить настройки облака и перейти к шагу 2."""
        url = self._supabase_url.text().strip()
        key = self._supabase_key.text().strip()
        db  = self._db_url.text().strip()

        if url and key and db:
            from core.db.cloud import CloudDB
            CloudDB.save_config(url, key, db)
            self._cloud_url    = url
            self._cloud_key    = key
            self._cloud_db_url = db

        self._goto_step2()

    def _skip_cloud(self):
        self._goto_step2()

    def _goto_step2(self):
        self._stack.setCurrentIndex(1)
        self._step_lbl.setText("2 / 2")
        self._progress.setValue(2)
        self._back_btn.setVisible(True)
        self._next_btn.setText(tr("setup.finish"))
        self._admin_fullname.setFocus()

    def _finish_step2(self):
        """Создать admin и завершить настройку."""
        fullname  = self._admin_fullname.text().strip()
        username  = self._admin_username.text().strip()
        password  = self._admin_password.text()
        password2 = self._admin_password2.text()

        # Валидация
        if not fullname or not username or not password:
            self._show_step2_error("Заполните все обязательные поля")
            return

        if len(username) < 3:
            self._show_step2_error("Логин должен быть не менее 3 символов")
            return

        if len(password) < 8:
            self._show_step2_error("Пароль должен быть не менее 8 символов")
            return

        if password != password2:
            self._show_step2_error("Пароли не совпадают")
            self._admin_password2.clear()
            self._admin_password2.setFocus()
            return

        # Удалить дефолтного admin и создать нового
        self._db.execute("DELETE FROM users WHERE username='admin'")
        self._db.commit()

        from core.auth.auth import hash_password
        self._db.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role, is_active)
            VALUES (?, ?, ?, 'admin', 1)
            """,
            (username, hash_password(password), fullname)
        )
        self._db.commit()

        # Записать флаг что настройка выполнена
        config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config"
        )
        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, "setup_done"), "w") as f:
            f.write("1")

        self.setup_complete.emit()
        self.accept()

    def _show_step2_error(self, msg: str):
        self._step2_error.setText(msg)
        self._step2_error.setVisible(True)

    # ── Проверка соединения ──────────────────────────────────

    def _test_connection(self):
        db_url = self._db_url.text().strip()
        if not db_url:
            self._test_status.setText("Введите Database URL")
            self._test_status.setStyleSheet(f"color: {Colors.WARNING}; font-size: 12px;")
            return

        self._test_btn.setEnabled(False)
        self._test_btn.setText("Проверяю...")
        self._test_status.setText("")

        self._test_thread = ConnectionTestThread(db_url)
        self._test_thread.result.connect(self._on_test_result)
        self._test_thread.start()

    def _on_test_result(self, success: bool, message: str):
        self._test_btn.setEnabled(True)
        self._test_btn.setText(tr("settings.cloud_test"))
        if success:
            self._test_status.setText(f"✓ {tr('settings.cloud_ok')}")
            self._test_status.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 12px;")
        else:
            self._test_status.setText(f"✗ {message}")
            self._test_status.setStyleSheet(f"color: {Colors.ERROR}; font-size: 12px;")

    # ── Утилиты ──────────────────────────────────────────────

    @staticmethod
    def _field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        return lbl

    @staticmethod
    def _divider() -> QFrame:
        d = QFrame()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background-color: {Colors.BORDER};")
        return d

    @staticmethod
    def needs_setup() -> bool:
        """True если первый запуск (файл setup_done отсутствует)."""
        config_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config"
        )
        return not os.path.exists(os.path.join(config_dir, "setup_done"))
