"""
modules/autocad/connector.py
=============================
Универсальное подключение к AutoCAD через COM.
Поддерживает все версии: 2000 (16) → 2025 (25+).

Принцип: перебираем ProgID от новых к старым,
берём первый который отвечает.
"""

import logging
from typing import Optional

log = logging.getLogger("autocad")

# ProgID всех известных версий AutoCAD (новые → старые)
AUTOCAD_PROGIDS = [
    "AutoCAD.Application.26",  # 2026
    "AutoCAD.Application.25",  # 2025
    "AutoCAD.Application.24",  # 2024
    "AutoCAD.Application.23",  # 2023 / 2022 / 2021
    "AutoCAD.Application.22",  # 2020 / 2019
    "AutoCAD.Application.21",  # 2018 / 2017
    "AutoCAD.Application.20",  # 2016 / 2015
    "AutoCAD.Application.19",  # 2014 / 2013
    "AutoCAD.Application.18",  # 2012 / 2011 / 2010
    "AutoCAD.Application.17",  # 2008 / 2007 / 2006
    "AutoCAD.Application.16",  # 2004 / 2005
    "AutoCAD.Application",     # generic fallback
]

_cached_app = None


def get_autocad(force_reconnect: bool = False):
    """
    Получить объект AutoCAD.Application.
    Возвращает COM-объект или None если AutoCAD не запущен.
    Кэширует подключение.
    """
    global _cached_app

    if not force_reconnect and _cached_app is not None:
        try:
            _ = _cached_app.Version  # проверка живости
            return _cached_app
        except Exception:
            _cached_app = None

    try:
        import win32com.client as win32
    except ImportError:
        log.error("pywin32 не установлен. pip install pywin32")
        return None

    # Сначала попробовать подключиться к уже запущенному
    for progid in AUTOCAD_PROGIDS:
        try:
            app = win32.GetActiveObject(progid)
            _ = app.Version
            _cached_app = app
            log.info(f"Подключён к AutoCAD: {progid} (v{app.Version})")
            return app
        except Exception:
            continue

    # Если не запущен — попробовать запустить
    for progid in AUTOCAD_PROGIDS:
        try:
            app = win32.Dispatch(progid)
            app.Visible = True
            _cached_app = app
            log.info(f"Запущен AutoCAD: {progid}")
            return app
        except Exception:
            continue

    log.warning("AutoCAD не найден ни по одному ProgID")
    return None


def get_active_doc(app=None):
    """Получить активный документ AutoCAD."""
    if app is None:
        app = get_autocad()
    if app is None:
        return None
    try:
        doc = app.ActiveDocument
        _ = doc.Name  # проверка
        return doc
    except Exception:
        return None


def get_modelspace(app=None):
    """Получить ModelSpace активного документа."""
    doc = get_active_doc(app)
    if doc is None:
        return None
    try:
        return doc.ModelSpace
    except Exception:
        return None


def get_autocad_version() -> Optional[str]:
    """Вернуть строку версии AutoCAD или None."""
    app = get_autocad()
    if app is None:
        return None
    try:
        return app.Version
    except Exception:
        return None


def is_autocad_running() -> bool:
    return get_autocad() is not None


def get_all_layers() -> list[str]:
    """Список всех слоёв активного документа."""
    doc = get_active_doc()
    if doc is None:
        return []
    try:
        return [doc.Layers.Item(i).Name for i in range(doc.Layers.Count)]
    except Exception as e:
        log.error(f"get_all_layers: {e}")
        return []


def get_layer_objects(layer_name: str) -> list:
    """Все объекты на указанном слое."""
    ms = get_modelspace()
    if ms is None:
        return []
    try:
        return [
            ms.Item(i) for i in range(ms.Count)
            if ms.Item(i).Layer == layer_name
        ]
    except Exception as e:
        log.error(f"get_layer_objects: {e}")
        return []


def get_layer_object_count(layer_name: str) -> dict:
    """Статистика объектов на слое: {всего, точки, блоки, текст}."""
    objects = get_layer_objects(layer_name)
    stats   = {"всего": len(objects), "точки": 0, "блоки": 0, "текст": 0}
    for obj in objects:
        try:
            name = obj.EntityName
            if name == "AcDbPoint":
                stats["точки"] += 1
            elif name == "AcDbBlockReference":
                stats["блоки"] += 1
            elif name in ("AcDbText", "AcDbMText"):
                stats["текст"] += 1
        except Exception:
            continue
    return stats


def extract_property(obj, prop: str):
    """
    Извлечь свойство из объекта AutoCAD.
    prop: 'X' | 'Y' | 'Z' | 'TextString' | 'Handle'
    """
    try:
        if prop in ("X", "Y", "Z"):
            idx = {"X": 0, "Y": 1, "Z": 2}[prop]
            name = obj.EntityName
            if name == "AcDbPoint":
                coords = obj.Coordinates
            elif name in ("AcDbBlockReference", "AcDbText", "AcDbMText"):
                coords = obj.InsertionPoint
            else:
                return None
            return round(coords[idx], 4)
        elif prop == "TextString":
            return obj.TextString
        elif prop == "Handle":
            return obj.Handle
        elif prop == "Layer":
            return obj.Layer
    except Exception:
        return None
    return None


def reset_cache():
    global _cached_app
    _cached_app = None