# Same logger as other but improved...sorta
import logging
from pathlib import Path
import os
import sys
import threading

def get_logger(name: str = "app_logger") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        log_dir = Path.home() / "NonomiBeat" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = str(log_dir / "NonomiBeat.log")

        fh = logging.FileHandler(log_path, mode="a")
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(formatter)

        logger.addHandler(fh)
    return logger

default_logger = get_logger()
