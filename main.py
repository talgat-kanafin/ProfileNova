"""
main.py — Точка входа ProfileNova.
"""

import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S"
)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore    import Qt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.theme import apply_theme
from ui.i18n  import set_language, get_language


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ProfileNova")
    app.setOrganizationName("ProfileNova")
    apply_theme(app)

    # Инициализация ядра
    from core.app_context import AppContext
    ctx = AppContext()

    if not ctx.initialize():
        QMessageBox.critical(None, "Ошибка", "Не удалось инициализировать базу данных.")
        sys.exit(1)

    # Восстановить язык из настроек
    saved_lang = ctx.db.fetchone(
        "SELECT value FROM app_meta WHERE key='language'"
    )
    if saved_lang:
        set_language(saved_lang["value"])

    # Первый запуск — визард настройки
    from ui.screens.setup_wizard import SetupWizard
    if SetupWizard.needs_setup():
        wizard = SetupWizard(ctx.db)
        wizard.exec()
        # После визарда переинициализировать auth
        from core.auth.auth import AuthManager
        ctx.auth = AuthManager(ctx.db, ctx.cloud)

    # Экран входа
    from ui.screens.login_screen import LoginScreen
    login = LoginScreen(ctx.auth)
    login.setMinimumSize(900, 600)
    login.setWindowTitle("ProfileNova — Вход")

    def on_login_success(user: dict):
        login.hide()

        from ui.screens.projects_screen import ProjectsScreen
        projects_screen = ProjectsScreen(ctx)
        projects_screen.setWindowTitle(f"ProfileNova — {user['full_name']}")
        projects_screen.setMinimumSize(1100, 700)

        def on_project_selected(project_id: int, is_editing: bool):
            from ui.screens.main_window import MainWindow
            main_win = MainWindow(ctx, project_id, is_editing)
    
            def on_logout():
                main_win.hide()
                projects_screen.show()
                projects_screen._load_projects()
    
            main_win.logout_requested.connect(on_logout)
            projects_screen.hide()
            main_win.show()
    
        projects_screen.project_selected.connect(on_project_selected)
        projects_screen.show()
    
    login.login_success.connect(on_login_success)
    login.show()

    exit_code = app.exec()
    ctx.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
