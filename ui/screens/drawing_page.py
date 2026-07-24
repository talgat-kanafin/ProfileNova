"""
ui/screens/drawing_page.py
===========================
Раздел "Чертёж".

Вкладка 1: Чертёж — генерация в AutoCAD
Вкладка 2: Захват — получение данных из AutoCAD в БД
"""

import os, sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QPushButton, QComboBox, QFrame,
    QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox,
    QListWidget, QMessageBox, QProgressBar,
    QRadioButton, QButtonGroup, QLineEdit,
    QSplitter, QTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import Colors, Typography, Spacing, Sizes
from modules.autocad.drawing   import DRAWING_TYPES, DrawingGenerator
from modules.autocad.capture   import CAPTURE_PROPERTIES, auto_capture, manual_capture
from modules.autocad.connector import (
    is_autocad_running, get_autocad_version,
    get_all_layers, get_layer_object_count, reset_cache
)


class DrawingThread(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, generator, drawing_type, way_id,
                 side, v_radius, split_pages, station_id):
        super().__init__()
        self._gen          = generator
        self._drawing_type = drawing_type
        self._way_id       = way_id
        self._side         = side
        self._v_radius     = v_radius
        self._split_pages  = split_pages
        self._station_id   = station_id

    def run(self):
        self._gen._progress = lambda msg: self.progress.emit(msg)
        ok = self._gen.generate(
            self._drawing_type, self._way_id,
            side=self._side,
            vertical_radius=self._v_radius,
            split_pages=self._split_pages,
            station_id=self._station_id
        )
        self.finished.emit(ok, "" if ok else "Ошибка генерации")


class CaptureThread(QThread):
    finished = Signal(list, str)  # values, error

    def __init__(self, mode, layer, prop):
        super().__init__()
        self._mode  = mode   # "auto" | "manual"
        self._layer = layer
        self._prop  = prop

    def run(self):
        try:
            if self._mode == "auto":
                values = auto_capture(self._layer, self._prop)
            else:
                values = manual_capture(self._prop)
            self.finished.emit(values, "")
        except InterruptedError:
            self.finished.emit([], "cancelled")
        except Exception as e:
            self.finished.emit([], str(e))


