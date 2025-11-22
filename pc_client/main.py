import asyncio
import json
import os
import platform
import signal
import uuid
import websockets
from utils import system
from utils.logger import setup_logger

logger = setup_logger(log=True, files=False)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
DEFAULT_SERVER_URL = "ws://127.0.0.1:1337/ws/"

COMMANDS = {
    "shutdown": system.shutdown,
    "reboot": system.reboot,
    "lock": system.lock,
    "open_link": system.open_link
    # "screenshot": system.screenshot
}


def get_system_uuid():
    """Возвращает уникальный идентификатор системы."""
    try:
        sys_id = platform.node() + platform.system()
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, sys_id))
    except Exception as e:
        logger.warning(f'Ошибка генерации UUID: {e}')
        return str(uuid.uuid4())


def create_config():
    """Создаёт config.json при первом запуске и возвращает его содержимое."""
    if os.path.exists(CONFIG_PATH):
        logger.info(f'Используется существующий config: {CONFIG_PATH}')
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    client_id = get_system_uuid()
    config = {
        "client_id": client_id,
        "server_url": DEFAULT_SERVER_URL
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    logger.info(f'Создан новый config: {CONFIG_PATH}')
    logger.info(f'client_id: {client_id}')
    return config


async def heartbeat(websocket):
    """Периодический пинг для проверки соединения."""
    while True:
        try:
            await websocket.send(json.dumps({"command": "ping"}))
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f'Heartbeat error: {e}')
            break


async def handle_server_messages(websocket, config):
    async for message in websocket:
        try:
            data = json.loads(message)
            print(data)
        except json.JSONDecodeError:
            logger.warning(f'Некорректный JSON: {message}')
            continue
        cmd = data.get("command")
        if cmd in ["pong", "ping"]:
            continue
        if cmd == "result" and data.get("cmd") == "update_client_id":
            status = data.get("status")
            if status == "ok":
                try:
                    if "client_id_pending" in config:
                        config["client_id"] = config.pop("client_id_pending")
                        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                            json.dump(config, f, indent=4)
                        logger.info(f"client_id успешно обновлён локально: {config['client_id']}")
                except Exception as e:
                    logger.error(f"Ошибка при записи config.json: {e}")
            else:
                logger.warning("Сервер отказался обновлять client_id.")
            continue
        property = data.get("property")
        logger.info(f'Команда от сервера: {cmd}')
        command = COMMANDS.get(cmd)
        if command:
            try:
                if property is not None:
                    command(property)
                else:
                    command()
                logger.info(f'Команда выполнена: {cmd}')
                await websocket.send(json.dumps({"command": cmd, "status": "ok"}))
            except Exception as e:
                logger.error(f'Ошибка выполнения команды {cmd}: {e}')
                await websocket.send(json.dumps({"command": cmd, "status": "error"}))
        else:
            logger.warning(f'Неизвестная команда: {cmd}')


async def main():
    config = create_config()
    client_id = config.get("client_id")
    server_url = config["server_url"] + config["client_id"]
    logger.info(f'Подключаюсь к серверу {server_url}')
    while True:
        try:
            async with websockets.connect(server_url) as websocket:
                logger.info('Соединение с сервером установлено.')
                hb_task = asyncio.create_task(heartbeat(websocket))
                try:
                    await handle_server_messages(websocket, config)
                finally:
                    hb_task.cancel()
        except Exception as e:
            logger.error('Соединение потеряно.')
            logger.info('Переподключение через 5 секунд...')
            await asyncio.sleep(5)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda *_: exit(0))
    asyncio.run(main())
