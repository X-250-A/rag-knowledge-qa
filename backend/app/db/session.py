import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.requests import Request

from backend.app.config import settings

# 创建异步引擎
engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=10, max_overflow=10)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

logger = logging.getLogger("app")

# 创建依赖项
async def get_db(request: Request):
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
            logger.info("db committed, path=%s", request.url.path)
        except Exception as exc:
            await db.rollback()
            logger.warning("db rollback, path=%s err=%s", request.url.path, type(exc).__name__)
            raise
        finally:
            await db.close()
