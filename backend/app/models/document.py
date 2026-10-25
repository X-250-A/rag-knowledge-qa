from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base

if TYPE_CHECKING:
    from backend.app.models.chunk import Chunk


class DocumentStatus:
    PENDING = "pending"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"


class Documents(Base):
    __tablename__ = "documents"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), comment="用户id")
    file_name: Mapped[str] = mapped_column(String, comment="文件名")
    file_type: Mapped[str] = mapped_column(String, comment="文件类型")
    file_size: Mapped[float] = mapped_column(Float, comment="文件大小")
    status: Mapped[str] = mapped_column(
        String,
        default=DocumentStatus.PENDING,
        comment="状态机：pending/parsing/chunking/embedding/ready/failed",
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, comment="向量块数量")

    # 级联删除：删文档时连带删其 chunks（ORM 层 cascade，不依赖 SQLite 外键 PRAGMA）
    chunks: Mapped[list[Chunk]] = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )
