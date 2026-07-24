"""
ui/screens/calc_page.py
========================
Раздел "Вычисления".

Вкладка 1: Калькулятор кривой
  — ввод параметров кривой → расчёт всех элементов
  — справочник ординат (tbOrdinate) и тангенсов (tbTangent)

Вкладка 2: Таблицы справочников
  — просмотр tbOrdinate и tbTangent
"""

import os, sys, math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QFrame, QDoubleSpinBox, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QGridLayout, QLineEdit,
    QSplitter, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import Colors, Typography, Spacing, Sizes


class CalcPage(QWidget):

    def __init__(self, ctx, project_id: int, parent=None):
        super().__init__(parent)
        self._ctx        = ctx
        self._project_id = project_id
        self._build_ui()
        self._load_reference_tables()

    # ── UI ───────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

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

        self._tabs.addTab(self._build_curve_calc_tab(), "Калькулятор кривой")
        self._tabs.addTab(self._build_reference_tab(),  "Справочники")

        root.addWidget(self._tabs)

    # ── Вкладка: Калькулятор кривой ──────────────────────────

    def _build_curve_calc_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background-color: {Colors.BG_BASE};")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.XL)

        # Левая панель — ввод
        input_frame = QFrame()
        input_frame.setFixedWidth(320)
        input_frame.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
        """)
        in_layout = QVBoxLayout(input_frame)
        in_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        in_layout.setSpacing(Spacing.MD)

        in_layout.addWidget(self._section_label("Исходные данные"))
        in_layout.addWidget(self._divider())

        grid = QGridLayout()
        grid.setSpacing(Spacing.SM)

        # Угол поворота
        grid.addWidget(self._field_label("Угол поворота (°)"), 0, 0)
        self._angle_deg = QSpinBox()
        self._angle_deg.setRange(0, 179)
        self._angle_deg.setValue(0)
        self._angle_deg.setFixedHeight(32)
        grid.addWidget(self._angle_deg, 0, 1)

        grid.addWidget(self._field_label("Минуты (')"), 1, 0)
        self._angle_min = QDoubleSpinBox()
        self._angle_min.setRange(0, 59.9)
        self._angle_min.setDecimals(1)
        self._angle_min.setValue(0)
        self._angle_min.setFixedHeight(32)
        grid.addWidget(self._angle_min, 1, 1)

        # Радиус
        grid.addWidget(self._field_label("Радиус (м)"), 2, 0)
        self._radius = QSpinBox()
        self._radius.setRange(1, 99999)
        self._radius.setValue(500)
        self._radius.setSingleStep(50)
        self._radius.setFixedHeight(32)
        grid.addWidget(self._radius, 2, 1)

        in_layout.addLayout(grid)
        in_layout.addWidget(self._divider())

        # Кнопка расчёта
        btn_calc = QPushButton("▶  Рассчитать")
        btn_calc.setFixedHeight(Sizes.BTN_HEIGHT_LG)
        btn_calc.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white; border: none; border-radius: 4px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {Colors.ACCENT_HOVER}; }}
        """)
        btn_calc.clicked.connect(self._calculate_curve)
        in_layout.addWidget(btn_calc)

        in_layout.addWidget(self._divider())

        # Подсказка
        hint = QLabel(
            "Расчёт элементов круговой кривой:\n"
            "тангенс, длина, биссектриса,\n"
            "домер, ординаты по таблице."
        )
        hint.setStyleSheet(
            f"color: {Colors.TEXT_DISABLED}; font-size: 11px;"
        )
        hint.setWordWrap(True)
        in_layout.addWidget(hint)
        in_layout.addStretch()

        layout.addWidget(input_frame)

        # Правая панель — результаты
        result_frame = QFrame()
        result_frame.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
        """)
        res_layout = QVBoxLayout(result_frame)
        res_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        res_layout.setSpacing(Spacing.MD)

        res_layout.addWidget(self._section_label("Результаты расчёта"))
        res_layout.addWidget(self._divider())

        # Таблица результатов
        self._result_table = QTableWidget(0, 2)
        self._result_table.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self._result_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._result_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._result_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG_BASE};
                color: {Colors.TEXT_PRIMARY};
                gridline-color: {Colors.TABLE_GRID};
                border: 1px solid {Colors.BORDER};
                font-size: 13px;
            }}
            QTableWidget::item {{ padding: 8px 12px; }}
            QTableWidget::item:selected {{
                background-color: {Colors.ACCENT_DIM};
            }}
            QHeaderView::section {{
                background-color: {Colors.TABLE_HEADER};
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-right: 1px solid {Colors.BORDER};
                border-bottom: 1px solid {Colors.BORDER};
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        res_layout.addWidget(self._result_table, 1)

        # Ординаты кривой по справочнику
        res_layout.addWidget(self._section_label("Ординаты из справочника"))
        self._ordinate_table = QTableWidget(0, 3)
        self._ordinate_table.setHorizontalHeaderLabels(
            ["Тангенс × 10", "Ордината × 10", "Ордината (м)"]
        )
        self._ordinate_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._ordinate_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._ordinate_table.setMaximumHeight(180)
        self._ordinate_table.setStyleSheet(self._result_table.styleSheet())
        res_layout.addWidget(self._ordinate_table)

        layout.addWidget(result_frame, 1)
        return w

    # ── Вкладка: Справочники ─────────────────────────────────

    def _build_reference_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background-color: {Colors.BG_BASE};")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.XL)

        # Ординаты
        ord_frame = self._ref_table_frame(
            "Ординаты кривых (tbOrdinate)",
            ["Тангенс × 10", "Ордината × 10"],
            "_ref_ordinate"
        )
        layout.addWidget(ord_frame)

        # Тангенсы
        tan_frame = self._ref_table_frame(
            "Тангенсы уклонов (tbTangent)",
            ["Разность уклонов", "Тангенс × 10"],
            "_ref_tangent"
        )
        layout.addWidget(tan_frame)

        return w

    def _ref_table_frame(self, title: str, headers: list,
                          attr: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            background-color: {Colors.BG_SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 6px;
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)

        lbl = QLabel(title)
        lbl.setFont(Typography.get_font(13, bold=True))
        lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(lbl)
        layout.addWidget(self._divider())

        tbl = QTableWidget(0, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG_BASE};
                color: {Colors.TEXT_PRIMARY};
                gridline-color: {Colors.TABLE_GRID};
                border: none;
                font-size: 13px;
            }}
            QTableWidget::item {{ padding: 6px 12px; }}
            QTableWidget::item:selected {{
                background-color: {Colors.ACCENT_DIM};
            }}
            QHeaderView::section {{
                background-color: {Colors.TABLE_HEADER};
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        layout.addWidget(tbl, 1)
        setattr(self, attr, tbl)
        return frame

    # ── Загрузка справочников ────────────────────────────────

    def _load_reference_tables(self):
        # Ординаты
        rows = self._ctx.db.fetchall(
            "SELECT Tangent10, Ordinate10 FROM tbOrdinate ORDER BY Tangent10"
        )
        self._ref_ordinate.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._ref_ordinate.setItem(i, 0, QTableWidgetItem(str(r["Tangent10"])))
            self._ref_ordinate.setItem(i, 1, QTableWidgetItem(str(r["Ordinate10"])))

        # Тангенсы
        rows = self._ctx.db.fetchall(
            "SELECT SlopeDifference, Tangent10 FROM tbTangent ORDER BY SlopeDifference"
        )
        self._ref_tangent.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._ref_tangent.setItem(i, 0, QTableWidgetItem(str(r["SlopeDifference"])))
            self._ref_tangent.setItem(i, 1, QTableWidgetItem(str(r["Tangent10"])))

    # ── Расчёт кривой ────────────────────────────────────────

    def _calculate_curve(self):
        deg    = self._angle_deg.value()
        min_   = self._angle_min.value()
        radius = self._radius.value()

        if radius <= 0:
            return

        # Угол в радианах
        angle_total_deg = deg + min_ / 60.0
        alpha = math.radians(angle_total_deg)

        # Основные элементы круговой кривой
        tangent    = radius * math.tan(alpha / 2)           # Тангенс
        length     = math.radians(angle_total_deg) * radius  # Длина кривой
        bisector   = radius * (1 / math.cos(alpha / 2) - 1) # Биссектриса
        domer      = 2 * tangent - length                    # Домер
        midord     = radius * (1 - math.cos(alpha / 2))      # Средняя ордината

        results = [
            ("Угол поворота",        f"{deg}° {min_:.1f}'"),
            ("Радиус",               f"{radius} м"),
            ("",                     ""),
            ("Тангенс (Т)",          f"{tangent:.3f} м"),
            ("Длина кривой (К)",     f"{length:.3f} м"),
            ("Биссектриса (Б)",      f"{bisector:.3f} м"),
            ("Домер (Д)",            f"{domer:.3f} м"),
            ("Средняя ордината",     f"{midord:.3f} м"),
            ("",                     ""),
            ("Т × 10",               f"{tangent * 10:.1f}"),
            ("К × 10",               f"{length * 10:.1f}"),
        ]

        self._result_table.setRowCount(len(results))
        bold_font = Typography.get_font(13, bold=True)

        for i, (param, value) in enumerate(results):
            p_item = QTableWidgetItem(param)
            v_item = QTableWidgetItem(value)

            if not param:  # разделитель
                p_item.setBackground(
                    self._result_table.palette().alternateBase()
                )
                v_item.setBackground(
                    self._result_table.palette().alternateBase()
                )
            elif param in ("Тангенс (Т)", "Длина кривой (К)", "Домер (Д)"):
                v_item.setFont(bold_font)
                v_item.setForeground(
                    __import__("PySide6.QtGui", fromlist=["QColor"]).QColor(Colors.ACCENT)
                )

            self._result_table.setItem(i, 0, p_item)
            self._result_table.setItem(i, 1, v_item)

        # Ординаты из справочника для данного тангенса
        self._fill_ordinates(tangent, radius)

    def _fill_ordinates(self, tangent: float, radius: float):
        """Подобрать ординаты из tbOrdinate для данного тангенса."""
        tangent10 = tangent * 10

        rows = self._ctx.db.fetchall(
            "SELECT Tangent10, Ordinate10 FROM tbOrdinate "
            "WHERE Tangent10 <= ? ORDER BY Tangent10 DESC LIMIT 10",
            (tangent10,)
        )

        self._ordinate_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            t10 = r["Tangent10"]
            o10 = r["Ordinate10"]
            # Масштабируем ординату под реальный радиус
            # Формула: O = O10 × (R / 10)
            o_real = o10 * (radius / 10.0) if o10 else 0

            self._ordinate_table.setItem(i, 0, QTableWidgetItem(str(t10)))
            self._ordinate_table.setItem(i, 1, QTableWidgetItem(str(o10)))
            self._ordinate_table.setItem(i, 2, QTableWidgetItem(f"{o_real:.4f} м"))

    # ── Утилиты ──────────────────────────────────────────────

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;"
        )
        return lbl

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