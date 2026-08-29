# schemas 统一出口：from backend.app.schemas import xxx
# ---- auth ----
from backend.app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)

# ---- chat ----
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatStreamDelta,
    SourceChunk,
)

# ---- document ----
from backend.app.schemas.document import (
    DocumentListOut,
    DocumentOut,
)

__all__ = [
    # auth
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest",
    "LoginResponse",
    # document
    "DocumentOut",
    "DocumentListOut",
    # chat
    "ChatRequest",
    "SourceChunk",
    "ChatResponse",
    "ChatStreamDelta",
]
