"""
test_module1.py
===============
Проверка Модуля 1 — ядро БД, авторизация.
Запускать из папки ProfileNova: python test_module1.py

Ожидаемый результат:
  [OK] LocalDB создана
  [OK] Таблицы созданы: XX таблиц
  [OK] Admin создан по умолчанию
  [OK] Вход admin/admin123
  [OK] Смена пароля
  [OK] Создание пользователя
  [OK] Создание проекта
  [OK] Блокировка проекта
  [OK] Снятие блокировки
  [OK] AppContext инициализирован
"""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s"
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Тестовая БД — не трогает основную
TEST_DB = os.path.join(os.path.dirname(__file__), "test_local.db")
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)


def check(label, condition, detail=""):
    if condition:
        print(f"  [OK] {label}")
    else:
        print(f"  [FAIL] {label}" + (f": {detail}" if detail else ""))
    return condition


def run_tests():
    print("\n══════════════════════════════════")
    print("  ProfileNova — Модуль 1: Ядро БД")
    print("══════════════════════════════════\n")

    # ── 1. LocalDB ───────────────────────────────────────────
    print("1. LocalDB")
    from core.db.database import LocalDB

    db = LocalDB(TEST_DB)
    check("LocalDB создана", os.path.exists(TEST_DB))

    tables = db.fetchall(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    table_names = [t["name"] for t in tables]
    check(f"Таблицы созданы ({len(table_names)} шт)", len(table_names) >= 25)

    # Проверить ключевые таблицы
    required = ["users", "projects", "project_locks", "audit_log",
                "sync_queue", "tbWayData", "tbStation", "tbCurve"]
    for t in required:
        check(f"  Таблица {t}", t in table_names)

    # ── 2. AuthManager ───────────────────────────────────────
    print("\n2. AuthManager")
    from core.auth.auth import AuthManager

    auth = AuthManager(db)

    admin = db.fetchone("SELECT * FROM users WHERE role='admin'")
    check("Admin создан по умолчанию", admin is not None)
    check("  Username = 'admin'", admin and admin["username"] == "admin")

    ok, msg = auth.login("admin", "admin123")
    check("Вход admin/admin123", ok, msg)
    check("current_user установлен", auth.current_user is not None)
    check("is_admin = True", auth.is_admin)

    ok, msg = auth.login("admin", "wrongpass")
    check("Неверный пароль отклонён", not ok)

    # Смена пароля
    user_id = admin["id"]
    ok, _ = auth.login("admin", "admin123")
    ok2, _ = auth.change_password(user_id, "newpass456")
    check("Смена пароля", ok2)
    auth.login("admin", "admin123")  # перелогин для прав
    # вход со старым паролем
    ok3, _ = auth.login("admin", "admin123")
    # Восстановить
    auth.login("admin", "newpass456")
    auth.change_password(user_id, "admin123")

    # Создание пользователя
    auth.login("admin", "admin123")
    ok, msg = auth.create_user(
        "ivanov", "pass123",
        "Иванов Иван Иванович", "Путевой отдел",
        role="editor"
    )
    check("Создание пользователя", ok, msg)

    # Дубликат
    ok2, _ = auth.create_user("ivanov", "xxx", "X", "Y")
    check("Дублирующийся username отклонён", not ok2)

    # ── 3. Проекты ───────────────────────────────────────────
    print("\n3. Проекты")
    auth.login("admin", "admin123")

    db.execute(
        "INSERT INTO projects (name, description, mdb_origin, created_by) VALUES (?,?,?,?)",
        ("Тестовый проект", "Проект для проверки", "profile 971.mdb", auth.current_user["id"])
    )
    db.commit()

    projects = auth.get_accessible_projects()
    check("Проект создан и доступен admin", len(projects) >= 1)

    project_id = projects[0]["id"]

    # Выдать доступ ivanov
    ivanov = db.fetchone("SELECT * FROM users WHERE username='ivanov'")
    auth.grant_access(project_id, ivanov["id"], can_edit=True)

    auth.login("ivanov", "pass123")
    projects2 = auth.get_accessible_projects()
    check("ivanov видит проект после grant_access", len(projects2) >= 1)
    check("ivanov может редактировать", auth.can_edit_project(project_id))

    # ── 4. Блокировки ────────────────────────────────────────
    print("\n4. Блокировки проекта")
    auth.login("admin", "admin123")

    success, who = auth.acquire_project_lock(project_id)
    check("admin взял блокировку", success)
    check("  Нет конфликта (who=None)", who is None)

    lock_info = auth.get_project_lock_info(project_id)
    check("  lock_info не None", lock_info is not None)
    check(f"  Заблокировал: {lock_info.get('user_fullname') if lock_info else '?'}",
          lock_info and "Администратор" in str(lock_info.get("user_fullname", "")))

    # Другой пользователь пытается взять блокировку
    auth.login("ivanov", "pass123")
    success2, who2 = auth.acquire_project_lock(project_id)
    check("ivanov не может взять заблокированный проект", not success2)
    check(f"  Видит кто держит: {who2}", who2 is not None)

    # Снять блокировку
    auth.login("admin", "admin123")
    auth.release_project_lock(project_id)

    auth.login("ivanov", "pass123")
    success3, _ = auth.acquire_project_lock(project_id)
    check("ivanov берёт проект после снятия блокировки", success3)
    auth.release_project_lock(project_id)

    # ── 5. AppContext ────────────────────────────────────────
    print("\n5. AppContext")
    from core.app_context import AppContext

    ctx = AppContext()
    ok = ctx.initialize()
    check("AppContext инициализирован", ok)
    check("ctx.db не None", ctx.db is not None)
    check("ctx.auth не None", ctx.auth is not None)
    check("ctx.sync не None", ctx.sync is not None)
    ctx.shutdown()

    # ── Итог ─────────────────────────────────────────────────
    print("\n══════════════════════════════════")
    print("  Модуль 1 проверен.")
    print("  Следующий шаг: Модуль 2 — Экран входа (UI)")
    print("══════════════════════════════════\n")

    # Cleanup
    db.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


if __name__ == "__main__":
    run_tests()
