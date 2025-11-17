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
BUILD_FILE = build_settings.get("build_file")

CLIENT_PATH = str(Path(__file__).resolve().parent.parent / BUILD_DIR / BUILD_FILE)
