from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.config import settings

# 创建异步引擎
engine = create_async_engine(settings.DATABASE_URL, echo=True, pool_size=10, max_overflow=10)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


# 创建依赖项
async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except:
            await db.rollback()
            raise
        finally:
            await db.close()
