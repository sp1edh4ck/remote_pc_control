"""
Отказоустойчивая версия loader:
- атомарная загрузка клиента (tmp .part)
- проверка размера / sha256
- проверка RSA-подписи метаданных (signature)
- запуск клиента в фоне, без окна (win) / setsid (unix)
- мониторинг и перезапуск клиента при падении
- одна копия loader (pidfile lock)
- автообновление loader (через /loader_info и /loader_download) — проверка ТОЛЬКО при старте
"""

import base64
import hashlib
import logging
import os
import platform
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

BASE_DIR = Path(__file__).resolve().parent
APP_NAME = "RemotePCLoader"
PIDFILE = BASE_DIR / f"{APP_NAME}.pid"

SERVER_BASE = "http://127.0.0.1:1337"
CLIENT_INFO_URL = f"{SERVER_BASE}/client_info"
CLIENT_DOWNLOAD_URL = f"{SERVER_BASE}/download_client"
LOADER_INFO_URL = f"{SERVER_BASE}/loader_info"
LOADER_DOWNLOAD_URL = f"{SERVER_BASE}/loader_download"

CLIENT_FILENAME = "pc_client.exe"
SAVE_CLIENT_PATH = str(BASE_DIR / CLIENT_FILENAME)
CLIENT_TMP_PATH = str(BASE_DIR / (CLIENT_FILENAME + ".part"))

LOADER_FILENAME = Path(sys.argv[0]).name
LOADER_TMP_NAME = LOADER_FILENAME + ".new"
LOADER_TMP_PATH = str(BASE_DIR / LOADER_TMP_NAME)

MAX_RETRIES = 5
RETRY_DELAY = 2
CHECK_INTERVAL = 30
CLIENT_MONITOR_RESTART_DELAY = 3
MIN_CLIENT_SIZE = 1024
LOADER_VERSION = "1"

PUB_KEY_PEM = b"""
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAuZqCP2cO3JliI00VO5DH
z2a/xOJBwxGnOMIYp8Jz0FGCf537JN58DM9fmFCJIrMCbyjzguYXssrcxcfpPHD8
WHFnRI9dwhm3RoC2NpXVdpYiWSeIpx76PshtoaabkbZpPoHCLYNraB/V/Q6lKBX/
mUzMzIg15UU3+8GHihR/AjL0KAZaRh1k2uEQ4Ih3SdRM4mbxkz9BWb+kO1IAP+AW
dSj9UBRXYKtjuZEJtJY1tBeQaK3bWY9c/XFIthEhZ1QVkFmmuLafpVc0Za476jM7
mKQ4Y+/8I2UVBInYqxnnInuTUHFUtt1TfUHpvAKqKV5Y5u5tEte1Poy4vDs5xsxD
HWWdGVw3bzREpTNAcheLkEUslKOSiv/uVJteaf3HA12nkBDQD5gJdRGmb1MpbfAY
bWwCweNgm6SdmCkg10BtZTL6jEpSoYsT2bb5t7rf+hijO7qDvD/Hbay4KQxseO6D
VqEJMG4vhUNljaU0NMXOpYZAlrlWgL7VKyt5URpTLxGPMUL69kg1qsCJ2F2DXF2/
YpkXOEwm4TBak6ohSswo6BC0vqul5xW71eeqO4kyTWPXuwAHadCPSQDmL5dbQv9x
JzPE8SVPcoanvNVtn/GvdUDJHvfsrhA1zdlNrKBRnwecHCfhexx7whYML2NYhBFJ
5xKJNxtbwYO17ZiLjWkC8UECAwEAAQ==
-----END PUBLIC KEY-----
"""

def setup_logger(log=True, files=True):
    logger = logging.getLogger("bot_server")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.hasHandlers():
        logger.handlers.clear()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    if log:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    if files:
        file_handler = logging.FileHandler(
            f"client_{datetime.now().strftime('%Y%m%d')}.log", encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    if not log and not files:
        logger.addHandler(logging.NullHandler())
    return logger


logger = setup_logger(log=True, files=False)


def safe_request(url, timeout=10):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            return resp
        except Exception as e:
            logger.error(f"Не удалось подключиться к {url} ({attempt}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY)
    return None


def compute_file_hash(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error(f"Ошибка вычисления хэша для {path}: {e}")
        return None


def verify_signature(pubkey_pem, data_bytes, signature_b64):
    try:
        public_key = serialization.load_pem_public_key(pubkey_pem)
        signature = base64.b64decode(signature_b64)
        public_key.verify(
            signature,
            data_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        logger.error(f"Signature verify failed: {e}")
        return False


def is_process_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
    except Exception:
        return False


def acquire_pidfile():
    try:
        if PIDFILE.exists():
            try:
                pid = int(PIDFILE.read_text().strip())
                if is_process_running(pid):
                    logger.error(f"Loader уже запущен с PID {pid}. Выход.")
                    return False
                else:
                    logger.warning("Найден старый PID файл, но процесса нет — перезаписываем.")
            except Exception:
                logger.warning("PID файл повреждён — перезаписываем.")
        PIDFILE.write_text(str(os.getpid()))
        return True
    except Exception as e:
        logger.error(f"Не удалось создать PID файл: {e}")
        return False


def release_pidfile():
    try:
        if PIDFILE.exists():
            PIDFILE.unlink()
    except Exception as e:
        logger.warning(f"Не удалось удалить PID файл: {e}")


def get_client_info():
    """Получение метаданных клиента."""
    logger.info("Получение информации о клиенте...")
    r = safe_request(CLIENT_INFO_URL)
    if not r:
        logger.error("Сервер недоступен.")
        return None
    try:
        logger.info("Информация получена.")
        info = r.json()
    except Exception as e:
        logger.error(f"Сервер вернул некорректные данные: {e}")
        return None
    if "error" in info:
        logger.error(f"Ошибка сервера: {info['error']}")
        return None
    required = {"filename", "hash", "size", "signature"}
    if not all(k in info for k in required):
        logger.error("Ответ сервера неполный (нужны filename, hash, size, signature).")
        return None
    return info


def check_client():
    """
    Проверка необходимости скачивания клиента.
    True -> нужно скачать/обновить клиент
    False -> клиент актуален или сервер недоступен и локальный файл есть
    """
    info = get_client_info()
    if not info:
        logger.warning("Проверка версии невозможна, сервер недоступен.")
        return not Path(SAVE_CLIENT_PATH).exists()
    server_hash = info["hash"]
    server_size = info["size"]
    server_sig = info.get("signature")
    if not server_sig:
        logger.error("Сервер не прислал подпись. Отказано в доступе.")
        return not Path(SAVE_CLIENT_PATH).exists()
    p = Path(SAVE_CLIENT_PATH)
    if not p.exists():
        logger.info("Клиент отсутствует, требуется скачивание.")
        return True
    try:
        local_size = p.stat().st_size
        if local_size != server_size:
            logger.info("Размер отличается, требуется обновление.")
            return True
        local_hash = compute_file_hash(str(p))
        if not local_hash:
            logger.error("Не удалось вычислить локальный хэш.")
            return True
        if local_hash != server_hash:
            logger.info("Хэш не совпадает, требуется обновление.")
            return True
        if not verify_signature(PUB_KEY_PEM, server_hash.encode(), server_sig):
            logger.error("Подпись метаданных не валидна.")
            return False
        logger.info("Локальный клиент актуален.")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке локального клиента: {e}")
        return True


def download_client():
    """Скачивание и валидация клиента (с .part и атомарной заменой)."""
    info = get_client_info()
    if not info:
        logger.error("Невозможно получить метаданные сервера.")
        return False
    server_hash = info["hash"]
    server_size = info["size"]
    server_sig = info.get("signature")
    if not server_sig:
        logger.error("Сервер не предоставил подпись. Отказано в доступе.")
        return False
    logger.info("Скачивание клиента...")
    r = safe_request(CLIENT_DOWNLOAD_URL, timeout=30)
    if not r or r.status_code != 200:
        logger.error("Не удалось скачать файл.")
        return False
    tmp_path = Path(CLIENT_TMP_PATH)
    try:
        tmp_path.write_bytes(r.content)
    except Exception as e:
        logger.error(f"Не удалось сохранить временный файл: {e}")
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False
    try:
        if not tmp_path.exists():
            logger.error("Временный файл отсутствует после записи.")
            return False
        local_size = tmp_path.stat().st_size
    except Exception as e:
        logger.error(f"Ошибка проверки размера: {e}")
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False
    if local_size < MIN_CLIENT_SIZE:
        logger.error(f"Файл слишком мал ({local_size} байт).")
        tmp_path.unlink(missing_ok=True)
        return False
    if local_size != server_size:
        logger.error(f"Размер не совпадает ({local_size} vs {server_size}). Удаляю временный файл.")
        tmp_path.unlink(missing_ok=True)
        return False
    local_hash = compute_file_hash(str(tmp_path))
    if not local_hash or local_hash != server_hash:
        logger.error("Хэш не совпадает, файл повреждён. Удаляю временный файл.")
        tmp_path.unlink(missing_ok=True)
        return False
    if not verify_signature(PUB_KEY_PEM, server_hash.encode(), server_sig):
        logger.error("Проверка цифровой подписи не пройдена! Удаляю временный файл.")
        tmp_path.unlink(missing_ok=True)
        return False
    try:
        final_path = Path(SAVE_CLIENT_PATH)
        if final_path.exists():
            bak = final_path.with_suffix(final_path.suffix + ".bak")
            try:
                if bak.exists():
                    bak.unlink()
                final_path.replace(bak)
            except Exception:
                pass
        tmp_path.replace(final_path)
    except Exception as e:
        logger.error(f"Не удалось установить новый клиент: {e}")
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False
    logger.info("Файл успешно скачан, проверен и установлен.")
    return True


class ClientRunner(threading.Thread):
    """Запуск клиента в фоне и мониторинг."""
    def __init__(self, exe_path):
        super().__init__(daemon=True)
        self.exe_path = exe_path
        self.proc = None
        self._stop = threading.Event()

    def run(self):
        logger.info("Запуск мониторинга клиента.")
        while not self._stop.is_set():
            if not Path(self.exe_path).exists():
                logger.error("Клиент отсутствует, ожидаю установки...")
                time.sleep(CHECK_INTERVAL)
                continue
            try:
                logger.info(f"Запуск клиента: {self.exe_path}")
                if platform.system() == "Windows":
                    CREATE_NO_WINDOW = 0x08000000
                    self.proc = subprocess.Popen(
                        [self.exe_path],
                        creationflags=CREATE_NO_WINDOW,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    self.proc = subprocess.Popen(
                        [self.exe_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        preexec_fn=os.setsid,
                        close_fds=True
                    )
            except Exception as e:
                logger.error(f"Не удалось запустить клиент: {e}")
                time.sleep(CLIENT_MONITOR_RESTART_DELAY)
                continue
            try:
                rc = self.proc.wait()
                logger.warning(f"Клиент завершился с кодом {rc}. Перезапуск через {CLIENT_MONITOR_RESTART_DELAY}s.")
            except Exception as e:
                logger.error(f"Ошибка ожидания клиента: {e}")
            time.sleep(CLIENT_MONITOR_RESTART_DELAY)

    def stop(self):
        self._stop.set()
        try:
            if self.proc and self.proc.poll() is None:
                logger.info("Останавливаем процесс клиента...")
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except Exception:
                    self.proc.kill()
        except Exception as e:
            logger.debug(f"Ошибка при остановке клиента: {e}")


def get_loader_info():
    """Автообновление loader (best-effort)."""
    r = safe_request(LOADER_INFO_URL)
    if not r:
        return None
    try:
        info = r.json()
        required = {"filename", "hash", "size", "signature", "version"}
        if not all(k in info for k in required):
            logger.error("Ответ /loader_info неполный.")
            return None
        return info
    except Exception as e:
        logger.error(f"Ошибка парсинга /loader_info: {e}")
        return None


def check_loader_update():
    """Проверяет, есть ли новая версия загрузчика на сервере."""
    info = get_loader_info()
    if not info:
        logger.info("Нет данных об обновлении loader.")
        return False
    server_version = info["version"]
    server_hash = info["hash"]
    if server_version == LOADER_VERSION:
        logger.info("Версия загрузчика совпадает. Дополнительно проверяю целостность.")
        local_path = Path(sys.argv[0]).resolve()
        if not local_path.exists():
            logger.warning("Файл загрузчика отсутствует. Обновляем.")
            return True
        local_hash = compute_file_hash(str(local_path))
        if not local_hash or local_hash != server_hash:
            logger.warning("Файл загрузчика поврежден или хэш не совпадает — обновляем.")
            return True
        logger.info("Loader актуален.")
        return False
    logger.info(f"Найдена новая версия загрузчика: {server_version} (локальная: {LOADER_VERSION})")
    return True


def download_loader_update():
    """
    Скачивает новый loader, проверяет hash+signature и запускает апдейтер-скрипт.
    """
    info = get_loader_info()
    if not info:
        logger.info("Нет информации об обновлении loader.")
        return False
    new_hash = info["hash"]
    new_size = info["size"]
    new_sig = info["signature"]
    new_version = info.get("version")
    logger.info(f"Обновление loader: версия {new_version}")
    r = safe_request(LOADER_DOWNLOAD_URL, timeout=30)
    if not r or r.status_code != 200:
        logger.error("Не удалось скачать новый loader.")
        return False
    tmp_path = Path(LOADER_TMP_PATH)
    try:
        tmp_path.write_bytes(r.content)
    except Exception as e:
        logger.error(f"Не удалось записать временный loader: {e}")
        tmp_path.unlink(missing_ok=True)
        return False
    try:
        size = tmp_path.stat().st_size
        if size != new_size:
            logger.error("Размер нового loader не совпадает.")
            tmp_path.unlink(missing_ok=True)
            return False
    except Exception as e:
        logger.error(f"Ошибка проверки размера: {e}")
        tmp_path.unlink(missing_ok=True)
        return False
    h = compute_file_hash(str(tmp_path))
    if not h or h != new_hash:
        logger.error("Хэш нового loader не совпадает.")
        tmp_path.unlink(missing_ok=True)
        return False
    if not verify_signature(PUB_KEY_PEM, new_hash.encode(), new_sig):
        logger.error("Проверка подписи нового loader не пройдена.")
        tmp_path.unlink(missing_ok=True)
        return False
    try:
        cur_exe = Path(sys.argv[0]).resolve()
        tmp = tmp_path.resolve()
        if platform.system() == "Windows":
            bat = BASE_DIR / "update_loader.bat"
            with open(bat, "w", encoding="utf-8") as f:
                f.write(
                    f"""
                        @echo off
                        REM Ждём завершения текущего процесса
                        :waitloop
                        tasklist /fi "PID eq {os.getpid()}" | findstr /I "{cur_exe.name}" >NUL
                        if %ERRORLEVEL%==0 (
                            timeout /T 1 /NOBREAK >NUL
                            goto waitloop
                        )
                        REM заменяем файл
                        move /Y "{tmp}" "{cur_exe}"
                        start "" "{cur_exe}"
                        del "%~f0"
                    """
                )
            subprocess.Popen([str(bat)], shell=True)
            logger.info("Updater запущен (Windows). Завершаю текущий процесс для обновления.")
            return True
        else:
            sh = BASE_DIR / "update_loader.sh"
            with open(sh, "w", encoding="utf-8") as f:
                f.write(
                    f"""
                        #!/bin/sh
                        # ждём пока текущий процесс завершится
                        while kill -0 {os.getpid()} 2>/dev/null; do
                          sleep 1
                        done
                        mv "{tmp}" "{cur_exe}"
                        chmod +x "{cur_exe}"
                        "{cur_exe}" &
                        rm -- "$0"
                    """
                )
            sh.chmod(0o755)
            subprocess.Popen(["/bin/sh", str(sh)])
            logger.info("Updater запущен (Unix). Завершаю текущий процесс для обновления.")
            return True
    except Exception as e:
        logger.error(f"Не удалось запустить updater: {e}")
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False


def main_loop():
    if not acquire_pidfile():
        return
    try:
        logger.info("Проверяем обновление loader...")
        try:
            if check_loader_update():
                logger.info("Найдена новая версия loader. Попытка загрузки и запуска апдейтера.")
                if download_loader_update():
                    # Если апдейтер успешно запущен, мы завершаем текущий процесс,
                    # апдейтер подождёт и заменит файл.
                    return
                else:
                    logger.error("Не удалось загрузить/установить обновление loader.")
        except Exception as e:
            logger.debug(f"Ошибка при ONE-TIME проверке обновления loader: {e}")
    except Exception as e:
        logger.debug(f"Неожиданная ошибка при стартовой проверке loader: {e}")

    client_runner = ClientRunner(SAVE_CLIENT_PATH)
    try:
        # CHANGED: Перед стартом мониторинга — проверяем/скачиваем клиент (как раньше)
        try:
            need_download = check_client()
            if need_download:
                ok = download_client()
                if not ok:
                    logger.error(f"Не удалось скачать клиент. Повтор через {CHECK_INTERVAL}s.")
                    time.sleep(CHECK_INTERVAL)
                    return
        except Exception as e:
            logger.error(f"Ошибка при проверке/скачивании клиента: {e}")

        client_runner.start()

        # Основной цикл теперь — только мониторинг состояния клиента и обновление клиента (не loader)
        while True:
            try:
                info = get_client_info()
                if info:
                    server_hash = info["hash"]
                    server_sig = info.get("signature")
                    # если файл существует — проверяем хэш и при несоответствии — обновляем
                    if Path(SAVE_CLIENT_PATH).exists():
                        local_hash = compute_file_hash(SAVE_CLIENT_PATH)
                        if local_hash != server_hash:
                            logger.info("Найдена новая версия клиента, обновляем.")
                            client_runner.stop()
                            client_runner.join(timeout=5)
                            if download_client():
                                client_runner = ClientRunner(SAVE_CLIENT_PATH)
                                client_runner.start()
                                logger.info("Клиент обновлён и перезапущен.")
                            else:
                                logger.error("Не удалось обновить клиента. Попытка перезапустить старую версию.")
                                client_runner = ClientRunner(SAVE_CLIENT_PATH)
                                client_runner.start()
                    else:
                        # клиент исчез — пробуем скачать и запустить
                        logger.warning("Клиент отсутствует локально — пробуем загрузить.")
                        if download_client():
                            logger.info("Клиент загружен — запускаю мониторинг.")
                            client_runner = ClientRunner(SAVE_CLIENT_PATH)
                            client_runner.start()
                        else:
                            logger.error("Не удалось загрузить клиента. Повторим позже.")
                # CHANGED: УДАЛЁН повторный вызов check_loader_update() здесь — проверяем loader ТОЛЬКО при старте
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
            time.sleep(CHECK_INTERVAL)
    finally:
        try:
            client_runner.stop()
        except Exception:
            pass
        release_pidfile()


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("Прерывание по Ctrl-C")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в loader: {e}")
    finally:
        release_pidfile()
