# routers 统一出口：from backend.app.routers import xxx_router
from fastapi import FastAPI

from backend.app.routers.auth import router as auth_router
from backend.app.routers.chat import router as chat_router
from backend.app.routers.conversations import router as conversations_router
from backend.app.routers.documents import router as documents_router
from backend.app.routers.health import router as health_router


def register_routers(app: FastAPI) -> None:
    """统一挂载所有路由（prefix 集中管理）"""
    app.include_router(auth_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(documents_router, prefix="/api")
    app.include_router(conversations_router, prefix="/api")


__all__ = [
    "health_router",
    "auth_router",
    "documents_router",
    "chat_router",
    "conversations_router",
    "register_routers",
]
