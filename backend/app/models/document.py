from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


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
