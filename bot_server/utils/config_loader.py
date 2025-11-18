import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "settings.json"

def load_settings():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

settings = load_settings()

build_settings = settings.get("build")
BUILD_DIR = build_settings.get("build_dir")
BUILD_CLIENT_FILE = build_settings.get("build_client_file")
BUILD_LOADER_FILE = build_settings.get("build_loader_file")

CLIENT_PATH = str(Path(__file__).resolve().parent.parent / BUILD_DIR / BUILD_CLIENT_FILE)
LOADER_PATH = str(Path(__file__).resolve().parent.parent / BUILD_DIR / BUILD_LOADER_FILE)

BASE_DIR = Path(__file__).resolve().parents[1]
SIGN_PRIV_PATH = BASE_DIR / "sign_priv.pem"

LOADER_VERSION = "1.0.1"
