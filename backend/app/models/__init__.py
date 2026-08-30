# models 包出口：统一导出所有模型
# 每个模型类 import 的瞬间会注册进 Base.metadata，
# create_all 只建已注册的表——所以新模型必须在这里加一行。
from backend.app.models.base import Base
from backend.app.models.chunk import Chunk
from backend.app.models.conversation import Conversation
from backend.app.models.document import Documents
from backend.app.models.messages import Message
from backend.app.models.user import User

__all__ = ["Base", "User", "Documents", "Chunk", "Conversation", "Message"]
