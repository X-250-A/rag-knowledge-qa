# routers 统一出口：from backend.app.routers import xxx_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.chat import router as chat_router
from backend.app.routers.conversations import router as conversations_router
from backend.app.routers.documents import router as documents_router
from backend.app.routers.health import router as health_router

__all__ = [
    "health_router",
    "auth_router",
    "documents_router",
    "chat_router",
    "conversations_router",
]
