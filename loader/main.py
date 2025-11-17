import hashlib
import logging
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

SERVER_INFO_URL = "http://127.0.0.1:1337/client_info"
SERVER_DOWNLOAD_URL = "http://127.0.0.1:1337/download_client"
SAVE_PATH = "pc_client.exe"
MAX_RETRIES = 5


def setup_logger(log=False):
    logger = logging.getLogger("loader")
    logger.setLevel(logging.INFO)
    if not log:
        logger.addHandler(logging.NullHandler())
        return logger
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(f"client_{datetime.now().strftime('%Y%m%d')}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger(True)


def compute_file_hash(path):
    try:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f'Ошибка вычисления хэша: {e}')
        return None


def safe_request(url):
    """Безопасный запрос с повторными попытками."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return requests.get(url, timeout=5)
        except Exception as e:
            logger.error(f'Не удалось подключиться ({attempt}/{MAX_RETRIES}) — {e}')
            time.sleep(2)
    return None


def get_client_info():
    logger.info('Получение информации о клиенте...')
    r = safe_request(SERVER_INFO_URL)
    if not r:
        logger.error('Сервер недоступен.')
        return None
    try:
        info = r.json()
    except Exception:
        logger.error('Сервер вернул некорректные данные.')
        return None
    if "error" in info:
        logger.error(f'Ошибка сервера: {info["error"]}')
        return None
    required = {"filename", "hash", "size"}
    if not all(k in info for k in required):
        logger.error('Ответ сервера неполный.')
        return None
    return info


def download_client():
    info = get_client_info()
    if not info:
        return False
    server_hash = info["hash"]
    server_size = info["size"]
    logger.info('Скачивание клиента...')
    r = safe_request(SERVER_DOWNLOAD_URL)
    if not r or r.status_code != 200:
        logger.error('Не удалось скачать файл.')
        return False
    try:
        with open(SAVE_PATH, "wb") as f:
            f.write(r.content)
    except Exception as e:
        logger.error(f'Не удалось сохранить файл: {e}')
        return False
    local_size = os.path.getsize(SAVE_PATH)
    if local_size != server_size:
        logger.error(f'Размер не совпадает ({local_size} vs {server_size}).')
        return False
    local_hash = compute_file_hash(SAVE_PATH)
    if not local_hash or local_hash != server_hash:
        logger.error('Хэш не совпадает — файл повреждён или изменён.')
        return False
    logger.info('Файл успешно скачан и проверен.')
    return True


def run_client():
    logger.info('Запуск клиента...')
    try:
        system = platform.system()
        file = Path(SAVE_PATH).resolve()
        if not file.exists():
            logger.error('Файл не найден — запуск невозможен.')
            return
        if system == "Windows":
            subprocess.Popen([str(file)], shell=True)
        logger.info('Клиент запущен.')
    except Exception as e:
        logger.error(f'Ошибка запуска клиента: {e}')

if __name__ == "__main__":
    while True:
        if download_client():
            run_client()
            break
        else:
            logger.error('Повторная попытка через 30 секунд...')
        time.sleep(30)