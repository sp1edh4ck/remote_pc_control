import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

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
    logger.info(f'({client_id}) Пользователь подключился.')
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
                logger.warning(f'Не удалось отправить сообщение в Telegram: {e}')
            logger.info(f'Новое устройство добавлено в db: {client_id}.')
    except Exception as e:
        logger.error(f'({client_id}) Ошибка работы с базой данных: {e}')
    try:
        while True:
            try:
                message = await websocket.receive_text()
            except (WebSocketDisconnect, ConnectionClosedOK, ConnectionClosedError):
                raise WebSocketDisconnect()
            except Exception as e:
                logger.warning(f'({client_id}) Ошибка получения сообщения: {e}')
                break
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                logger.warning(f'({client_id}) Невалидный json: {message}')
                continue
            command = data.get("command")
            status = data.get("status")
            if status == "ok":
                try:
                    await on_client_result(client_id, data)
                except Exception as e:
                    logger.error(f'({client_id}) Ошибка обработки результата: {e}')
                continue
            # ! Тут пишем код под разные команды
            logger.info(f'({client_id}) {command}.')
    except WebSocketDisconnect:
        logger.info(f'Пользователь {client_id} отключился.')
    except Exception as e:
        logger.error(f'({client_id}) Непредвиденная ошибка websocket: {e}')
    finally:
        connected_clients.pop(client_id, None)
