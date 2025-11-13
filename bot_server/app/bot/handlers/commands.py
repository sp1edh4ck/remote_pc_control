from aiogram import F, Router
from aiogram.filters.command import Command
from aiogram.types import Message
from app.bot.service.loader import bot
from app.routes.websocket import connected_clients
from app.bot.keyboards import inline_markups as kb

router = Router()


@router.message(Command(commands=["s", "start"]))
async def start(message: Message):
    await bot.send_message(
        message.from_user.id,
        'Ку'
    )


@router.message(Command(commands=["c", "clients"]))
async def list_clients(message: Message):
    if not connected_clients:
        return await message.reply(
            '❌ Нет подключённых ПК'
        )
    await bot.send_message(
        message.from_user.id,
        'Выберите ПК:',
        reply_markup=kb.clients(connected_clients).as_markup()
    )
