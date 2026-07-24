"""
ui/screens/main_window.py
==========================
Главное окно ProfileNova.

Навигация: MenuBar сверху (как в старой программе).
Разделы: Перегон / Станция / Подъездные пути / Чертёж / Вычисления / Администрирование
Строка статуса: пользователь | проект | режим | синхронизация
"""

import os
import sys
import logging

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget,
    QMenuBar, QMenu, QStatusBar, QLabel,
    QFrame, QHBoxLayout, QMessageBox
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, QTimer, Signal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import Colors, Typography, Spacing, Sizes
from ui.i18n  import tr, on_language_change, set_language, available_languages
from core.sync.engine import SyncStatus



# Индексы страниц
PAGE_MAINLINE   = 0
PAGE_STATION    = 1
PAGE_ACCESS_WAY = 2
PAGE_DRAWING    = 3
PAGE_CALC       = 4
PAGE_ADMIN      = 5


class MainWindow(QMainWindow):

    logout_requested = Signal()

    def __init__(self, ctx, project_id: int, is_editing: bool, parent=None):
        super().__init__(parent)
        self._ctx        = ctx
        self._project_id = project_id
        self._is_editing = is_editing
        self._project    = self._load_project()

        self._build_window()
        self._build_menubar()
        self._build_statusbar()
        self._build_pages()
        self._connect_sync()

        on_language_change(self._retranslate)

        # Heartbeat блокировки каждые 5 минут
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.timeout.connect(self._heartbeat)
        if self._is_editing:
            self._heartbeat_timer.start(300_000)

        # Обновлять статусбар каждые 5 сек
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_statusbar)
        self._status_timer.start(5_000)

        self._go_to(PAGE_MAINLINE)

    # ── Инициализация окна ───────────────────────────────────

    def _load_project(self) -> dict:
        row = self._ctx.db.fetchone(
            "SELECT * FROM projects WHERE id=?", (self._project_id,)
        )
        return row or {}

    def _build_window(self):
        name = self._project.get("name", f"Проект #{self._project_id}")
        mode = tr("mode.editing") if self._is_editing else tr("mode.viewing")
        user = self._ctx.auth.current_user.get("full_name", "")
        self.setWindowTitle(f"ProfileNova — {name} [{mode}] — {user}")
        self.setMinimumSize(1280, 780)

    # ── Меню ─────────────────────────────────────────────────

    def _build_menubar(self):
        mb = self.menuBar()
        mb.setStyleSheet(f"""
            QMenuBar {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border-bottom: 1px solid {Colors.BORDER};
                padding: 2px 4px;
                font-size: 13px;
            }}
            QMenuBar::item {{
                padding: 6px 14px;
                border-radius: 3px;
            }}
            QMenuBar::item:selected {{
                background-color: {Colors.BG_ELEVATED};
            }}
            QMenuBar::item:pressed {{
                background-color: {Colors.ACCENT_DIM};
                color: {Colors.ACCENT};
            }}
            QMenu {{
                background-color: {Colors.BG_OVERLAY};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                padding: 4px 0;
            }}
            QMenu::item {{
                padding: 8px 32px 8px 16px;
                font-size: 13px;
            }}
            QMenu::item:selected {{
                background-color: {Colors.BG_ELEVATED};
            }}
            QMenu::item:disabled {{
                color: {Colors.TEXT_DISABLED};
            }}
            QMenu::separator {{
                height: 1px;
                background: {Colors.BORDER};
                margin: 4px 8px;
            }}
        """)

        # ── Файл ──────────────────────────────────────────────
        self._menu_file = mb.addMenu("Файл")

        self._act_close_project = QAction("Закрыть проект", self)
        self._act_close_project.triggered.connect(self._close_project)
        self._menu_file.addAction(self._act_close_project)

        self._menu_file.addSeparator()

        self._act_export_excel = QAction("Экспорт в Excel...", self)
        self._act_export_excel.setShortcut(QKeySequence("Ctrl+E"))
        self._act_export_excel.triggered.connect(self._export_excel)
        self._menu_file.addAction(self._act_export_excel)

        self._menu_file.addSeparator()

        self._act_exit = QAction("Выход", self)
        self._act_exit.setShortcut(QKeySequence("Alt+F4"))
        self._act_exit.triggered.connect(self.close)
        self._menu_file.addAction(self._act_exit)

        # ── Правка ────────────────────────────────────────────
        self._menu_edit = mb.addMenu("Правка")

        self._act_copy = QAction("Копировать", self)
        self._act_copy.setShortcut(QKeySequence.StandardKey.Copy)
        self._act_copy.triggered.connect(self._edit_copy)
        self._menu_edit.addAction(self._act_copy)

        self._act_paste = QAction("Вставить", self)
        self._act_paste.setShortcut(QKeySequence.StandardKey.Paste)
        self._act_paste.triggered.connect(self._edit_paste)
        self._menu_edit.addAction(self._act_paste)

        self._act_cut = QAction("Вырезать", self)
        self._act_cut.setShortcut(QKeySequence.StandardKey.Cut)
        self._act_cut.triggered.connect(self._edit_cut)
        self._menu_edit.addAction(self._act_cut)

        self._menu_edit.addSeparator()

        self._act_undo = QAction("Отменить", self)
        self._act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self._act_undo.triggered.connect(self._edit_undo)
        self._menu_edit.addAction(self._act_undo)

        self._act_redo = QAction("Повторить", self)
        self._act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self._act_redo.triggered.connect(self._edit_redo)
        self._menu_edit.addAction(self._act_redo)

        self._menu_edit.addSeparator()

        self._act_select_all = QAction("Выделить всё", self)
        self._act_select_all.setShortcut(QKeySequence.StandardKey.SelectAll)
        self._act_select_all.triggered.connect(self._edit_select_all)
        self._menu_edit.addAction(self._act_select_all)

        self._act_delete = QAction("Удалить", self)
        self._act_delete.setShortcut(QKeySequence.StandardKey.Delete)
        self._act_delete.triggered.connect(self._edit_delete)
        self._menu_edit.addAction(self._act_delete)

        # ── Разделы (навигация) ───────────────────────────────
        self._menu_sections = mb.addMenu("Разделы")

        self._act_mainline = QAction(tr("nav.mainline"), self)
        self._act_mainline.setShortcut(QKeySequence("Ctrl+1"))
        self._act_mainline.triggered.connect(lambda: self._go_to(PAGE_MAINLINE))
        self._menu_sections.addAction(self._act_mainline)

        self._act_station = QAction(tr("nav.station"), self)
        self._act_station.setShortcut(QKeySequence("Ctrl+2"))
        self._act_station.triggered.connect(lambda: self._go_to(PAGE_STATION))
        self._menu_sections.addAction(self._act_station)

        self._act_access = QAction(tr("nav.access_way"), self)
        self._act_access.setShortcut(QKeySequence("Ctrl+3"))
        self._act_access.triggered.connect(lambda: self._go_to(PAGE_ACCESS_WAY))
        self._menu_sections.addAction(self._act_access)

        self._menu_sections.addSeparator()

        self._act_drawing = QAction(tr("nav.drawing"), self)
        self._act_drawing.setShortcut(QKeySequence("Ctrl+4"))
        self._act_drawing.triggered.connect(lambda: self._go_to(PAGE_DRAWING))
        self._menu_sections.addAction(self._act_drawing)

        self._act_calc = QAction(tr("nav.calculations"), self)
        self._act_calc.setShortcut(QKeySequence("Ctrl+5"))
        self._act_calc.triggered.connect(lambda: self._go_to(PAGE_CALC))
        self._menu_sections.addAction(self._act_calc)

        # ── Режим ─────────────────────────────────────────────
        self._menu_mode = mb.addMenu(
            tr("mode.editing") if self._is_editing else tr("mode.viewing")
        )

        self._act_switch_mode = QAction(
            tr("mode.switch_to_view") if self._is_editing else tr("mode.switch_to_edit"),
            self
        )
        self._act_switch_mode.triggered.connect(self._switch_mode)
        self._menu_mode.addAction(self._act_switch_mode)

        # ── Администрирование (только admin) ──────────────────
        if self._ctx.auth.is_admin:
            self._menu_admin = mb.addMenu(tr("nav.admin"))

            self._act_users = QAction(tr("admin.users"), self)
            self._act_users.triggered.connect(lambda: self._go_to(PAGE_ADMIN))
            self._menu_admin.addAction(self._act_users)

            self._act_audit = QAction(tr("admin.audit_log"), self)
            self._act_audit.triggered.connect(self._show_audit_log)
            self._menu_admin.addAction(self._act_audit)

        # ── Язык ──────────────────────────────────────────────
        self._menu_lang = mb.addMenu("Язык / Тіл")
        for code, name in available_languages():
            act = QAction(name, self)
            act.triggered.connect(lambda checked, c=code: self._switch_lang(c))
            self._menu_lang.addAction(act)

        # ── Справка ───────────────────────────────────────────
        self._menu_help = mb.addMenu("Справка")
        act_about = QAction("О программе", self)
        act_about.triggered.connect(self._show_about)
        self._menu_help.addAction(act_about)

    # ── Статусбар ────────────────────────────────────────────

    def _build_statusbar(self):
        sb = QStatusBar()
        sb.setStyleSheet(f"""
            QStatusBar {{
                background-color: {Colors.BG_SURFACE};
                border-top: 1px solid {Colors.BORDER};
                font-size: 11px;
                color: {Colors.TEXT_SECONDARY};
            }}
            QStatusBar::item {{ border: none; }}
        """)
        self.setStatusBar(sb)

        # Пользователь
        user = self._ctx.auth.current_user
        self._sb_user = QLabel(
            f"  👤 {user.get('full_name', '')}  |  {tr('admin.role_' + user.get('role','viewer'))}"
        )
        sb.addWidget(self._sb_user)

        sb.addWidget(self._separator())

        # Проект
        self._sb_project = QLabel(
            f"📁 {self._project.get('name', '')}"
        )
        sb.addWidget(self._sb_project)

        sb.addWidget(self._separator())

        # Режим
        self._sb_mode = QLabel("")
        self._update_mode_label()
        sb.addWidget(self._sb_mode)

        # Синхронизация — справа
        self._sb_sync = QLabel("⚪ —")
        self._sb_sync.setAlignment(Qt.AlignmentFlag.AlignRight)
        sb.addPermanentWidget(self._sb_sync)

        # Секция
        self._sb_section = QLabel("")
        sb.addPermanentWidget(self._sb_section)

    def _separator(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.VLine)
        f.setFixedHeight(16)
        f.setStyleSheet(f"color: {Colors.BORDER};")
        return f

    def _update_mode_label(self):
        if self._is_editing:
            self._sb_mode.setText(
                f"<span style='color:{Colors.ACCENT};'>✏ {tr('mode.editing')}</span>"
            )
        else:
            self._sb_mode.setText(
                f"<span style='color:{Colors.TEXT_SECONDARY};'>👁 {tr('mode.viewing')}</span>"
            )

    def _refresh_statusbar(self):
        pass  # расширим в следующих модулях

    # ── Страницы ─────────────────────────────────────────────

    def _build_pages(self):
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)
        self._loaded_pages = {}
    
        # Добавляем заглушки для всех 6 страниц
        for i in range(6):
            placeholder = QWidget()
            placeholder.setStyleSheet(f"background-color: {Colors.BG_BASE};")
            self._stack.addWidget(placeholder)
    
    def _go_to(self, page: int):
        # Ленивая загрузка — создаём страницу только при первом переходе
        if page not in self._loaded_pages:
            self._load_page(page)
    
        self._stack.setCurrentIndex(page)
        names = [
            tr("nav.mainline"), tr("nav.station"), tr("nav.access_way"),
            tr("nav.drawing"),  tr("nav.calculations"), tr("nav.admin")
        ]
        if 0 <= page < len(names):
            self._sb_section.setText(f"{names[page]}  ")
    
    def _load_page(self, page: int):
        """Создать страницу при первом обращении."""
        widget = None
        try:
            if page == PAGE_MAINLINE:
                from ui.screens.mainline_page import MainlinePage
                widget = MainlinePage(self._ctx, self._project_id, self._is_editing)
                self._page_mainline = widget
            elif page == PAGE_STATION:
                from ui.screens.station_page import StationPage
                widget = StationPage(self._ctx, self._project_id, self._is_editing)
                self._page_station = widget
            elif page == PAGE_ACCESS_WAY:
                from ui.screens.access_way_page import AccessWayPage
                widget = AccessWayPage(self._ctx, self._project_id, self._is_editing)
                self._page_access = widget
            elif page == PAGE_DRAWING:
                from ui.screens.drawing_page import DrawingPage
                widget = DrawingPage(self._ctx, self._project_id, self._is_editing)
                self._page_drawing = widget
            elif page == PAGE_CALC:
                from ui.screens.calc_page import CalcPage
                widget = CalcPage(self._ctx, self._project_id)
                self._page_calc = widget
            elif page == PAGE_ADMIN:
                from ui.screens.admin_page import AdminPage
                widget = AdminPage(self._ctx)
                self._page_admin = widget
        except Exception as e:
            import traceback
            logging.getLogger("main").error(
                f"_load_page({page}) ОШИБКА:\n{traceback.format_exc()}"
            )
            widget = self._placeholder(f"Ошибка", str(e))
    
        if widget:
            # Заменяем заглушку реальной страницей
            self._stack.removeWidget(self._stack.widget(page))
            self._stack.insertWidget(page, widget)
            self._loaded_pages[page] = widget

    def _placeholder(self, section: str, module: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background-color: {Colors.BG_BASE};")
        layout = QHBoxLayout(w)
        lbl = QLabel(f"{section}\n\n{module}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"""
            color: {Colors.TEXT_DISABLED};
            font-size: 16px;
        """)
        layout.addWidget(lbl)
        return w

    # ── Действия меню ────────────────────────────────────────

    def _edit_copy(self):
        w = self.focusWidget()
        if hasattr(w, "copy"):
            w.copy()

    def _edit_paste(self):
        w = self.focusWidget()
        if hasattr(w, "paste"):
            w.paste()

    def _edit_cut(self):
        w = self.focusWidget()
        if hasattr(w, "cut"):
            w.cut()

    def _edit_undo(self):
        w = self.focusWidget()
        if hasattr(w, "undo"):
            w.undo()

    def _edit_redo(self):
        w = self.focusWidget()
        if hasattr(w, "redo"):
            w.redo()

    def _edit_select_all(self):
        w = self.focusWidget()
        if hasattr(w, "selectAll"):
            w.selectAll()

    def _edit_delete(self):
        w = self.focusWidget()
        if hasattr(w, "clear"):
            w.clear()

    def _export_excel(self):
        page = self._stack.currentWidget()
        if hasattr(page, "export_excel"):
            page.export_excel()

    def _switch_mode(self):
        if self._is_editing:
            # Переключиться в просмотр — снять блокировку
            reply = QMessageBox.question(
                self, "Переключить режим",
                "Перейти в режим просмотра?\nДругие пользователи смогут взять проект на редактирование.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._ctx.auth.release_project_lock(self._project_id)
                self._ctx.sync.set_editing(False)
                self._is_editing = False
                self._heartbeat_timer.stop()
                self._update_ui_for_mode()
        else:
            # Попытка взять на редактирование
            success, who = self._ctx.auth.acquire_project_lock(self._project_id)
            if success:
                self._ctx.sync.set_editing(True)
                self._is_editing = True
                self._heartbeat_timer.start(300_000)
                self._update_ui_for_mode()
            else:
                QMessageBox.warning(
                    self, "Занято",
                    tr("projects.locked_msg", user=who)
                )

    def _update_ui_for_mode(self):
        mode = tr("mode.editing") if self._is_editing else tr("mode.viewing")
        name = self._project.get("name", "")
        user = self._ctx.auth.current_user.get("full_name", "")
        self.setWindowTitle(f"ProfileNova — {name} [{mode}] — {user}")
        self._menu_mode.setTitle(mode)
        self._act_switch_mode.setText(
            tr("mode.switch_to_view") if self._is_editing else tr("mode.switch_to_edit")
        )
        self._update_mode_label()

    def _switch_lang(self, code: str):
        set_language(code)
        self._ctx.db.execute(
            "INSERT OR REPLACE INTO app_meta (key, value) VALUES ('language', ?)",
            (code,)
        )
        self._ctx.db.commit()

    def _show_about(self):
        QMessageBox.about(
            self, "О программе",
            "ProfileNova v2.0\n\nСистема путевой документации\n"
            "Железнодорожный профиль"
        )

    def _show_audit_log(self):
        self._go_to(PAGE_ADMIN)
        # Переключить на вкладку журнала
        if hasattr(self, "_page_admin"):
            self._page_admin._tabs.setCurrentIndex(2)

    def _heartbeat(self):
        if self._is_editing:
            self._ctx.auth.heartbeat(self._project_id)

    # ── Синхронизация → статусбар ────────────────────────────

    def _connect_sync(self):
        pass  # статус синхронизации — в следующей итерации

    def _on_sync_status(self, status: str, message: str, pending: int = 0):
        icons = {
            SyncStatus.OK:      f"<span style='color:{Colors.SUCCESS};'>● </span>",
            SyncStatus.OFFLINE: f"<span style='color:{Colors.WARNING};'>● </span>",
            SyncStatus.SYNCING: f"<span style='color:{Colors.INFO};'>● </span>",
            SyncStatus.ERROR:   f"<span style='color:{Colors.ERROR};'>● </span>",
        }
        icon = icons.get(status, "⚪ ")
        text = message[:60] + "..." if len(message) > 60 else message
        self._sb_sync.setText(f"{icon}{text}  ")

    # ── Перевод ──────────────────────────────────────────────

    def _retranslate(self, lang=None):
        self._act_mainline.setText(tr("nav.mainline"))
        self._act_station.setText(tr("nav.station"))
        self._act_access.setText(tr("nav.access_way"))
        self._act_drawing.setText(tr("nav.drawing"))
        self._act_calc.setText(tr("nav.calculations"))
        self._update_ui_for_mode()

    # ── Закрытие ─────────────────────────────────────────────

    def closeEvent(self, event):
        # closeEvent больше не показывает диалог — всё обрабатывается в _close_project
        self._heartbeat_timer.stop()
        self._status_timer.stop()
        event.accept()
    
    def keyPressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.key() == Qt.Key.Key_Escape:
            self._close_project()
        else:
            super().keyPressEvent(event)
    
    def _close_project(self):
        # Шаг 1: сразу спросить подтверждение
        if self._is_editing:
            reply = QMessageBox.question(
                self, "Закрыть проект",
                "Закрыть проект?\nБлокировка редактирования будет снята.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            self._ctx.auth.release_project_lock(self._project_id)
    
        # Шаг 2: показать индикатор загрузки
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PySide6.QtCore import Qt, QTimer
    
        loading = QDialog(self)
        loading.setWindowTitle("")
        loading.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        loading.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        loading.setFixedSize(320, 100)
        loading.setStyleSheet(f"""
            QDialog {{
                background-color: #1A1A1A;
                border: 1px solid #FF6B00;
                border-radius: 8px;
            }}
        """)
        lay = QVBoxLayout(loading)
        lbl = QLabel("💾  Сохранение... Проект закрывается, подождите")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #F0F0F0; font-size: 13px; padding: 20px;")
        lay.addWidget(lbl)
        loading.show()
    
        # Шаг 3: завершить сессию и вернуться к проектам
        def _do_close():
            self._ctx.end_session(self._project_id)
            loading.close()
            self.logout_requested.emit()
            self.close()
    
        QTimer.singleShot(300, _do_close)