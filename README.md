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
Python 3.11+
PySide6
psycopg2-binary
bcrypt
openpyxl
access-parser
matplotlib
pywin32 (Windows only, for AutoCAD)

## Quick Start

```bash
git clone https://github.com/your-username/ProfileNova
cd ProfileNova
pip install -r requirements.txt
python main.py
```

On first launch a setup wizard will guide you through cloud configuration and admin account creation.

## Cloud Setup

The app uses [Supabase](https://supabase.com) as a cloud backend. Create a free project, run `supabase_schema.sql` in the SQL Editor, and enter the connection details in the setup wizard.

## Building

```bash
python -m PyInstaller --onefile --windowed --name ProfileNova \
  --add-data "ui;ui" --add-data "core;core" \
  --add-data "modules;modules" --add-data "config;config" \
  --hidden-import PySide6.QtCore --hidden-import PySide6.QtWidgets \
  --hidden-import PySide6.QtGui --hidden-import psycopg2 \
  --hidden-import bcrypt --hidden-import openpyxl \
  --hidden-import access_parser --hidden-import mdb_parser \
  main.py
```

Output: `dist/ProfileNova.exe`

## Project Structure
ProfileNova/
├── core/
│ ├── db/ # LocalDB (SQLite), CloudDB (Supabase), importer (.mdb)
│ ├── auth/ # AuthManager — login, roles, project locks, sessions
│ └── sync/ # SyncEngine — background thread, offline queue
├── ui/
│ ├── screens/ # All application screens and pages
│ ├── dialogs/ # Add way, add station, split text dialogs
│ ├── theme.py # Design tokens — dark/orange
│ └── i18n.py # RU/KK localization
├── modules/
│ └── autocad/ # Connector, capture, drawing generation
├── main.py
└── supabase_schema.sql

## License

Private — all rights reserved.
