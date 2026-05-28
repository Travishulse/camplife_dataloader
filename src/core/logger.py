import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config import LOG_DIR


def setup_logger():
    """
    Configure and return the root logger for the application.
    Logs to both file (with rotation) and console (if --debug flag or env var set).
    """
    logger = logging.getLogger("camplife")
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        return logger

    log_file = os.path.join(LOG_DIR, "camplife_dataloader.log")
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    is_debug = "--debug" in sys.argv or os.environ.get("CAMPLIFE_DEBUG", "").lower() in ("1", "true", "yes")
    if is_debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
