from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings

MARKER = "change-me-to-your-key"


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
        # 空字符串校验
        for key in critical_key:
            if getattr(self, key) == "":
                raise ValueError(f"{key} is required")

        # 占位符校验
        marker = [key for key in critical_key if MARKER in getattr(self, key, "")]
        marker_key_name = "，".join(marker)
        if marker:
            raise ValueError(f"Invalid key：{marker_key_name}")
        return self

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./rag_qa.db"

    # Deepseek
    DEEPSEEK_API_KEY: str = MARKER
    BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # token与JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 60 * 24
    ALGORITHMS: list[str] = ["HS256"]
    SECRET_KEY: str = MARKER

    # https网络层超时变量
    LLM_CONNECTION_TIMEOUT: float = 10.0
    LLM_READ_TIMEOUT: float = 45.0  # 等待服务器响应的单次 read 间隔
    LLM_REQUEST_TIMEOUT: float = 90.0  # 整个 API 调用的总时长上限（传给 SDK）

    # logging配置
    LOG_LEVEL: str = "INFO"


settings = Settings()
