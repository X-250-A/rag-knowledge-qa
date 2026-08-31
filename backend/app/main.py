from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db import engine
from backend.app.exceptions import register_exception_handlers
from backend.app.logging_config import setup_logging
from backend.app.middleware import jwt_middleware, timing_middleware
from backend.app.models import Base
from backend.app.routers import (
    auth_router,
    chat_router,
    health_router,
)
from backend.app.routers import (
    conversations_router as conversation_router,
)
from backend.app.routers import (
    documents_router as document_router,
)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(version="0.1.0", lifespan=lifespan)
register_exception_handlers(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(auth_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(document_router, prefix="/api")
app.include_router(conversation_router, prefix="/api")


# 注意注册顺序：后添加的中间件在外层。必须把 CORSMiddleware 加在
# jwt_middleware 之后（最外层），这样浏览器的 OPTIONS 预检和 JWT 返回的
# 401/400 响应都能带上 CORS 头，否则跨域请求会 "failed to fetch"。
app.middleware("http")(jwt_middleware)
app.middleware("http")(timing_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)
