"""
ui/screens/project_new_dialog.py
=================================
Диалог создания нового пустого проекта.
Только для admin.
"""

import os, sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QCheckBox,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import Colors, Spacing, Sizes, Typography
from ui.i18n  import tr


class ProjectNewDialog(QDialog):

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self._ctx = ctx
        self.setWindowTitle(tr("projects.new"))
        self.setFixedSize(480, 460)
        self.setModal(True)
        self._build_ui()
        self._load_users()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        title = QLabel(tr("projects.new"))
        title.setFont(Typography.get_font(15, bold=True))
        layout.addWidget(title)
        layout.addWidget(self._divider())

        layout.addWidget(self._lbl(tr("import.project_name") + " *"))
        self._name = QLineEdit()
        self._name.setFixedHeight(Sizes.INPUT_HEIGHT)
        layout.addWidget(self._name)

        layout.addWidget(self._lbl(tr("import.description")))
        self._desc = QLineEdit()
        self._desc.setFixedHeight(Sizes.INPUT_HEIGHT)
        layout.addWidget(self._desc)

        layout.addWidget(self._divider())

        # Выдать доступ пользователям
        layout.addWidget(self._lbl("Доступ (выберите пользователей):"))
        self._users_list = QListWidget()
        self._users_list.setFixedHeight(140)
        self._users_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self._users_list)

        self._can_edit_cb = QCheckBox("Разрешить редактирование выбранным")
        self._can_edit_cb.setChecked(True)
        layout.addWidget(self._can_edit_cb)

        # Ошибка
        self._error_lbl = QLabel("")
        self._error_lbl.setStyleSheet(f"color: {Colors.ERROR}; font-size: 12px;")
        self._error_lbl.setVisible(False)
        layout.addWidget(self._error_lbl)

        layout.addStretch()
        layout.addWidget(self._divider())

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton(tr("btn.cancel"))
        btn_cancel.setFixedHeight(Sizes.BTN_HEIGHT)
        btn_cancel.setFixedWidth(100)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_create = QPushButton(tr("btn.add"))
        btn_create.setFixedHeight(Sizes.BTN_HEIGHT)
        btn_create.setFixedWidth(120)
        btn_create.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT}; color: white;
                border: none; border-radius: 4px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {Colors.ACCENT_HOVER}; }}
        """)
        btn_create.clicked.connect(self._create)
        btn_row.addWidget(btn_create)
        layout.addLayout(btn_row)

    def _load_users(self):
        users = self._ctx.db.fetchall(
            "SELECT id, full_name, department FROM users WHERE is_active=1 ORDER BY full_name"
        )
        for u in users:
            dept = f" ({u['department']})" if u.get("department") else ""
            item = QListWidgetItem(f"{u['full_name']}{dept}")
            item.setData(Qt.ItemDataRole.UserRole, u["id"])
            self._users_list.addItem(item)

    def _create(self):
        name = self._name.text().strip()
        if not name:
            self._error_lbl.setText(tr("error.required_field"))
            self._error_lbl.setVisible(True)
            return

        user_id = self._ctx.auth.current_user["id"]
        self._ctx.db.execute(
            "INSERT INTO projects (name, description, created_by) VALUES (?,?,?)",
            (name, self._desc.text().strip() or None, user_id)
        )
        self._ctx.db.commit()

        row = self._ctx.db.fetchone("SELECT id FROM projects ORDER BY id DESC LIMIT 1")
        project_id = row["id"]

        # Доступ создателю
        self._ctx.db.execute(
            "INSERT OR REPLACE INTO project_access (project_id, user_id, can_edit) VALUES (?,?,1)",
            (project_id, user_id)
        )

        # Доступ выбранным пользователям
        can_edit = 1 if self._can_edit_cb.isChecked() else 0
        for item in self._users_list.selectedItems():
            uid = item.data(Qt.ItemDataRole.UserRole)
            if uid != user_id:
                self._ctx.db.execute(
                    "INSERT OR REPLACE INTO project_access (project_id, user_id, can_edit) VALUES (?,?,?)",
                    (project_id, uid, can_edit)
                )

        self._ctx.db.commit()
        self.accept()

    @staticmethod
    def _lbl(text):
        l = QLabel(text)
        l.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        return l

    @staticmethod
    def _divider():
        d = QFrame()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background-color: {Colors.BORDER};")
        return d