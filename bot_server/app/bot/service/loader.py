from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties

from . import config

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()
