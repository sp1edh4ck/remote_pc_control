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
            logger.warning(f'({client_id}) Невалидный json: {result_json}')
            return
        except Exception as e:
            logger.error(f'({client_id}) Ошибка при обработке json: {e}')
            return
    if not isinstance(result_json, dict):
        logger.warning(f'({client_id}) Некорректный формат данных: {result_json}')
        return
    command = result_json.get("command", "unknown")
    status = result_json.get("status", "unknown")
    message_map = {
        "ok": f'Команда "{command}" выполнена на ({client_id}).',
        "error": f'({client_id}) Ошибка выполнения "{command}".',
        "unknown": f'({client_id}) Неизвестная команда "{command}".'
    }
    message = message_map.get(status, message_map["unknown"])
    try:
        await bot.send_message(config.ADMIN_ID, message)
    except Exception as e:
        logger.error(f'Ошибка отправки сообщения администратору ({config.ADMIN_ID}): {e}')
