import json

from bot.service import config
from bot.service.loader import bot


async def on_client_result(client_id, result_json):
    if isinstance(result_json, str):
        try:
            result_json = json.loads(result_json)
        except Exception:
            print(f"⚠ Невалидный JSON от {client_id}: {result_json}")
            return
    cmd = result_json.get("cmd")
    status = result_json.get("status")
    if status == "ok":
        await bot.send_message(config.ADMIN_ID, f"💚 Команда {cmd} выполнена на {client_id}")
    elif status == "error":
        await bot.send_message(config.ADMIN_ID, f"❌ Ошибка выполнения {cmd} на {client_id}")
    else:
        await bot.send_message(config.ADMIN_ID, f"⚠ Неизвестная команда {cmd}")
