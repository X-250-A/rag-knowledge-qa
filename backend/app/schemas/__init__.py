# schemas 统一出口：from backend.app.schemas import xxx
# ---- auth ----
from backend.app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
)
# ---- chat ----
from backend.app.schemas.chat import (
    ChatRequest,
    SourceChunk,
    ChatResponse,
    ChatStreamDelta,
)
# ---- document ----
from backend.app.schemas.document import (
    DocumentOut,
    DocumentListOut,
)

__all__ = [
    # auth
    "RegisterRequest", "RegisterResponse", "LoginRequest", "LoginResponse",
    # document
    "DocumentOut", "DocumentListOut",
    # chat
    "ChatRequest", "SourceChunk", "ChatResponse", "ChatStreamDelta",
]
