"""
Centralised logging configuration.

Call setup_logging() once at application startup (in main.py).
Every module then does:

    import logging
    logger = logging.getLogger(__name__)
"""

import logging
import logging.handlers
import sys
from pathlib import Path

_LOG_DIR = Path("logs")


def setup_logging(debug: bool = False) -> None:
    _LOG_DIR.mkdir(exist_ok=True)

    console_level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(console_level)
    console.setFormatter(formatter)

    # Always write DEBUG+ to file so crashes are captured even in production
    file_handler = logging.handlers.RotatingFileHandler(
        _LOG_DIR / "pipeline.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialised — console=%s  file=logs/pipeline.log",
        logging.getLevelName(console_level),
    )
