from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
    }

    @model_validator(mode="after")
    def validate_key(self):
        critical_key = [
            "SECRET_KEY",
            "DEEPSEEK_API_KEY",
        ]
        missing = [key for key in critical_key if "change-me" in getattr(self, key, "")]
        if missing:
            raise ValueError
        return self

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./rag_qa.db"

    # Deepseek
    DEEPSEEK_API_KEY: str = "change-me-to-your-key"
    BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # token与JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 60 * 24
    ALGORITHMS: list[str] = ["HS256"]
    SECRET_KEY: str = "change-me-to-your-key"

    # https网络层超时变量
    LLM_CONNECTION_TIMEOUT: float = 10.0
    LLM_READ_TIMEOUT: float = 45.0  # 等待服务器响应的单次 read 间隔
    LLM_REQUEST_TIMEOUT: float = 90.0  # 整个 API 调用的总时长上限（传给 SDK）

    # logging配置
    LOG_LEVEL: str = "INFO"


settings = Settings()
