"""
ui/screens/project_import_dialog.py
=====================================
Диалог импорта .mdb файла в новый проект.
"""

import os
import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QProgressBar,
    QFileDialog, QFrame, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import Colors, Spacing, Sizes, Typography
from ui.i18n  import tr


class ImportThread(QThread):
    progress = Signal(str, int, int)   # table, current, total
    finished = Signal(dict)            # {table: count}
    error    = Signal(str)

    def __init__(self, ctx, mdb_path: str, project_id: int):
        super().__init__()
        self._ctx        = ctx
        self._mdb_path   = mdb_path
        self._project_id = project_id

    def run(self):
        try:
            from core.db.importer import MDBImporter
            importer = MDBImporter(self._ctx.db)
            results  = importer.import_from_mdb(
                self._mdb_path,
                self._project_id,
                on_progress=lambda t, c, total: self.progress.emit(t, c, total)
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class ProjectImportDialog(QDialog):

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self._ctx        = ctx
        self._mdb_path   = ""
        self._project_id = None
        self._thread     = None

        self.setWindowTitle(tr("import.title"))
        self.setFixedSize(520, 400)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        # Заголовок
        title = QLabel(tr("import.title"))
        title.setFont(Typography.get_font(15, bold=True))
        layout.addWidget(title)

        layout.addWidget(self._divider())

        # Выбор файла
        layout.addWidget(self._lbl("Файл базы данных (.mdb) *"))
        file_row = QHBoxLayout()
        self._file_input = QLineEdit()
        self._file_input.setReadOnly(True)
        self._file_input.setFixedHeight(Sizes.INPUT_HEIGHT)
        self._file_input.setPlaceholderText("Выберите файл .mdb...")
        file_row.addWidget(self._file_input)

        btn_browse = QPushButton("Обзор")
        btn_browse.setFixedHeight(Sizes.INPUT_HEIGHT)
        btn_browse.setFixedWidth(80)
        btn_browse.clicked.connect(self._browse_file)
        file_row.addWidget(btn_browse)
        layout.addLayout(file_row)

        # Название проекта
        layout.addWidget(self._lbl(tr("import.project_name") + " *"))
        self._name_input = QLineEdit()
        self._name_input.setFixedHeight(Sizes.INPUT_HEIGHT)
        self._name_input.setPlaceholderText("Например: Алматы — Шымкент 2024")
        layout.addWidget(self._name_input)

        # Описание
        layout.addWidget(self._lbl(tr("import.description")))
        self._desc_input = QLineEdit()
        self._desc_input.setFixedHeight(Sizes.INPUT_HEIGHT)
        layout.addWidget(self._desc_input)

        # Прогресс (скрыт до начала)
        self._progress_lbl = QLabel("")
        self._progress_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        self._progress_lbl.setVisible(False)
        layout.addWidget(self._progress_lbl)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        # Ошибка
        self._error_lbl = QLabel("")
        self._error_lbl.setStyleSheet(f"color: {Colors.ERROR}; font-size: 12px;")
        self._error_lbl.setVisible(False)
        layout.addWidget(self._error_lbl)

        layout.addStretch()
        layout.addWidget(self._divider())

        # Кнопки
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton(tr("btn.cancel"))
        btn_cancel.setFixedHeight(Sizes.BTN_HEIGHT)
        btn_cancel.setFixedWidth(100)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        self._btn_import = QPushButton(tr("btn.import"))
        self._btn_import.setFixedHeight(Sizes.BTN_HEIGHT)
        self._btn_import.setFixedWidth(140)
        self._btn_import.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white; border: none; border-radius: 4px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {Colors.ACCENT_HOVER}; }}
            QPushButton:disabled {{ background-color: {Colors.BG_OVERLAY}; color: {Colors.TEXT_DISABLED}; }}
        """)
        self._btn_import.clicked.connect(self._start_import)
        btn_row.addWidget(self._btn_import)
        layout.addLayout(btn_row)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать файл базы данных", "",
            "Access Database (*.mdb);;Все файлы (*)"
        )
        if path:
            self._mdb_path = path
            self._file_input.setText(path)
            # Авто-заполнить название из имени файла
            if not self._name_input.text():
                name = os.path.splitext(os.path.basename(path))[0]
                self._name_input.setText(name)

    def _start_import(self):
        self._error_lbl.setVisible(False)

        if not self._mdb_path:
            self._show_error("Выберите файл .mdb")
            return
        if not self._name_input.text().strip():
            self._show_error(tr("error.required_field") + ": " + tr("import.project_name"))
            return

        # Создать проект
        user_id = self._ctx.auth.current_user["id"]
        self._ctx.db.execute(
            "INSERT INTO projects (name, description, mdb_origin, created_by) VALUES (?,?,?,?)",
            (
                self._name_input.text().strip(),
                self._desc_input.text().strip() or None,
                self._mdb_path,
                user_id
            )
        )
        self._ctx.db.commit()

        row = self._ctx.db.fetchone(
            "SELECT id FROM projects ORDER BY id DESC LIMIT 1"
        )
        self._project_id = row["id"]

        # Выдать доступ создателю
        self._ctx.db.execute(
            "INSERT OR REPLACE INTO project_access (project_id, user_id, can_edit) VALUES (?,?,1)",
            (self._project_id, user_id)
        )
        self._ctx.db.commit()

        # Запустить импорт
        self._btn_import.setEnabled(False)
        self._progress_lbl.setVisible(True)
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 25)

        self._thread = ImportThread(self._ctx, self._mdb_path, self._project_id)
        self._thread.progress.connect(self._on_progress)
        self._thread.finished.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_progress(self, table: str, current: int, total: int):
        self._progress_bar.setValue(current)
        self._progress_lbl.setText(tr("import.progress", table=table))

    def _on_finished(self, results: dict):
        total = sum(results.values())
        self._progress_bar.setValue(self._progress_bar.maximum())
        self._progress_lbl.setText(tr("import.done", count=total))
        self._btn_import.setEnabled(True)
        self._btn_import.setText("✓ Готово — Закрыть")
        self._btn_import.clicked.disconnect()
        self._btn_import.clicked.connect(self.accept)

    def _on_error(self, error: str):
        self._show_error(tr("import.error", error=error))
        self._btn_import.setEnabled(True)
        self._progress_lbl.setVisible(False)
        self._progress_bar.setVisible(False)

    def _show_error(self, msg: str):
        self._error_lbl.setText(msg)
        self._error_lbl.setVisible(True)

    @staticmethod
    def _lbl(text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        return l

    @staticmethod
    def _divider() -> QFrame:
        d = QFrame()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background-color: {Colors.BORDER};")
        return d