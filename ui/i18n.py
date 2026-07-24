"""
ui/i18n.py — Локализация: русский / қазақша.
"""

import logging
from typing import Callable

log = logging.getLogger("i18n")

_listeners: list[Callable] = []
_current_lang: str = "ru"

_STRINGS = {
    "app.name":            {"ru": "ProfileNova",              "kk": "ProfileNova"},
    "btn.ok":              {"ru": "ОК",                       "kk": "ОК"},
    "btn.cancel":          {"ru": "Отмена",                   "kk": "Болдырмау"},
    "btn.save":            {"ru": "Сохранить",                "kk": "Сақтау"},
    "btn.close":           {"ru": "Закрыть",                  "kk": "Жабу"},
    "btn.delete":          {"ru": "Удалить",                  "kk": "Жою"},
    "btn.edit":            {"ru": "Редактировать",            "kk": "Өңдеу"},
    "btn.add":             {"ru": "Добавить",                 "kk": "Қосу"},
    "btn.back":            {"ru": "Назад",                    "kk": "Артқа"},
    "btn.confirm":         {"ru": "Подтвердить",              "kk": "Растау"},
    "btn.refresh":         {"ru": "Обновить",                 "kk": "Жаңарту"},
    "btn.import":          {"ru": "Импортировать",            "kk": "Импорттау"},
    "btn.export":          {"ru": "Экспорт",                  "kk": "Экспорт"},

    "login.title":         {"ru": "Вход в систему",           "kk": "Жүйеге кіру"},
    "login.subtitle":      {"ru": "Железнодорожный профиль",  "kk": "Теміржол профилі"},
    "login.username":      {"ru": "Логин",                    "kk": "Логин"},
    "login.password":      {"ru": "Пароль",                   "kk": "Құпия сөз"},
    "login.remember":      {"ru": "Запомнить меня",           "kk": "Мені есте сақтау"},
    "login.btn":           {"ru": "Войти",                    "kk": "Кіру"},
    "login.error.empty":   {"ru": "Введите логин и пароль",   "kk": "Логин мен құпия сөзді енгізіңіз"},
    "login.error.wrong":   {"ru": "Неверный логин или пароль","kk": "Логин немесе құпия сөз қате"},
    "login.error.inactive":{"ru": "Учётная запись отключена", "kk": "Тіркелгі өшірілген"},

    "projects.title":      {"ru": "Проекты",                  "kk": "Жобалар"},
    "projects.new":        {"ru": "Новый проект",             "kk": "Жаңа жоба"},
    "projects.import_mdb": {"ru": "Импорт из .mdb",           "kk": ".mdb-ден импорттау"},
    "projects.open_edit":  {"ru": "Открыть (редактирование)", "kk": "Ашу (өңдеу)"},
    "projects.open_view":  {"ru": "Открыть (просмотр)",       "kk": "Ашу (қарау)"},
    "projects.locked_by":  {"ru": "Редактирует:",             "kk": "Өңдеп жатыр:"},
    "projects.free":       {"ru": "Свободен",                 "kk": "Бос"},
    "projects.empty":      {"ru": "Нет доступных проектов",   "kk": "Қолжетімді жобалар жоқ"},
    "projects.search":     {"ru": "Поиск проектов...",        "kk": "Жобаларды іздеу..."},
    "projects.locked_msg": {
        "ru": "Проект редактирует: {user}.\nМожно открыть только для просмотра.",
        "kk": "Жоба {user} өңдеуде.\nТек қарау үшін ашуға болады.",
    },

    "import.title":        {"ru": "Импорт базы данных",       "kk": "Деректер базасын импорттау"},
    "import.select_file":  {"ru": "Выбрать файл .mdb",        "kk": ".mdb файлын таңдаңыз"},
    "import.project_name": {"ru": "Название проекта",         "kk": "Жоба атауы"},
    "import.description":  {"ru": "Описание (необязательно)", "kk": "Сипаттама (міндетті емес)"},
    "import.progress":     {"ru": "Импорт: {table}",          "kk": "Импорт: {table}"},
    "import.done":         {"ru": "Импорт завершён. Строк: {count}", "kk": "Импорт аяқталды. Жолдар: {count}"},
    "import.error":        {"ru": "Ошибка импорта: {error}",  "kk": "Импорт қатесі: {error}"},

    "nav.mainline":        {"ru": "Перегон",                  "kk": "Перегон"},
    "nav.station":         {"ru": "Станция",                  "kk": "Станция"},
    "nav.access_way":      {"ru": "Подъездные пути",          "kk": "Тармақ жолдар"},
    "nav.drawing":         {"ru": "Чертёж",                   "kk": "Сызба"},
    "nav.calculations":    {"ru": "Вычисления",               "kk": "Есептеулер"},
    "nav.admin":           {"ru": "Администрирование",        "kk": "Әкімшілік"},
    "nav.settings":        {"ru": "Настройки",                "kk": "Параметрлер"},

    "sync.ok":             {"ru": "Синхронизировано",         "kk": "Синхрондалды"},
    "sync.offline":        {"ru": "Нет связи — локальный режим", "kk": "Байланыс жоқ — жергілікті"},
    "sync.syncing":        {"ru": "Синхронизация...",         "kk": "Синхрондалуда..."},
    "sync.error":          {"ru": "Ошибка синхронизации",     "kk": "Синхрондау қатесі"},
    "sync.pending":        {"ru": "Ожидает: {count}",         "kk": "Күтуде: {count}"},

    "mode.editing":        {"ru": "Редактирование",           "kk": "Өңдеу"},
    "mode.viewing":        {"ru": "Просмотр",                 "kk": "Қарау"},
    "mode.switch_to_view": {"ru": "Перейти в просмотр",       "kk": "Қарауға өту"},
    "mode.switch_to_edit": {"ru": "Взять на редактирование",  "kk": "Өңдеуге алу"},

    "settings.title":      {"ru": "Настройки",                "kk": "Параметрлер"},
    "settings.language":   {"ru": "Язык интерфейса",          "kk": "Интерфейс тілі"},
    "settings.lang_ru":    {"ru": "Русский",                  "kk": "Орысша"},
    "settings.lang_kk":    {"ru": "Қазақша",                  "kk": "Қазақша"},
    "settings.cloud":      {"ru": "Облачный сервер",          "kk": "Бұлтты сервер"},
    "settings.cloud_url":  {"ru": "URL сервера",              "kk": "Сервер URL"},
    "settings.cloud_test": {"ru": "Проверить подключение",    "kk": "Қосылымды тексеру"},
    "settings.cloud_ok":   {"ru": "Подключение успешно",      "kk": "Қосылым сәтті"},
    "settings.cloud_fail": {"ru": "Не удалось подключиться",  "kk": "Қосылу мүмкін болмады"},

    "admin.users":         {"ru": "Пользователи",             "kk": "Қолданушылар"},
    "admin.user_new":      {"ru": "Новый пользователь",       "kk": "Жаңа қолданушы"},
    "admin.full_name":     {"ru": "ФИО",                      "kk": "Аты-жөні"},
    "admin.department":    {"ru": "Подразделение",            "kk": "Бөлім"},
    "admin.role":          {"ru": "Роль",                     "kk": "Рөл"},
    "admin.role_admin":    {"ru": "Администратор",            "kk": "Әкімші"},
    "admin.role_editor":   {"ru": "Редактор",                 "kk": "Редактор"},
    "admin.role_viewer":   {"ru": "Просмотр",                 "kk": "Қарау"},
    "admin.audit_log":     {"ru": "Журнал изменений",         "kk": "Өзгерістер журналы"},
    "admin.change_password":{"ru": "Сменить пароль",          "kk": "Құпия сөзді өзгерту"},

    "error.required_field":{"ru": "Обязательное поле",        "kk": "Міндетті өріс"},
    "error.db":            {"ru": "Ошибка базы данных",       "kk": "Деректер базасының қатесі"},
    "error.network":       {"ru": "Ошибка сети",              "kk": "Желі қатесі"},
    "error.no_permission": {"ru": "Нет прав для этого действия","kk": "Бұл әрекет үшін рұқсат жоқ"},

    "confirm.delete":      {"ru": "Вы уверены, что хотите удалить?",     "kk": "Жойғыңыз келетінін растайсыз ба?"},
    "confirm.logout":      {"ru": "Выйти из системы?",        "kk": "Жүйеден шығасыз ба?"},
    "confirm.discard":     {"ru": "Отменить несохранённые изменения?",   "kk": "Сақталмаған өзгерістерді болдырмайсыз ба?"},

    "setup.title":         {"ru": "Первоначальная настройка", "kk": "Бастапқы баптау"},
    "setup.welcome":       {"ru": "Добро пожаловать в ProfileNova", "kk": "ProfileNova-ға қош келдіңіз"},
    "setup.step_cloud":    {"ru": "Подключение к серверу",    "kk": "Серверге қосылу"},
    "setup.step_admin":    {"ru": "Учётная запись администратора", "kk": "Әкімші тіркелгісі"},
    "setup.supabase_url":  {"ru": "Supabase URL",             "kk": "Supabase URL"},
    "setup.supabase_key":  {"ru": "Supabase Anon Key",        "kk": "Supabase Anon Key"},
    "setup.db_url":        {"ru": "Database URL (postgresql://...)", "kk": "Database URL"},
    "setup.skip_cloud":    {"ru": "Пропустить (только локальный режим)", "kk": "Өткізіп жіберу (тек жергілікті)"},
    "setup.admin_username":{"ru": "Логин администратора",     "kk": "Әкімші логині"},
    "setup.admin_password":{"ru": "Пароль",                   "kk": "Құпия сөз"},
    "setup.admin_password2":{"ru": "Повторите пароль",        "kk": "Құпия сөзді қайталаңыз"},
    "setup.admin_fullname":{"ru": "ФИО",                      "kk": "Аты-жөні"},
    "setup.finish":        {"ru": "Завершить настройку",      "kk": "Баптауды аяқтау"},
    "setup.done":          {"ru": "Настройка завершена. Добро пожаловать!", "kk": "Баптау аяқталды. Қош келдіңіз!"},
}


def set_language(lang: str):
    global _current_lang
    if lang not in ("ru", "kk"):
        lang = "ru"
    _current_lang = lang
    for cb in _listeners:
        try:
            cb(lang)
        except Exception as e:
            log.error(f"i18n listener: {e}")


def get_language() -> str:
    return _current_lang


def tr(key: str, **kwargs) -> str:
    entry = _STRINGS.get(key)
    if entry is None:
        log.warning(f"i18n missing key: '{key}'")
        return key
    text = entry.get(_current_lang) or entry.get("ru") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def on_language_change(callback: Callable):
    if callback not in _listeners:
        _listeners.append(callback)


def off_language_change(callback: Callable):
    if callback in _listeners:
        _listeners.remove(callback)


def available_languages() -> list[tuple[str, str]]:
    return [("ru", "Русский"), ("kk", "Қазақша")]
