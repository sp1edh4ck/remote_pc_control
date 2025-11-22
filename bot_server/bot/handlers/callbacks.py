from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.keyboards import inline_markups as kb
from bot.service.loader import bot
from routes.websocket import connected_clients

router = Router()

class OpenLink(StatesGroup):
    link = State()


@router.callback_query(F.data.startswith("client_"))
async def client_menu(callback: CallbackQuery):
    client_id = callback.data.split("_", 1)[1]
    await callback.message.edit_text(
        f'ПК: {client_id}',
        reply_markup=kb.client(client_id).as_markup()
    )


@router.callback_query(F.data.startswith("cmd_"))
async def execute_command(callback: CallbackQuery):
    parts = callback.data.split("_", 2)
    cmd = parts[1]
    client_id = parts[2]
    client = connected_clients.get(client_id)
    if not client:
        return await callback.answer("ПК не подключен", show_alert=True)
    try:
        await client.send_json({"command": cmd})
        await callback.answer(f'Команда "{cmd}" отправлена на ({client_id})')
    except Exception as e:
        await callback.answer(f'Ошибка: {e}', show_alert=True)


@router.callback_query(F.data.startswith("open_link_"))
async def execute_command(callback: CallbackQuery, state: FSMContext):
    client_id = callback.data[10:]
    await state.update_data(client_id=client_id)
    await state.set_state(OpenLink.link)
    await bot.send_message(
        callback.from_user.id,
        'Введите ссылку, которую хотите открыть:'
    )


@router.message(OpenLink.link)
async def check_user_profile(message: Message, state: FSMContext):
    await state.update_data(link=message.text)
    data = await state.get_data()
    await state.clear()
    client_id = data["client_id"]
    link = data["link"]
    client = connected_clients.get(client_id)
    if not client:
        return await message.answer('ПК не подключен', show_alert=True)
    try:
        await client.send_json({"command": "open_link", "property": link})
        await message.answer(f'Команда "open_link" отправлена на ({client_id})')
    except Exception as e:
        await message.answer(f'Ошибка: {e}', show_alert=True)
