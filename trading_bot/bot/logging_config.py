from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> Path:
    """
    Configure logging to a timestamped file under trading_bot/logs/.
    Returns the log file path.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    logs_dir = Path(__file__).resolve().parents[2] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    log_path = logs_dir / f"trading_bot_{ts}.log"

    fmt = "%(asctime)s %(levelname)s %(name)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    root.setLevel(level)

    for h in list(root.handlers):
        root.removeHandler(h)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    logging.getLogger("urllib3").setLevel(max(level, logging.WARNING))
    os.environ["TRADING_BOT_LOG_FILE"] = str(log_path)
    return log_path

