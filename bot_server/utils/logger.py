import logging
import sys


def setup_logger(log=False):
    logger = logging.getLogger("bot_server")
    logger.setLevel(logging.INFO)
    if not log:
        logger.addHandler(logging.NullHandler())
        return logger
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger
