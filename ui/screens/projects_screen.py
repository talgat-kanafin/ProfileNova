"""
ui/screens/projects_screen.py
==============================
Экран списка проектов.

- Карточки проектов со статусом блокировки
- Кто редактирует — показывается в реальном времени (опрос каждые 10 сек)
- Кнопки: открыть на редактирование / просмотр
- Импорт из .mdb
- Создать новый проект (пустой)
- Поиск по названию
- Только admin видит все проекты, editor/viewer — только свои
"""

import os
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QFrame,
    QMessageBox, QFileDialog, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import Colors, Typography, Spacing, Sizes
from ui.i18n  import tr, on_language_change
from ui.screens.project_import_dialog import ProjectImportDialog
from ui.screens.project_new_dialog    import ProjectNewDialog


class ProjectCard(QFrame):
    """
    Карточка одного проекта.
    Сигналы: open_edit(project_id), open_view(project_id)
    """
    open_edit = Signal(int)
    open_view = Signal(int)

    def __init__(self, project: dict, lock_info: dict,
                 can_edit: bool, is_admin: bool, parent=None):
        super().__init__(parent)
        self._project   = project
        self._lock_info = lock_info   # None если свободен
        self._can_edit  = can_edit
        self._is_admin  = is_admin
        self._build_ui()

    def update_lock(self, lock_info: dict):
        """Обновить статус блокировки без пересоздания карточки."""
        self._lock_info = lock_info
        self._refresh_lock_ui()

    # ── UI ───────────────────────────────────────────────────

    def _build_ui(self):
        self.setFixedHeight(110)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
            }}
            QFrame:hover {{
                border-color: {Colors.TEXT_DISABLED};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(Spacing.LG)

        # Левая часть: иконка статуса
        self._status_bar = QFrame()
        self._status_bar.setFixedWidth(4)
        self._status_bar.setStyleSheet(f"border-radius: 2px; border: none;")
        layout.addWidget(self._status_bar)

        # Центр: название + мета
        info = QVBoxLayout()
        info.setSpacing(4)

        self._name_lbl = QLabel(self._project.get("name", ""))
        self._name_lbl.setFont(Typography.get_font(14, bold=True))
        self._name_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")
        info.addWidget(self._name_lbl)

        desc = self._project.get("description", "") or ""
        if desc:
            self._desc_lbl = QLabel(desc)
            self._desc_lbl.setStyleSheet(
                f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; border: none;"
            )
            self._desc_lbl.setWordWrap(True)
            info.addWidget(self._desc_lbl)

        self._lock_lbl = QLabel("")
        self._lock_lbl.setStyleSheet(f"font-size: 11px; border: none;")
        info.addWidget(self._lock_lbl)

        info.addStretch()
        layout.addLayout(info, 1)

        # Правая часть: кнопки
        btn_col = QVBoxLayout()
        btn_col.setSpacing(Spacing.XS)
        btn_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._btn_edit = QPushButton(tr("projects.open_edit"))
        self._btn_edit.setFixedHeight(34)
        self._btn_edit.setFixedWidth(200)
        self._btn_edit.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {Colors.ACCENT_HOVER}; }}
            QPushButton:pressed {{ background-color: {Colors.ACCENT_PRESS}; }}
            QPushButton:disabled {{
                background-color: {Colors.BG_OVERLAY};
                color: {Colors.TEXT_DISABLED};
            }}
        """)
        self._btn_edit.clicked.connect(
            lambda: self.open_edit.emit(self._project["id"])
        )
        btn_col.addWidget(self._btn_edit)

        self._btn_view = QPushButton(tr("projects.open_view"))
        self._btn_view.setFixedHeight(34)
        self._btn_view.setFixedWidth(200)
        self._btn_view.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_ELEVATED};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        self._btn_view.clicked.connect(
            lambda: self.open_view.emit(self._project["id"])
        )
        btn_col.addWidget(self._btn_view)
        layout.addLayout(btn_col)

        self._refresh_lock_ui()

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = self._on_click
        self._selected = False

    def _on_click(self, event):
        # Уведомить родителя о выделении
        if hasattr(self.parent(), '_on_card_selected'):
            self.parent()._on_card_selected(self._project["id"])

    def _refresh_lock_ui(self):
        lock = self._lock_info
        is_locked_by_other = (
            lock is not None and
            lock.get("user_fullname") != ""
        )

        if is_locked_by_other:
            who = lock.get("user_fullname", "?")
            self._lock_lbl.setText(f"🔴  {tr('projects.locked_by')} {who}")
            self._lock_lbl.setStyleSheet(
                f"color: {Colors.ERROR}; font-size: 11px; border: none;"
            )
            self._status_bar.setStyleSheet(
                f"background-color: {Colors.ERROR}; border-radius: 2px; border: none;"
            )
            self._btn_edit.setEnabled(False)
            self._btn_edit.setText("🔒 " + tr("projects.locked_by") + " " + who)
        else:
            self._lock_lbl.setText(f"🟢  {tr('projects.free')}")
            self._lock_lbl.setStyleSheet(
                f"color: {Colors.SUCCESS}; font-size: 11px; border: none;"
            )
            self._status_bar.setStyleSheet(
                f"background-color: {Colors.SUCCESS}; border-radius: 2px; border: none;"
            )
            self._btn_edit.setEnabled(self._can_edit)
            self._btn_edit.setText(tr("projects.open_edit"))

        # Если нет прав на редактирование вообще
        if not self._can_edit and not self._is_admin:
            self._btn_edit.setEnabled(False)
            self._btn_edit.setText(tr("projects.no_access"))


class ProjectsScreen(QWidget):
    """
    Главный экран выбора проекта.
    Сигнал project_selected(project_id, is_editing)
    """
    project_selected = Signal(int, bool)   # (project_id, is_editing)

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self._ctx   = ctx          # AppContext
        self._cards : dict[int, ProjectCard] = {}
        self._all_projects: list[dict] = []

        self._build_ui()
        self._load_projects()

        # Опрос блокировок каждые 10 сек
        self._lock_timer = QTimer(self)
        self._lock_timer.timeout.connect(self._refresh_locks)
        self._lock_timer.start(10_000)

        on_language_change(self._retranslate)

    # ── UI ───────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Тулбар
        toolbar = QFrame()
        toolbar.setFixedHeight(Sizes.TOOLBAR_HEIGHT)
        toolbar.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border-bottom: 1px solid {Colors.BORDER};
        """)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(Spacing.XL, 0, Spacing.XL, 0)
        tb_layout.setSpacing(Spacing.MD)

        self._title_lbl = QLabel(tr("projects.title"))
        self._title_lbl.setFont(Typography.get_font(15, bold=True))
        self._title_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        tb_layout.addWidget(self._title_lbl)

        tb_layout.addStretch()

        # Поиск
        self._search = QLineEdit()
        self._search.setPlaceholderText(tr("projects.search"))
        self._search.setFixedWidth(240)
        self._search.setFixedHeight(32)
        self._search.textChanged.connect(self._filter_cards)
        tb_layout.addWidget(self._search)

        # Кнопка импорта .mdb
        self._btn_import = QPushButton("⬆  " + tr("projects.import_mdb"))
        self._btn_import.setFixedHeight(32)
        self._btn_import.clicked.connect(self._on_import_mdb)
        tb_layout.addWidget(self._btn_import)

        btn_delete = QPushButton("🗑  Удалить")
        btn_delete.setFixedHeight(32)
        btn_delete.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_ELEVATED};
                color: {Colors.ERROR};
                border: 1px solid {Colors.ERROR};
                border-radius: 4px;
                padding: 0 12px;
            }}
            QPushButton:hover {{ background-color: {Colors.ERROR}; color: white; }}
        """)
        btn_delete.clicked.connect(self._on_delete_project)
        tb_layout.addWidget(btn_delete)

        # Кнопка нового проекта — только admin
        if self._ctx.auth.is_admin:
            self._btn_new = QPushButton("＋  " + tr("projects.new"))
            self._btn_new.setFixedHeight(32)
            self._btn_new.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.ACCENT};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: 600;
                    padding: 0 16px;
                }}
                QPushButton:hover {{ background-color: {Colors.ACCENT_HOVER}; }}
            """)
            self._btn_new.clicked.connect(self._on_new_project)
            tb_layout.addWidget(self._btn_new)

        root.addWidget(toolbar)

        # Область прокрутки карточек
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {Colors.BG_BASE}; }}
        """)

        self._cards_container = QWidget()
        self._cards_container.setStyleSheet(
            f"background-color: {Colors.BG_BASE};"
        )
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        self._cards_layout.setSpacing(Spacing.MD)
        self._cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Заглушка "нет проектов"
        self._empty_lbl = QLabel(tr("projects.empty"))
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {Colors.TEXT_DISABLED}; font-size: 14px;"
        )
        self._empty_lbl.setVisible(False)
        self._cards_layout.addWidget(self._empty_lbl)

        scroll.setWidget(self._cards_container)
        root.addWidget(scroll, 1)

        # Статусная строка внизу
        self._statusbar = QLabel("")
        self._statusbar.setFixedHeight(Sizes.STATUSBAR_HEIGHT)
        self._statusbar.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            color: {Colors.TEXT_SECONDARY};
            border-top: 1px solid {Colors.BORDER};
            padding: 0 {Spacing.XL}px;
            font-size: 11px;
        """)
        root.addWidget(self._statusbar)

    # ── Загрузка данных ──────────────────────────────────────

    def _load_projects(self):
        for card in self._cards.values():
            card.deleteLater()
        self._cards.clear()
    
        self._all_projects = self._ctx.auth.get_accessible_projects()
    
        if not self._all_projects:
            self._empty_lbl.setVisible(True)
            self._statusbar.setText(tr("projects.empty"))
            return
    
        self._empty_lbl.setVisible(False)
    
        # Один батч-запрос для всех блокировок
        pids = [p["id"] for p in self._all_projects]
        locks = self._ctx.auth.prefetch_locks(pids)
    
        for project in self._all_projects:
            pid      = project["id"]
            can_edit = self._ctx.auth.can_edit_project(pid)
            lock     = locks.get(pid)
    
            card = ProjectCard(
                project   = project,
                lock_info = lock,
                can_edit  = can_edit,
                is_admin  = self._ctx.auth.is_admin
            )
            card.open_edit.connect(self._on_open_edit)
            card.open_view.connect(self._on_open_view)
            card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            card.customContextMenuRequested.connect(
                lambda pos, p=project: self._card_context_menu(pos, p["id"])
            )
    
            self._cards_layout.addWidget(card)
            self._cards[pid] = card
    
        self._statusbar.setText(f"Проектов: {len(self._all_projects)}")

    def _add_card(self, project: dict):
        pid      = project["id"]
        can_edit = self._ctx.auth.can_edit_project(pid)
        lock     = self._ctx.auth.get_project_lock_info(pid)

        card = ProjectCard(
            project   = project,
            lock_info = lock,
            can_edit  = can_edit,
            is_admin  = self._ctx.auth.is_admin
        )
        card.open_edit.connect(self._on_open_edit)
        card.open_view.connect(self._on_open_view)
        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(
            lambda pos, p=project: self._card_context_menu(pos, p["id"])
        )

        self._cards_layout.addWidget(card)
        self._cards[pid] = card

    def _refresh_locks(self):
        if not self._cards:
            return
        pids  = list(self._cards.keys())
        locks = self._ctx.auth.prefetch_locks(pids)
        for pid, card in self._cards.items():
            card.update_lock(locks.get(pid))

    # ── Фильтрация ───────────────────────────────────────────

    def _filter_cards(self, text: str):
        text = text.lower().strip()
        visible = 0
        for project in self._all_projects:
            pid  = project["id"]
            card = self._cards.get(pid)
            if not card:
                continue
            match = (
                not text or
                text in project.get("name", "").lower() or
                text in (project.get("description") or "").lower()
            )
            card.setVisible(match)
            if match:
                visible += 1

        self._empty_lbl.setVisible(visible == 0)

    # ── Действия ─────────────────────────────────────────────

    def _on_open_edit(self, project_id: int):
        success, who = self._ctx.auth.acquire_project_lock(project_id)
        if success:
            self._ctx.start_session(project_id, is_editing=True)
            self.project_selected.emit(project_id, True)
        else:
            QMessageBox.warning(
                self,
                "Проект заблокирован",
                tr("projects.locked_msg", user=who)
            )

    def _on_open_view(self, project_id: int):
        self._ctx.start_session(project_id, is_editing=False)
        self.project_selected.emit(project_id, False)

    def _on_import_mdb(self):
        dlg = ProjectImportDialog(self._ctx, self)
        if dlg.exec():
            self._load_projects()

    def _on_new_project(self):
        dlg = ProjectNewDialog(self._ctx, self)
        if dlg.exec():
            self._load_projects()

    # ── Перевод ──────────────────────────────────────────────

    def _retranslate(self, lang=None):
        self._title_lbl.setText(tr("projects.title"))
        self._search.setPlaceholderText(tr("projects.search"))
        self._btn_import.setText("⬆  " + tr("projects.import_mdb"))
        self._empty_lbl.setText(tr("projects.empty"))
        self._load_projects()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_projects()

    def _on_delete_project(self):
        pid = getattr(self, '_selected_project_id', None)
        if pid is None:
            QMessageBox.information(
                self, "Удаление",
                "Сначала кликните на карточку проекта, затем нажмите 'Удалить'."
            )
            return
    
        project = self._ctx.db.fetchone(
            "SELECT name FROM projects WHERE id=?", (pid,)
        )
        name = project["name"] if project else f"#{pid}"
    
        reply = QMessageBox.question(
            self, "Удалить проект",
            f"Удалить проект «{name}»?\n\nВсе данные будут удалены безвозвратно.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
    
        tables = [
            "tbWayData", "tbWayInfo", "tbStationWay", "tbStationWayData",
            "tbStation", "tbCurve", "tbLeftCurve", "tbRightCurve",
            "tbDeviceLocation", "tbStationDeviceLocation",
            "tbLeftIsolatedJoint", "tbRightIsolatedJoint",
            "tbStraighteningData", "tbStraighteningPlace",
            "tbLeftPleti", "tbRightPleti", "tbLeftVstavki", "tbRightVstavki",
            "tbAccessWayInfo", "tbAccessWayData", "tbAccessWayCurve", "tbAccessWayDevice",
            "project_access", "project_locks", "audit_log", "sync_queue"
        ]
        for table in tables:
            try:
                self._ctx.db.execute(
                    f"DELETE FROM {table} WHERE project_id=?", (pid,)
                )
            except Exception:
                pass
    
        self._ctx.db.execute("DELETE FROM projects WHERE id=?", (pid,))
        self._ctx.db.commit()
        self._selected_project_id = None
        self._load_projects()

    def _on_card_selected(self, project_id: int):
       """Выделить карточку."""
       self._selected_project_id = project_id
       for pid, card in self._cards.items():
            is_selected = pid == project_id
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {"#1E1E1E" if is_selected else Colors.BG_SURFACE};
                    border: 1px solid {"#FF6B00" if is_selected else Colors.BORDER};
                    border-radius: 6px;
                }}
            """)

    def _card_context_menu(self, pos, project_id: int):
        from PySide6.QtWidgets import QMenu
        self._on_card_selected(project_id)
        menu = QMenu(self)
        act_edit = menu.addAction("✏  Открыть (редактирование)")
        act_view = menu.addAction("👁  Открыть (просмотр)")
        menu.addSeparator()
        act_del  = menu.addAction("🗑  Удалить проект")
        act_del.setIcon(self.style().standardIcon(
            __import__("PySide6.QtWidgets", fromlist=["QStyle"]).QStyle.StandardPixmap.SP_TrashIcon
        ))
    
        action = menu.exec(self._cards[project_id].mapToGlobal(pos))
        if action == act_edit:
            self._on_open_edit(project_id)
        elif action == act_view:
            self._on_open_view(project_id)
        elif action == act_del:
            self._on_delete_project()