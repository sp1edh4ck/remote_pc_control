import asyncio
import platform
import json
import os
import signal
import uuid

import websockets
from utils.logger import setup_logger

logger = setup_logger()

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
DEFAULT_SERVER_URL = "ws://127.0.0.1:1337/ws/"


def get_system_uuid():
    """Возвращает уникальный идентификатор системы."""
    try:
        if platform.system() == "Windows":
            import subprocess
            cmd = 'wmic csproduct get UUID'
            uuid_str = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
            if uuid_str:
                return uuid_str
        elif platform.system() == "Linux":
            with open("/etc/machine-id", "r") as f:
                return f.read().strip()
    except Exception as e:
        logger.warning(f"Не удалось получить системный UUID: {e}")
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
            await websocket.send(json.dumps({"type": "ping"}))
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            break


async def handle_server_messages(websocket):
    async for message in websocket:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.warning(f"Некорректный JSON: {message}")
            continue
        msg_type = data.get("type")
        if msg_type in ["pong", "ping"]:
            continue
        logger.info(f"Сообщение от сервера: {data}")


async def main():
    config = create_config()
    server_url = config["server_url"] + config["client_id"]
    logger.info(f'Подключаюсь к серверу {server_url}')
    while True:
        try:
            async with websockets.connect(server_url) as websocket:
                logger.info("✅ Соединение установлено с сервером")
                asyncio.create_task(heartbeat(websocket))
                await handle_server_messages(websocket)
        except Exception as e:
            logger.error(f"Соединение потеряно: {e}")
            logger.info("⏳ Переподключение через 5 секунд...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda *_: exit(0))
    asyncio.run(main())
