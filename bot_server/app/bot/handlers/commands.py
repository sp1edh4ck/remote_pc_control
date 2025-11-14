from aiogram import Router
from aiogram.filters.command import Command
from aiogram.types import Message

from app.bot.keyboards import inline_markups as kb
from app.bot.service.loader import bot
from app.routes.websocket import connected_clients
from app.bot.service.loader import db

router = Router()


@router.message(Command(commands=["s", "start"]))
async def start(message: Message):
    await bot.send_message(
        message.from_user.id,
        'Клиент-серверный бот для удалённого контроля рабочих станций.'
    )


@router.message(Command(commands=["c", "clients"]))
async def list_clients(message: Message):
    if not connected_clients:
        return await message.reply(
            '❌ Нет подключённых пользователей'
        )
    users = await db.get_users()
    if not users:
        users = ''
    await bot.send_message(
        message.from_user.id,
        f'Кол-во подключённых пользователей: <code>{len(connected_clients)}</code>.\n'
        f'Кол-во пользователей в db: <code>{len(users)}</code>.\n\n'
        f'Выберите пользователя для управления:',
        reply_markup=kb.clients(connected_clients).as_markup()
    )
