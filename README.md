# ProfileNova

Modern railway track documentation system — a complete rebuild of the legacy Profile.exe (Delphi 2003 / MS Access) into a cross-platform desktop application.

## Stack

- **Frontend:** Python 3.11+, PySide6 (Qt6)
- **Local DB:** SQLite (WAL mode, offline-first)
- **Cloud:** PostgreSQL via Supabase (background sync)
- **AutoCAD:** COM integration (versions 2000–2025)

## Features

- Import legacy `.mdb` databases (Access 97/2000)
- Multi-user access with role-based permissions (admin / editor / viewer)
- Project locking — one editor at a time, others read-only
- Offline-first with automatic cloud sync every 30 seconds
- AutoCAD integration: data capture (auto by layer / manual selection) and drawing generation (9 types)
- Excel export for all data sections
- Longitudinal profile chart (matplotlib)
- Russian / Kazakh UI with runtime language switching
- Dark engineering UI — high contrast, orange accent

## Sections

| Section | Tables |
|---|---|
| Mainline (Перегон) | tbWayData, tbLeftCurve, tbRightCurve, tbDeviceLocation, tbLeftPleti, tbRightPleti, tbStraighteningData |
| Station (Станция) | tbStation, tbStationWay, tbStationWayData, tbStationDeviceLocation |
| Access Ways (Подъездные пути) | tbAccessWayInfo, tbAccessWayData, tbAccessWayCurve, tbAccessWayDevice |
| Drawings (Чертёж) | AutoCAD COM — 9 drawing types |
| Calculations (Вычисления) | tbOrdinate, tbTangent — curve element calculator |
| Admin | Users, roles, project access, audit log |

## Requirements
