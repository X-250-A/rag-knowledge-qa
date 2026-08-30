from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Message(Base):
    __tablename__ = "messages"

    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id"), comment="关联的会话id"
    )
    role: Mapped[str] = mapped_column(String, comment="角色：user / assistant")
    content: Mapped[str] = mapped_column(Text, comment="消息内容")
    citations_json: Mapped[str] = mapped_column(
        Text, default="", comment="引用列表JSON（assistant消息用）"
    )
