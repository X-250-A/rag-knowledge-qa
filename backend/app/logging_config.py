import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.app.config import settings

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"  # backend/logs
logger = logging.getLogger("app")
FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

NOISY_LOGGERS = {
    "httpx": logging.WARNING,
    "sqlalchemy.engine": logging.WARNING,
}

_configured = False # 幂等

def setup_logging():
    global _configured
    if _configured:
        return


    LOG_DIR.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    formatter = logging.Formatter(FORMAT)

    # 文件出口：轮转（单文件无限涨=运维缺口）
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=5 * 1024 * 1024,  # 5MB 一份
        backupCount=3,  # 生成 app.log.1/.2/.3
        encoding="utf-8",
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)

    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    for name, lv in NOISY_LOGGERS.items():
        logging.getLogger(name).setLevel(lv)
    _configured = True

