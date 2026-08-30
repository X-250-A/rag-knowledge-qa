from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), comment="用户id")
    title: Mapped[str] = mapped_column(String, comment="会话标题（取首次提问前20字）")
