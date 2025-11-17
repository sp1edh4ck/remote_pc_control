from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards import inline_markups as kb
from routes.websocket import connected_clients

router = Router()


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
        return await callback.answer("❌ ПК не подключен", show_alert=True)
    try:
        await client.send_json({"type": cmd})
        await callback.answer(f"✅ Команда {cmd} отправлена на {client_id}")
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)