class DrawingPage(QWidget):

    def __init__(self, ctx, project_id: int, is_editing: bool, parent=None):
        super().__init__(parent)
        self._ctx        = ctx
        self._project_id = project_id
        self._is_editing = is_editing
        self._draw_thread    = None
        self._capture_thread = None

        self._build_ui()
        self._load_ways()
        self._check_autocad()

    # ── UI ───────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Статус AutoCAD
        self._status_bar = QFrame()
        self._status_bar.setFixedHeight(36)
        self._status_bar.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border-bottom: 1px solid {Colors.BORDER};
        """)
        sb_layout = QHBoxLayout(self._status_bar)
        sb_layout.setContentsMargins(Spacing.LG, 0, Spacing.LG, 0)

        self._autocad_status = QLabel("⚪ Проверка AutoCAD...")
        self._autocad_status.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        sb_layout.addWidget(self._autocad_status)
        sb_layout.addStretch()

        btn_reconnect = QPushButton("🔄 Переподключить")
        btn_reconnect.setFixedHeight(26)
        btn_reconnect.clicked.connect(self._reconnect_autocad)
        sb_layout.addWidget(btn_reconnect)

        root.addWidget(self._status_bar)

        # Вкладки
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background-color: {Colors.BG_BASE}; }}
            QTabBar::tab {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.TEXT_SECONDARY};
                padding: 10px 24px; border: none;
                border-bottom: 2px solid transparent; font-size: 13px;
            }}
            QTabBar::tab:selected {{
                color: {Colors.TEXT_PRIMARY};
                border-bottom: 2px solid {Colors.ACCENT};
            }}
            QTabBar::tab:hover {{
                color: {Colors.TEXT_PRIMARY};
                background-color: {Colors.BG_ELEVATED};
            }}
        """)

        self._tabs.addTab(self._build_drawing_tab(), "Чертёж")
        self._tabs.addTab(self._build_capture_tab(), "Захват данных")

        root.addWidget(self._tabs, 1)

    # ── Вкладка Чертёж ───────────────────────────────────────

    def _build_drawing_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background-color: {Colors.BG_BASE};")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.XL)

        # Левая панель — параметры
        left = QFrame()
        left.setFixedWidth(340)
        left.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
        """)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        left_layout.setSpacing(Spacing.MD)

        # Тип чертежа
        left_layout.addWidget(self._section_label("Тип чертежа"))
        self._drawing_list = QListWidget()
        self._drawing_list.setFixedHeight(200)
        self._drawing_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {Colors.BG_BASE};
                border: 1px solid {Colors.BORDER};
                color: {Colors.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QListWidget::item {{ padding: 7px 10px; }}
            QListWidget::item:selected {{
                background-color: {Colors.ACCENT_DIM};
                color: {Colors.TEXT_PRIMARY};
                border-left: 3px solid {Colors.ACCENT};
            }}
            QListWidget::item:hover {{ background-color: {Colors.BG_ELEVATED}; }}
        """)
        for key, label in DRAWING_TYPES:
            self._drawing_list.addItem(label)
        self._drawing_list.setCurrentRow(0)
        self._drawing_list.currentRowChanged.connect(self._on_drawing_type_changed)
        left_layout.addWidget(self._drawing_list)

        left_layout.addWidget(self._divider())

        # Выбор пути
        left_layout.addWidget(self._section_label("Путь"))
        self._way_combo = QComboBox()
        self._way_combo.setFixedHeight(32)
        left_layout.addWidget(self._way_combo)

        # Сторона (Левый / Правый)
        self._side_group = QWidget()
        side_layout = QHBoxLayout(self._side_group)
        side_layout.setContentsMargins(0, 0, 0, 0)
        self._rb_left  = QRadioButton("Левый")
        self._rb_right = QRadioButton("Правый / Однопутный")
        self._rb_left.setChecked(True)
        self._rb_left.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self._rb_right.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        side_layout.addWidget(self._rb_left)
        side_layout.addWidget(self._rb_right)
        left_layout.addWidget(self._side_group)

        # Станция (для станционных типов)
        self._station_widget = QWidget()
        st_layout = QVBoxLayout(self._station_widget)
        st_layout.setContentsMargins(0, 0, 0, 0)
        st_layout.addWidget(self._section_label("Станция"))
        self._station_combo = QComboBox()
        self._station_combo.setFixedHeight(32)
        st_layout.addWidget(self._station_combo)
        self._station_widget.setVisible(False)
        left_layout.addWidget(self._station_widget)

        left_layout.addWidget(self._divider())

        # Радиус вертикальной кривой
        left_layout.addWidget(self._section_label("Радиус вертикальной кривой"))
        self._v_radius = QDoubleSpinBox()
        self._v_radius.setRange(0, 99999)
        self._v_radius.setValue(0)
        self._v_radius.setFixedHeight(32)
        self._v_radius.setSpecialValueText("Не задан")
        left_layout.addWidget(self._v_radius)

        # Разбить на страницы
        self._split_pages_cb = QCheckBox("Разбить на страницы для печати")
        self._split_pages_cb.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        left_layout.addWidget(self._split_pages_cb)

        left_layout.addStretch()

        # Кнопка генерации
        self._btn_generate = QPushButton("▶  Создать чертёж в AutoCAD")
        self._btn_generate.setFixedHeight(Sizes.BTN_HEIGHT_LG)
        self._btn_generate.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white; border: none; border-radius: 4px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {Colors.ACCENT_HOVER}; }}
            QPushButton:disabled {{
                background-color: {Colors.BG_OVERLAY};
                color: {Colors.TEXT_DISABLED};
            }}
        """)
        self._btn_generate.clicked.connect(self._start_drawing)
        left_layout.addWidget(self._btn_generate)

        layout.addWidget(left)

        # Правая панель — лог и прогресс
        right = QFrame()
        right.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
        """)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)

        right_layout.addWidget(self._section_label("Статус генерации"))

        self._draw_progress = QProgressBar()
        self._draw_progress.setRange(0, 0)  # indeterminate
        self._draw_progress.setFixedHeight(4)
        self._draw_progress.setVisible(False)
        self._draw_progress.setStyleSheet(f"""
            QProgressBar {{ background-color: {Colors.BG_BASE}; border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background-color: {Colors.ACCENT}; border-radius: 2px; }}
        """)
        right_layout.addWidget(self._draw_progress)

        self._draw_log = QTextEdit()
        self._draw_log.setReadOnly(True)
        self._draw_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BG_BASE};
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                font-family: Consolas, monospace;
                font-size: 12px;
            }}
        """)
        right_layout.addWidget(self._draw_log, 1)

        layout.addWidget(right, 1)
        return w

    # ── Вкладка Захват данных ─────────────────────────────────

    def _build_capture_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background-color: {Colors.BG_BASE};")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.XL)

        # Левая панель — настройки захвата
        left = QFrame()
        left.setFixedWidth(340)
        left.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
        """)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        left_layout.setSpacing(Spacing.MD)

        # Режим захвата
        left_layout.addWidget(self._section_label("Режим захвата"))
        self._rb_auto   = QRadioButton("Авто — все объекты слоя")
        self._rb_manual = QRadioButton("Ручной — выделить в AutoCAD")
        self._rb_auto.setChecked(True)
        for rb in (self._rb_auto, self._rb_manual):
            rb.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self._rb_auto.toggled.connect(self._on_capture_mode_changed)
        left_layout.addWidget(self._rb_auto)
        left_layout.addWidget(self._rb_manual)

        # Слой (только для авто)
        self._layer_widget = QWidget()
        lw_layout = QVBoxLayout(self._layer_widget)
        lw_layout.setContentsMargins(0, 0, 0, 0)
        lw_layout.addWidget(self._section_label("Слой AutoCAD"))
        layer_row = QHBoxLayout()
        self._layer_combo = QComboBox()
        self._layer_combo.setFixedHeight(32)
        layer_row.addWidget(self._layer_combo)
        btn_refresh_layers = QPushButton("🔄")
        btn_refresh_layers.setFixedSize(32, 32)
        btn_refresh_layers.clicked.connect(self._refresh_layers)
        layer_row.addWidget(btn_refresh_layers)
        lw_layout.addLayout(layer_row)
        self._layer_widget.setVisible(True)
        left_layout.addWidget(self._layer_widget)

        left_layout.addWidget(self._divider())

        # Свойство для захвата
        left_layout.addWidget(self._section_label("Свойство"))
        self._prop_combo = QComboBox()
        self._prop_combo.setFixedHeight(32)
        for key, label in CAPTURE_PROPERTIES.items():
            self._prop_combo.addItem(label, key)
        left_layout.addWidget(self._prop_combo)

        left_layout.addWidget(self._divider())

        # Куда записать
        left_layout.addWidget(self._section_label("Записать в таблицу"))
        self._target_table = QComboBox()
        self._target_table.setFixedHeight(32)
        for t, label in [
            ("tbWayData",          "Данные профиля (tbWayData)"),
            ("tbStationWayData",   "Станция (tbStationWayData)"),
            ("tbAccessWayData",    "Подъездной путь (tbAccessWayData)"),
            ("tbStraighteningData","Рихтовка (tbStraighteningData)"),
        ]:
            self._target_table.addItem(label, t)
        left_layout.addWidget(self._target_table)

        left_layout.addWidget(self._section_label("Колонка назначения"))
        self._target_col = QComboBox()
        self._target_col.setFixedHeight(32)
        self._target_table.currentIndexChanged.connect(self._refresh_target_columns)
        left_layout.addWidget(self._target_col)

        left_layout.addWidget(self._section_label("Путь (WayId)"))
        self._capture_way = QComboBox()
        self._capture_way.setFixedHeight(32)
        left_layout.addWidget(self._capture_way)

        left_layout.addStretch()

        self._btn_capture = QPushButton("⚡  Начать захват")
        self._btn_capture.setFixedHeight(Sizes.BTN_HEIGHT_LG)
        self._btn_capture.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white; border: none; border-radius: 4px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {Colors.ACCENT_HOVER}; }}
            QPushButton:disabled {{
                background-color: {Colors.BG_OVERLAY};
                color: {Colors.TEXT_DISABLED};
            }}
        """)
        self._btn_capture.clicked.connect(self._start_capture)
        left_layout.addWidget(self._btn_capture)

        layout.addWidget(left)

        # Правая панель — предпросмотр захваченных данных
        right = QFrame()
        right.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
        """)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)

        right_layout.addWidget(self._section_label("Захваченные данные"))

        self._capture_log = QTextEdit()
        self._capture_log.setReadOnly(True)
        self._capture_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BG_BASE};
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                font-family: Consolas, monospace;
                font-size: 12px;
            }}
        """)
        right_layout.addWidget(self._capture_log, 1)

        # Кнопка записи в БД
        self._btn_write_db = QPushButton("💾  Записать в БД")
        self._btn_write_db.setFixedHeight(Sizes.BTN_HEIGHT)
        self._btn_write_db.setEnabled(False)
        self._btn_write_db.clicked.connect(self._write_to_db)
        right_layout.addWidget(self._btn_write_db)

        self._captured_values = []

        layout.addWidget(right, 1)
        return w

    # ── Загрузка данных ──────────────────────────────────────

    def _load_ways(self):
        rows = self._ctx.db.fetchall(
            "SELECT WayId, Name FROM tbWayInfo WHERE project_id=? ORDER BY WayId",
            (self._project_id,)
        )
        for combo in (self._way_combo, self._capture_way):
            combo.clear()
            for r in rows:
                name = r.get("Name") or f"Путь {r['WayId']}"
                combo.addItem(name, r["WayId"])

        stations = self._ctx.db.fetchall(
            "SELECT StationId, Name FROM tbStation WHERE project_id=? ORDER BY StationId",
            (self._project_id,)
        )
        self._station_combo.clear()
        for s in stations:
            self._station_combo.addItem(
                s.get("Name") or f"Станция {s['StationId']}",
                s["StationId"]
            )

        self._refresh_target_columns()
        self._refresh_layers()

    def _refresh_layers(self):
        layers = get_all_layers()
        self._layer_combo.clear()
        if not layers:
            self._layer_combo.addItem("AutoCAD не подключён")
            return
        for ln in layers:
            stats = get_layer_object_count(ln)
            if stats["всего"] > 0:
                parts = []
                if stats["точки"]: parts.append(f"точек:{stats['точки']}")
                if stats["блоки"]: parts.append(f"блоков:{stats['блоки']}")
                if stats["текст"]: parts.append(f"текста:{stats['текст']}")
                label = f"{ln} ({', '.join(parts)})" if parts else ln
                self._layer_combo.addItem(label, ln)

    def _refresh_target_columns(self):
        table = self._target_table.currentData()
        col_map = {
            "tbWayData": [
                ("Left_Rail",    "Рельс Л"),
                ("Right_Rail",   "Рельс П"),
                ("Ground",       "Земля"),
                ("Left_Ballast", "Балласт Л"),
                ("Right_Ballast","Балласт П"),
                ("Left_SUklon",  "Уклон Л"),
                ("Right_SUklon", "Уклон П"),
                ("TrackSpacing", "Межпутье"),
                ("GroundEdge",   "Бровка"),
            ],
            "tbStationWayData": [
                ("Rail",    "Рельс"),
                ("Ballast", "Балласт"),
                ("SUklon",  "Уклон"),
            ],
            "tbAccessWayData": [
                ("Rail",      "Рельс"),
                ("Ground",    "Земля"),
                ("SUklon",    "Уклон"),
                ("GroundEdge","Бровка"),
            ],
            "tbStraighteningData": [
                ("Left_Straightening",  "Рихтовка Л"),
                ("Right_Straightening", "Рихтовка П"),
                ("CurrentTrackSpacing", "Межпутье"),
            ],
        }
        self._target_col.clear()
        for col, label in col_map.get(table, []):
            self._target_col.addItem(label, col)

    # ── AutoCAD статус ───────────────────────────────────────

    def _check_autocad(self):
        if is_autocad_running():
            ver = get_autocad_version()
            self._autocad_status.setText(
                f"🟢 AutoCAD подключён  |  Версия: {ver}"
            )
            self._autocad_status.setStyleSheet(
                f"color: {Colors.SUCCESS}; font-size: 12px;"
            )
        else:
            self._autocad_status.setText(
                "🔴 AutoCAD не запущен  |  Запустите AutoCAD и нажмите 'Переподключить'"
            )
            self._autocad_status.setStyleSheet(
                f"color: {Colors.ERROR}; font-size: 12px;"
            )

    def _reconnect_autocad(self):
        reset_cache()
        self._check_autocad()
        self._refresh_layers()

    # ── Генерация чертежа ────────────────────────────────────

    def _on_drawing_type_changed(self, idx: int):
        key = DRAWING_TYPES[idx][0] if idx >= 0 else ""
        is_station = key in ("station_1000", "station_200", "station_compact")
        self._station_widget.setVisible(is_station)
        self._side_group.setVisible(not is_station)

    def _start_drawing(self):
        if not is_autocad_running():
            QMessageBox.warning(self, "AutoCAD",
                "AutoCAD не запущен.\nЗапустите AutoCAD и нажмите 'Переподключить'.")
            return

        idx          = self._drawing_list.currentRow()
        drawing_type = DRAWING_TYPES[idx][0]
        way_id       = self._way_combo.currentData()
        station_id   = self._station_combo.currentData()
        side         = "left" if self._rb_left.isChecked() else "right"
        v_radius     = self._v_radius.value()
        split_pages  = self._split_pages_cb.isChecked()

        if way_id is None and station_id is None:
            QMessageBox.warning(self, "Нет данных", "Выберите путь или станцию.")
            return

        self._btn_generate.setEnabled(False)
        self._draw_progress.setVisible(True)
        self._draw_log.clear()
        self._log_draw(f"▶ Генерация: {DRAWING_TYPES[idx][1]}")

        gen = DrawingGenerator(self._ctx.db, self._project_id)

        self._draw_thread = DrawingThread(
            gen, drawing_type, way_id,
            side, v_radius, split_pages, station_id
        )
        self._draw_thread.progress.connect(self._log_draw)
        self._draw_thread.finished.connect(self._on_drawing_done)
        self._draw_thread.start()

    def _log_draw(self, msg: str):
        self._draw_log.append(msg)

    def _on_drawing_done(self, ok: bool, error: str):
        self._btn_generate.setEnabled(True)
        self._draw_progress.setVisible(False)
        if ok:
            self._log_draw("✓ Чертёж построен успешно")
        else:
            self._log_draw(f"✗ Ошибка: {error}")

    # ── Захват данных ────────────────────────────────────────

    def _on_capture_mode_changed(self):
        is_auto = self._rb_auto.isChecked()
        self._layer_widget.setVisible(is_auto)

    def _start_capture(self):
        if not is_autocad_running():
            QMessageBox.warning(self, "AutoCAD",
                "AutoCAD не запущен.")
            return

        mode  = "auto" if self._rb_auto.isChecked() else "manual"
        layer = self._layer_combo.currentData() or self._layer_combo.currentText()
        prop  = self._prop_combo.currentData()

        if mode == "manual":
            QMessageBox.information(
                self, "Ручной захват",
                "Переключитесь в AutoCAD и выделите объекты рамкой.\n"
                "После выделения нажмите Enter или Пробел."
            )

        self._btn_capture.setEnabled(False)
        self._capture_log.clear()
        self._capture_log.append(f"▶ Захват: режим={mode}, свойство={prop}")

        self._capture_thread = CaptureThread(mode, layer, prop)
        self._capture_thread.finished.connect(self._on_capture_done)
        self._capture_thread.start()

    def _on_capture_done(self, values: list, error: str):
        self._btn_capture.setEnabled(True)

        if error == "cancelled":
            self._capture_log.append("⚠ Захват отменён")
            return
        if error:
            self._capture_log.append(f"✗ Ошибка: {error}")
            return

        self._captured_values = values
        self._capture_log.append(f"✓ Захвачено: {len(values)} значений\n")

        # Показать первые 20
        for i, v in enumerate(values[:20]):
            self._capture_log.append(f"  [{i+1}] {v}")
        if len(values) > 20:
            self._capture_log.append(f"  ... ещё {len(values)-20}")

        self._btn_write_db.setEnabled(len(values) > 0)

    def _write_to_db(self):
        if not self._captured_values:
            return

        table  = self._target_table.currentData()
        col    = self._target_col.currentData()
        way_id = self._capture_way.currentData()

        if not table or not col or not way_id:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу, колонку и путь.")
            return

        reply = QMessageBox.question(
            self, "Подтвердить запись",
            f"Записать {len(self._captured_values)} значений\n"
            f"→ {table}.{col} (WayId={way_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        from modules.autocad.capture import capture_to_table_column
        updated = capture_to_table_column(
            self._captured_values,
            self._ctx.db,
            self._project_id,
            table, col, way_id
        )

        self._capture_log.append(f"\n✓ Записано в БД: {updated} строк")
        self._btn_write_db.setEnabled(False)
        self._captured_values = []

    # ── Утилиты ──────────────────────────────────────────────

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;"
        )
        return lbl

    @staticmethod
    def _divider() -> QFrame:
        d = QFrame()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background-color: {Colors.BORDER};")
        return d