from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Chunk
from backend.app.utils import crud_log


@crud_log(action="create_chunk")
async def create_chunk(
    db: AsyncSession, document_id: int, content: str, seq_no: int, char_count: int, metadata: dict
):
    chunk = Chunk(
        document_id=document_id,
        content=content,
        seq_no=seq_no,
        char_count=char_count,
        metadata_json=metadata,
    )
    db.add(chunk)
    await db.flush()  # 生成主键，不结束事务；commit 边界在 get_db
    return chunk


async def get_chunk_by_document_id(db: AsyncSession, document_id: int):
    query = select(Chunk).where(Chunk.document_id == document_id)
    result = await db.execute(query)
    return result.scalars().all()


@crud_log(action="delete_chunk_by_document_id")
async def delete_chunk_by_document_id(db: AsyncSession, document_id: int):
    await db.execute(delete(Chunk).where(Chunk.document_id == document_id))
    return
