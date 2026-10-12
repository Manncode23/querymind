"""Consistent logging for every pipeline stage: console plus a rotating file."""
import logging
import sys
from logging.handlers import RotatingFileHandler

from src.common.config import LOGS_DIR


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:  # already configured
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOGS_DIR / "querymind.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger