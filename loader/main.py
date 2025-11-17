import platform
import subprocess
import hashlib
import requests
import os

INFO_URL = "http://127.0.0.1:1337/client_info"
DOWNLOAD_URL = "http://127.0.0.1:1337/download_client"
SAVE_PATH = "pc_client.exe"


def compute_file_hash(path):
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_client():
    print("⏳ Получение информации о клиенте...")
    try:
        info = requests.get(INFO_URL, timeout=5).json()
    except Exception:
        print("❌ Сервер недоступен")
        return False

    if "error" in info:
        print("❌ Ошибка сервера:", info["error"])
        return False

    expected_hash = info["hash"]
    expected_size = info["size"]

    print("📄 Ожидаемый размер:", expected_size, "байт")
    print("🔐 Ожидаемый хэш:", expected_hash)

    print("⏳ Скачивание файла...")
    try:
        r = requests.get(DOWNLOAD_URL, timeout=10)
    except Exception:
        print("❌ Ошибка сетевого подключения")
        return False

    if r.status_code != 200:
        print("❌ Скачивание не удалось:", r.text)
        return False

    with open(SAVE_PATH, "wb") as f:
        f.write(r.content)

    local_size = os.path.getsize(SAVE_PATH)
    local_hash = compute_file_hash(SAVE_PATH)

    print(f"📌 Файл сохранён: {SAVE_PATH}")
    print(f"📦 Размер: {local_size} байт")
    print(f"🛡️ Хэш: {local_hash}")

    if local_size != expected_size:
        print("❌ Размер не совпадает! Файл повреждён.")
        return False

    if local_hash != expected_hash:
        print("❌ Хэш не совпадает! Файл подменён или битый.")
        return False

    print("✔️ Проверка файла пройдена")
    return True


def run_client():
    print("🚀 Запуск клиента...")
    if platform.system() == "Windows":
        subprocess.Popen([SAVE_PATH], shell=True)
    else:
        subprocess.Popen(["chmod", "+x", SAVE_PATH])
        subprocess.Popen([f"./{SAVE_PATH}"])
    print("✅ Клиент запущен.")


if __name__ == "__main__":
    if download_client():
        run_client()
