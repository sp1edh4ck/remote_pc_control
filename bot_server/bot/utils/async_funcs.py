import json

from bot.service import config
from bot.service.loader import bot, logger


async def on_client_result(client_id, result_json):
    """
    Обрабатывает результат выполнения команды клиентом и отправляет уведомление администратору.
    """
    if isinstance(result_json, str):
        try:
            result_json = json.loads(result_json)
        except json.JSONDecodeError:
            logger.warning(f"⚠ Невалидный JSON от {client_id}: {result_json}")
            return
        except Exception as e:
            logger.error(f"Ошибка при обработке JSON от {client_id}: {e}")
            return
    if not isinstance(result_json, dict):
        logger.warning(f"⚠ Некорректный формат данных от {client_id}: {result_json}")
        return
    cmd = result_json.get("cmd", "unknown")
    status = result_json.get("status", "unknown")
    message_map = {
        "ok": f"💚 Команда {cmd} выполнена на {client_id}",
        "error": f"❌ Ошибка выполнения {cmd} на {client_id}",
        "unknown": f"⚠ Неизвестная команда {cmd} от {client_id}"
    }
    msg = message_map.get(status, message_map["unknown"])
    try:
        await bot.send_message(config.ADMIN_ID, msg)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения админу ({config.ADMIN_ID}): {e}")
