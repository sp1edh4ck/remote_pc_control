from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties

from bot.database.crud import Database
from utils.logger import setup_logger
from . import config

logger = setup_logger(log=True, files=True)

try:
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
except Exception as e:
    logger.critical(f"Ошибка инициализации Telegram Bot: {e}")
    raise SystemExit(1)

try:
    dp = Dispatcher()
except Exception as e:
    logger.critical(f"Ошибка инициализации Dispatcher: {e}")
    raise SystemExit(1)

try:
    db = Database()
except Exception as e:
    logger.critical(f"Ошибка инициализации базы данных: {e}")
    raise SystemExit(1)

logger.info("Инициализация компонентов завершена.")
