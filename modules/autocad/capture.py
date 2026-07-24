"""
modules/autocad/capture.py
===========================
Захват данных из AutoCAD.

Авто-захват:  все объекты слоя → список значений
Ручной захват: пользователь выделяет объекты в AutoCAD → список значений
"""

import logging
import time
from typing import Optional

from modules.autocad.connector import (
    get_autocad, get_active_doc, get_modelspace,
    get_layer_objects, extract_property
)

log = logging.getLogger("capture")

# Доступные свойства для захвата
CAPTURE_PROPERTIES = {
    "Z":          "Высотная отметка Z (м)",
    "X":          "Координата X",
    "Y":          "Координата Y",
    "TextString": "Текст / содержимое",
    "Handle":     "Идентификатор объекта",
}


def auto_capture(layer_name: str, prop: str) -> list:
    """
    Авто-захват всех объектов указанного слоя.
    Возвращает список значений (str/float) или пустой список.
    """
    objects = get_layer_objects(layer_name)
    if not objects:
        log.warning(f"Слой '{layer_name}' пустой или не найден")
        return []

    values = []
    for obj in objects:
        val = extract_property(obj, prop)
        if val is not None:
            values.append(val)

    log.info(f"Авто-захват '{layer_name}'.{prop}: {len(values)} значений")
    return values


def manual_capture(prop: str, timeout: int = 60) -> list:
    """
    Ручной захват — пользователь выделяет объекты в AutoCAD.

    Алгоритм:
    1. Отправить команду _SELECT в AutoCAD
    2. Ждать пока пользователь выделит объекты и нажмёт Enter
    3. Считать SelectionSet и извлечь свойство

    Возвращает список значений или пустой список.
    timeout — максимальное ожидание в секундах.
    """
    app = get_autocad()
    doc = get_active_doc(app)
    if app is None or doc is None:
        raise ConnectionError("AutoCAD не подключён")

    try:
        # Очистить предыдущие selection sets
        ss_name = "PROFILENOVA_CAPTURE"
        try:
            existing = doc.SelectionSets.Item(ss_name)
            existing.Delete()
        except Exception:
            pass

        ss = doc.SelectionSets.Add(ss_name)

        # Переключить фокус на AutoCAD
        app.Visible = True
        try:
            app.WindowState = 3  # acMax
        except Exception:
            pass

        # Предложить пользователю выделить объекты
        # SelectOnScreen() блокирует выполнение до нажатия Enter
        ss.SelectOnScreen()

        values = []
        for i in range(ss.Count):
            obj = ss.Item(i)
            val = extract_property(obj, prop)
            if val is not None:
                values.append(val)

        ss.Delete()
        log.info(f"Ручной захват .{prop}: {len(values)} значений")
        return values

    except Exception as e:
        log.error(f"manual_capture: {e}")
        if "0x80020009" in str(e) or "cancelled" in str(e).lower():
            raise InterruptedError("Захват отменён пользователем")
        raise


def capture_to_table_column(
    values: list,
    db,
    project_id: int,
    table_name: str,
    column_name: str,
    way_id: int,
    start_record: int = 1
) -> int:
    """
    Записать захваченные значения в указанную колонку таблицы БД.
    Совпадение по RecordNumber начиная с start_record.
    Возвращает количество обновлённых строк.
    """
    updated = 0
    for i, value in enumerate(values):
        record_num = start_record + i
        try:
            db.execute(
                f"UPDATE {table_name} SET {column_name}=? "
                f"WHERE project_id=? AND WayId=? AND RecordNumber=?",
                (value, project_id, way_id, record_num)
            )
            updated += 1
        except Exception as e:
            log.error(f"capture_to_table_column row {record_num}: {e}")

    db.commit()
    log.info(f"Записано {updated} значений → {table_name}.{column_name}")
    return updated