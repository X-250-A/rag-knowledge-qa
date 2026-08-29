from datetime import datetime

from pydantic import BaseModel


class ConversationOut(BaseModel):
    """会话列表里的一条"""

    id: int
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    """会话里的一条消息"""

    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
