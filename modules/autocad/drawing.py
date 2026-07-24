"""
modules/autocad/drawing.py
===========================
Генерация чертежей в AutoCAD из данных БД.

9 типов чертежей (как в старой программе):
  1. План-профиль пути
  2. Продольный профиль пути
  3. Раскладка рельсовых плетей
  4. Станционные пути (1:1000)
  5. Станционные пути (1:200)
  6. Станционные пути (сжатый)
  7. Рихтовка пути
  8. Подъездные пути
  9. Подъездные пути (паспорт.)
"""

import logging
import math
from typing import Optional, Callable

from modules.autocad.connector import get_autocad, get_active_doc, get_modelspace

log = logging.getLogger("drawing")

# Типы чертежей
DRAWING_TYPES = [
    ("plan_profile",      "План-профиль пути"),
    ("long_profile",      "Продольный профиль пути"),
    ("rail_pleti",        "Раскладка рельсовых плетей"),
    ("station_1000",      "Станционные пути (1:1000)"),
    ("station_200",       "Станционные пути (1:200)"),
    ("station_compact",   "Станционные пути (сжатый)"),
    ("straightening",     "Рихтовка пути"),
    ("access_way",        "Подъездные пути"),
    ("access_way_pass",   "Подъездные пути (паспорт.)"),
]

# Слои чертежа
LAYER_RAIL     = "RAIL"
LAYER_GROUND   = "GROUND"
LAYER_GRID     = "GRID"
LAYER_TEXT     = "TEXT"
LAYER_DEVICES  = "DEVICES"
LAYER_CURVES   = "CURVES"


class DrawingGenerator:
    """
    Генератор чертежей. Работает с открытым AutoCAD.
    on_progress(message) — callback для UI.
    """

    def __init__(self, db, project_id: int,
                 on_progress: Callable = None):
        self._db         = db
        self._project_id = project_id
        self._progress   = on_progress or (lambda msg: None)
        self._app        = None
        self._doc        = None
        self._ms         = None

    def connect(self) -> bool:
        self._app = get_autocad()
        self._doc = get_active_doc(self._app)
        self._ms  = get_modelspace(self._app)
        return self._ms is not None

    # ── Точка входа ──────────────────────────────────────────

    def generate(
        self,
        drawing_type: str,
        way_id: int,
        side: str = "left",           # "left" | "right"
        vertical_radius: float = 0,
        split_pages: bool = False,
        station_id: int = None
    ) -> bool:
        """
        Генерировать чертёж указанного типа.
        Возвращает True если успешно.
        """
        if not self.connect():
            log.error("AutoCAD недоступен")
            return False

        self._progress("Подготовка чертежа...")
        self._setup_layers()

        try:
            if drawing_type == "long_profile":
                return self._draw_long_profile(way_id, side, vertical_radius)
            elif drawing_type == "plan_profile":
                return self._draw_plan_profile(way_id, side)
            elif drawing_type == "rail_pleti":
                return self._draw_rail_pleti(way_id, side)
            elif drawing_type in ("station_1000", "station_200", "station_compact"):
                scale = {"station_1000": 1000, "station_200": 200,
                         "station_compact": 500}.get(drawing_type, 1000)
                return self._draw_station(station_id, scale)
            elif drawing_type == "straightening":
                return self._draw_straightening(way_id, side)
            elif drawing_type in ("access_way", "access_way_pass"):
                passport = drawing_type == "access_way_pass"
                return self._draw_access_way(way_id, passport)
            else:
                log.error(f"Неизвестный тип чертежа: {drawing_type}")
                return False
        except Exception as e:
            log.error(f"generate({drawing_type}): {e}")
            return False

    # ── Настройка слоёв ──────────────────────────────────────

    def _setup_layers(self):
        """Создать слои чертежа если не существуют."""
        layers_config = [
            (LAYER_RAIL,    7,   "CONTINUOUS"),   # белый
            (LAYER_GROUND,  8,   "CONTINUOUS"),   # серый
            (LAYER_GRID,    9,   "DASHED"),
            (LAYER_TEXT,    7,   "CONTINUOUS"),
            (LAYER_DEVICES, 1,   "CONTINUOUS"),   # красный
            (LAYER_CURVES,  5,   "CONTINUOUS"),   # синий
        ]
        try:
            for name, color, linetype in layers_config:
                try:
                    layer = self._doc.Layers.Item(name)
                except Exception:
                    layer = self._doc.Layers.Add(name)
                layer.Color = color
        except Exception as e:
            log.warning(f"_setup_layers: {e}")

    # ── Продольный профиль ───────────────────────────────────

    def _draw_long_profile(self, way_id: int, side: str,
                           vertical_radius: float) -> bool:
        self._progress("Загрузка данных профиля...")

        rail_col = "Left_Rail" if side == "left" else "Right_Rail"
        rows = self._db.fetchall(
            f"SELECT Km, Picket, Meter, {rail_col}, Ground "
            f"FROM tbWayData "
            f"WHERE project_id=? AND WayId=? "
            f"ORDER BY Km, Picket",
            (self._project_id, way_id)
        )
        if not rows:
            log.warning("Нет данных для продольного профиля")
            return False

        self._progress(f"Черчение профиля: {len(rows)} точек...")

        # Масштаб: горизонт 1:1000, вертикаль 1:100
        H_SCALE = 1.0    # 1 пк = 1 единица AutoCAD
        V_SCALE = 10.0   # высоты × 10

        # Базовая отметка — минимум земли
        valid_ground = [r["Ground"] for r in rows if r.get("Ground")]
        base_z = min(valid_ground) - 2.0 if valid_ground else 0

        # --- Линия рельса ---
        rail_points = []
        ground_points = []
        x = 0.0

        for r in rows:
            pk_len = 100.0  # стандартная длина пикета
            rail_z   = r.get(rail_col)
            ground_z = r.get("Ground")

            if rail_z is not None:
                rail_points.append((x, (rail_z - base_z) * V_SCALE))
            if ground_z is not None:
                ground_points.append((x, (ground_z - base_z) * V_SCALE))
            x += H_SCALE

        self._draw_polyline(rail_points,   LAYER_RAIL,   color=7)
        self._draw_polyline(ground_points, LAYER_GROUND, color=8)

        # --- Подписи отметок ---
        self._progress("Расстановка подписей...")
        x = 0.0
        for r in rows:
            rail_z = r.get(rail_col)
            if rail_z is not None:
                y = (rail_z - base_z) * V_SCALE + 2
                self._add_text(
                    str(round(rail_z, 2)), x, y,
                    height=1.5, layer=LAYER_TEXT, rotation=90
                )
            x += H_SCALE

        # --- Сетка пикетов ---
        self._progress("Сетка пикетов...")
        x = 0.0
        for i, r in enumerate(rows):
            # Вертикальная линия сетки
            self._draw_line(x, -5, x, -2, LAYER_GRID)
            # Подпись км+пк
            label = f"{r.get('Km','')}/{r.get('Picket','')}"
            self._add_text(label, x, -7, height=1.5, layer=LAYER_TEXT)
            x += H_SCALE

        # --- Устройства ---
        self._draw_devices_on_profile(way_id, base_z, V_SCALE)

        self._doc.Regen(0)
        self._progress("Продольный профиль построен ✓")
        return True

    # ── Станционные пути ─────────────────────────────────────

    def _draw_station(self, station_id: int, scale: int) -> bool:
        if station_id is None:
            log.error("station_id не указан")
            return False

        self._progress("Загрузка данных станции...")

        ways = self._db.fetchall(
            "SELECT WayId, Name FROM tbStationWay "
            "WHERE project_id=? AND StationId=? ORDER BY WayId",
            (self._project_id, station_id)
        )
        if not ways:
            return False

        station = self._db.fetchone(
            "SELECT Name FROM tbStation WHERE project_id=? AND StationId=?",
            (self._project_id, station_id)
        )
        station_name = station["Name"] if station else f"Станция {station_id}"

        self._progress(f"Черчение станции: {station_name} (1:{scale})...")

        y_offset = 0.0
        TRACK_SPACING = 20.0 / (scale / 200)

        for way in ways:
            wid  = way["WayId"]
            name = way["Name"] or f"Путь {wid}"

            rows = self._db.fetchall(
                "SELECT Km, Picket, Meter, Rail, SUklon "
                "FROM tbStationWayData "
                "WHERE project_id=? AND StationId=? AND StationWayId=? "
                "ORDER BY Km, Picket",
                (self._project_id, station_id, wid)
            )

            if not rows:
                y_offset += TRACK_SPACING
                continue

            # Горизонтальная линия пути
            x_start = 0.0
            x_end   = len(rows) * 1.0
            self._draw_line(x_start, y_offset, x_end, y_offset, LAYER_RAIL)

            # Подпись пути
            self._add_text(name, -5, y_offset, height=2.0, layer=LAYER_TEXT)

            # Отметки рельса
            for i, r in enumerate(rows):
                rail = r.get("Rail")
                if rail is not None:
                    self._add_text(
                        str(round(rail, 2)),
                        float(i), y_offset + 2,
                        height=1.2, layer=LAYER_TEXT, rotation=90
                    )

            y_offset += TRACK_SPACING

        # Название станции
        self._add_text(
            station_name, 0, y_offset + 10,
            height=4.0, layer=LAYER_TEXT
        )

        self._doc.Regen(0)
        self._progress(f"Чертёж станции построен ✓")
        return True

    # ── Раскладка рельсовых плетей ───────────────────────────

    def _draw_rail_pleti(self, way_id: int, side: str) -> bool:
        self._progress("Загрузка плетей...")

        table = "tbLeftPleti" if side == "left" else "tbRightPleti"
        rows = self._db.fetchall(
            f"SELECT * FROM {table} WHERE project_id=? AND WayId=? "
            f"ORDER BY RecordNumber",
            (self._project_id, way_id)
        )
        if not rows:
            return False

        self._progress(f"Черчение {len(rows)} плетей...")

        y = 0.0
        for r in rows:
            # R-нитка
            rx_s = (r.get("RStartKm", 0) * 10 + r.get("RStartPk", 0)) * 1.0
            rx_e = (r.get("REndKm",   0) * 10 + r.get("REndPk",   0)) * 1.0
            self._draw_line(rx_s, y,      rx_e, y,      LAYER_RAIL,   color=1)

            # L-нитка
            lx_s = (r.get("LStartKm", 0) * 10 + r.get("LStartPk", 0)) * 1.0
            lx_e = (r.get("LEndKm",   0) * 10 + r.get("LEndPk",   0)) * 1.0
            self._draw_line(lx_s, y - 3, lx_e, y - 3, LAYER_RAIL,   color=3)

            y -= 8

        self._doc.Regen(0)
        self._progress("Раскладка плетей построена ✓")
        return True

    # ── Рихтовка ─────────────────────────────────────────────

    def _draw_straightening(self, way_id: int, side: str) -> bool:
        self._progress("Загрузка данных рихтовки...")

        col = "Left_Straightening" if side == "left" else "Right_Straightening"
        rows = self._db.fetchall(
            f"SELECT Km, Picket, Meter, {col}, CurrentTrackSpacing "
            f"FROM tbStraighteningData "
            f"WHERE project_id=? AND WayId=? ORDER BY Km, Picket",
            (self._project_id, way_id)
        )
        if not rows:
            return False

        self._progress(f"Черчение рихтовки: {len(rows)} точек...")

        points = []
        x = 0.0
        for r in rows:
            val = r.get(col)
            if val is not None:
                points.append((x, float(val) * 5))
            x += 1.0

        # Нулевая линия
        self._draw_line(0, 0, x, 0, LAYER_GRID)
        self._draw_polyline(points, LAYER_CURVES, color=5)

        self._doc.Regen(0)
        self._progress("Рихтовка построена ✓")
        return True

    # ── Подъездные пути ──────────────────────────────────────

    def _draw_access_way(self, way_id: int, passport: bool) -> bool:
        self._progress("Загрузка подъездного пути...")

        rows = self._db.fetchall(
            "SELECT Picket, Meter, Ground, Rail, SUklon "
            "FROM tbAccessWayData "
            "WHERE project_id=? AND AccessWayId=? ORDER BY Picket, Meter",
            (self._project_id, way_id)
        )
        if not rows:
            return False

        self._progress(f"Черчение подъездного пути...")

        valid_ground = [r["Ground"] for r in rows if r.get("Ground")]
        base_z = min(valid_ground) - 1.0 if valid_ground else 0

        V_SCALE = 10.0
        rail_pts   = []
        ground_pts = []
        x = 0.0

        for r in rows:
            if r.get("Rail"):
                rail_pts.append((x, (r["Rail"] - base_z) * V_SCALE))
            if r.get("Ground"):
                ground_pts.append((x, (r["Ground"] - base_z) * V_SCALE))
            x += 1.0

        self._draw_polyline(rail_pts,   LAYER_RAIL,   color=7)
        self._draw_polyline(ground_pts, LAYER_GROUND, color=8)

        if passport:
            # Паспортный вариант: добавить таблицу с данными
            self._add_text("ПАСПОРТ ПОДЪЕЗДНОГО ПУТИ", 0, -15,
                           height=3.0, layer=LAYER_TEXT)

        self._doc.Regen(0)
        self._progress("Подъездной путь построен ✓")
        return True

    # ── План-профиль ─────────────────────────────────────────

    def _draw_plan_profile(self, way_id: int, side: str) -> bool:
        """Совмещённый план и профиль."""
        # Продольный профиль сверху
        ok = self._draw_long_profile(way_id, side, 0)
        if not ok:
            return False

        # Кривые снизу (план)
        table = "tbLeftCurve" if side == "left" else "tbRightCurve"
        curves = self._db.fetchall(
            f"SELECT startKm, startPk, endKm, endPk, Radius, AngleDegree "
            f"FROM {table} WHERE project_id=? AND WayId=? "
            f"ORDER BY startKm, startPk",
            (self._project_id, way_id)
        )

        y_plan = -20.0
        self._draw_line(0, y_plan, 200, y_plan, LAYER_GRID)

        for c in curves:
            x_s = (c.get("startKm", 0) * 10 + c.get("startPk", 0)) * 1.0
            x_e = (c.get("endKm",   0) * 10 + c.get("endPk",   0)) * 1.0
            r   = c.get("Radius", 0)
            self._draw_line(x_s, y_plan - 3, x_e, y_plan - 3, LAYER_CURVES)
            if r:
                mid = (x_s + x_e) / 2
                self._add_text(f"R={r}", mid, y_plan - 5,
                               height=1.5, layer=LAYER_TEXT)

        self._doc.Regen(0)
        self._progress("План-профиль построен ✓")
        return True

    # ── Устройства на профиле ────────────────────────────────

    def _draw_devices_on_profile(self, way_id: int,
                                  base_z: float, v_scale: float):
        devices = self._db.fetchall(
            "SELECT d.Kilometer, d.Picket, d.Meter, dev.DeviceName "
            "FROM tbDeviceLocation d "
            "LEFT JOIN tbDevice dev ON dev.DeviceId=d.DeviceId "
            "   AND dev.project_id=d.project_id "
            "WHERE d.project_id=? AND d.WayId=?",
            (self._project_id, way_id)
        )
        for d in devices:
            x = (d.get("Kilometer", 0) * 10 + d.get("Picket", 0)) * 1.0
            self._draw_line(x, 0, x, 5, LAYER_DEVICES, color=1)
            name = d.get("DeviceName") or "?"
            self._add_text(name[:6], x, 6, height=1.2, layer=LAYER_DEVICES)

    # ── Примитивы AutoCAD ────────────────────────────────────

    def _draw_line(self, x1: float, y1: float,
                   x2: float, y2: float,
                   layer: str, color: int = 256):
        try:
            import win32com.client as win32
            import pythoncom
            p1 = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8,
                               [x1, y1, 0.0])
            p2 = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8,
                               [x2, y2, 0.0])
            line = self._ms.AddLine(p1, p2)
            line.Layer = layer
            if color != 256:
                line.Color = color
        except Exception as e:
            log.debug(f"_draw_line: {e}")

    def _draw_polyline(self, points: list, layer: str, color: int = 256):
        if len(points) < 2:
            return
        try:
            import win32com.client as win32
            import pythoncom
            flat = []
            for x, y in points:
                flat.extend([float(x), float(y), 0.0])
            arr = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)
            pl = self._ms.Add3DPoly(arr)
            pl.Layer = layer
            if color != 256:
                pl.Color = color
        except Exception as e:
            log.debug(f"_draw_polyline: {e}")

    def _add_text(self, text: str, x: float, y: float,
                  height: float = 2.0, layer: str = LAYER_TEXT,
                  rotation: float = 0):
        try:
            import win32com.client as win32
            import pythoncom
            pt = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8,
                               [x, y, 0.0])
            txt = self._ms.AddText(str(text), pt, height)
            txt.Layer    = layer
            txt.Rotation = math.radians(rotation)
        except Exception as e:
            log.debug(f"_add_text: {e}")