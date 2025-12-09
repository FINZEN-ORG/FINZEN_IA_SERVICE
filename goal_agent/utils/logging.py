"""Logging helper."""
import logging
import os

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

def get_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    logger.setLevel(LOG_LEVEL)
    return logger
