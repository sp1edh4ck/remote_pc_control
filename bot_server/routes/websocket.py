import json
import os

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
    user = await db.user_exists(client_id)
    if not user:
        await db.add_user(client_id)
        await bot.send_message(
            config.ADMIN_ID,
            f'Новое устройство добавлено в db: <code>{client_id}</code>.'
        )
        logger.info(f'Новое устройство добавлено в db: {client_id}.')
    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            msg_type = data.get("type")
            if msg_type == "result":
                await on_client_result(client_id, data)
                continue
            logger.info(f'[{client_id}] [{data.get("type").upper()}].')
    except WebSocketDisconnect:
        logger.info(f'Пользователь {client_id} отключился.')
        connected_clients.pop(client_id, None)
