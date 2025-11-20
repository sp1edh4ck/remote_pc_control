import logging
import sys
from datetime import datetime


def setup_logger(log=True, files=True):
    logger = logging.getLogger("pc_client")
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
