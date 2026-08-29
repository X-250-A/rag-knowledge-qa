import logging
from pathlib import Path

from backend.app.config import settings

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"  # backend/logs


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_DIR / "app.log",
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        encoding="utf-8",
    )
    # 压掉 SQLAlchemy 的 SQL 级噪音，只保留警告以上
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
