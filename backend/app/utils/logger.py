"""
Logging configuration - structured logging with file + console output.
"""

import logging
import sys
from pathlib import Path

from app.config import settings


def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Ensure log directory exists
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE, encoding="utf-8"),
    ]

    logging.basicConfig(
        level=log_level,
        format=fmt,
        datefmt=date_fmt,
        handlers=handlers,
    )

    # Silence noisy libraries
    for noisy in ["httpx", "httpcore", "faiss", "urllib3"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)
