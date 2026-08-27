from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db import engine
from backend.app.middleware import jwt_middleware
from backend.app.models import Base
from backend.app.routers import (
    health_router,
    auth_router,
    chat_router,
    documents_router as document_router,
    conversations_router as conversation_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()



app = FastAPI(version="0.1.0", lifespan=lifespan)



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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)



