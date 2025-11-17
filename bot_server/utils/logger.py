import logging
import sys
from datetime import datetime


def setup_logger(log=False):
    logger = logging.getLogger("bot_server")
    logger.setLevel(logging.INFO)
    if not log:
        logger.addHandler(logging.NullHandler())
        return logger
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    # file_handler = logging.FileHandler(f"bot_{datetime.now().strftime('%Y%m%d')}.log", encoding="utf-8")
    # file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
