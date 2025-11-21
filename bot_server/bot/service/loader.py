from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties

from bot.database.crud import Database
from utils.logger import setup_logger

from . import config

logger = setup_logger(log=True, files=True)

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()
db = Database()

logger.info("Инициализация компонентов завершена.")
