from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties

from bot.database.crud import Database
from bot.utils.logger import setup_logger

from . import config

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()
db = Database()
logger = setup_logger()
