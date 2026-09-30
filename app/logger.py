import logging
from pathlib import Path


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "nnumber_monitor.log"


def setup_logger():
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger("nnumber_monitor")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if setup_logger() is called again
    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger