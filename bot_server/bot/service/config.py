import os
import re
import sys

from dotenv import load_dotenv

try:
    load_dotenv()
except Exception as e:
    print(f"[CONFIG WARNING] Не удалось загрузить .env: {e}")


def safe_get_env(key: str, default=None):
    """Безопасное получение переменной окружения."""
    try:
        value = os.getenv(key)
        return value if value not in (None, "") else default
    except Exception:
        return default

BOT_TOKEN = safe_get_env("BOT_TOKEN")
LOG_BOT_TOKEN = safe_get_env("LOG_BOT_TOKEN")

DB_USERNAME = safe_get_env("DB_USERNAME")
DB_PASSWORD = safe_get_env("DB_PASSWORD")
DB_NAME = safe_get_env("DB_NAME")

IP = safe_get_env("IP", "0.0.0.0")

_port_raw = safe_get_env("PORT")
try:
    PORT = int(_port_raw) if _port_raw and _port_raw.isdigit() else 1337
except Exception:
    PORT = 1337

_admin_ids_raw = safe_get_env("ADMIN_IDS", "")
try:
    ADMIN_IDS = [
        int(i.strip()) for i in re.split(r"[,\s]+", _admin_ids_raw) if i.strip().isdigit()
    ]
except Exception:
    ADMIN_IDS = []

_admin_id_raw = safe_get_env("ADMIN_ID")
try:
    ADMIN_ID = int(_admin_id_raw) if _admin_id_raw and _admin_id_raw.isdigit() else None
except Exception:
    ADMIN_ID = None


def warn():
    """Просто вывод предупреждений, без остановки сервера."""
    if not BOT_TOKEN:
        print("⚠ ERROR: BOT_TOKEN не найден. Телеграм-бот работать не сможет.")
        sys.exit()
    if DB_USERNAME is None or DB_PASSWORD is None or DB_NAME is None:
        print("⚠ ERROR: Данные подключения к БД отсутствуют — работа БД невозможна.")
        sys.exit()
    if ADMIN_ID is None:
        print("⚠ ERROR: ADMIN_ID отсутствует — только ADMIN_IDS будут авторизованы.")
        sys.exit()
    if not ADMIN_IDS and ADMIN_ID is None:
        print("⚠ ERROR: Нет ни одного администратора — бот станет доступен всем!")
        sys.exit()

warn()
