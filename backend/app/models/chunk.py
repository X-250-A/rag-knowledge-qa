from sqlalchemy import JSON, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models import Base


class Chunk(Base):
    __tablename__ = "chunks"

    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id"), comment="所属文档id"
    )
    content: Mapped[str] = mapped_column(Text, comment="文块内容")
    seq_no: Mapped[int] = mapped_column(Integer, comment="块序号（引用定位用）")
    char_count: Mapped[int] = mapped_column(Integer, comment="文本字符数")
    metadata_json: Mapped[dict] = mapped_column(JSON, comment="切块方法元数据，如策略/重叠字数等")
