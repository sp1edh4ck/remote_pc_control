import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from bot.service import config
from bot.service.loader import bot, db, logger
from bot.utils.async_funcs import on_client_result

router = APIRouter()
connected_clients = {}


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id):
    """
    WebSocket подключение от любого клиента.
    Любой client_id разрешён.
    """
    await websocket.accept()
    connected_clients[client_id] = websocket
    logger.info(f'Пользователь {client_id} подключился.')
    try:
        user = await db.user_exists(client_id)
        if not user:
            await db.add_user(client_id)
            try:
                await bot.send_message(
                    config.ADMIN_ID,
                    f'Новое устройство добавлено в db: <code>{client_id}</code>.'
                )
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение в Telegram: {e}")
            logger.info(f'Новое устройство добавлено в db: {client_id}.')
    except Exception as e:
        logger.error(f"Ошибка работы с базой данных для {client_id}: {e}")
    try:
        while True:
            try:
                msg = await websocket.receive_text()
            except Exception as e:
                logger.warning(f"Ошибка получения сообщения от {client_id}: {e}")
                continue
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                logger.warning(f"Невалидный JSON от {client_id}: {msg}")
                continue
            msg_type = data.get("type")
            if not isinstance(msg_type, str):
                logger.warning(f"Неверный тип команды от {client_id}: {msg_type}")
                continue
            if msg_type == "result":
                await on_client_result(client_id, data)
                continue
            logger.info(f'[{client_id}] [{data.get("type").upper()}].')
    except WebSocketDisconnect:
        logger.info(f'Пользователь {client_id} отключился.')
        connected_clients.pop(client_id, None)
