import os
import re

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_BOT_TOKEN = os.getenv("LOG_BOT_TOKEN")

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

IP = os.getenv("IP", "0.0.0.0")
_port_raw = os.getenv("PORT")
PORT = int(_port_raw) if _port_raw and _port_raw.isdigit() else 1337

_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [
    int(i.strip()) for i in re.split(r"[,\s]+", _admin_ids_raw) if i.strip().isdigit()
]

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env — добавь его перед запуском.")
