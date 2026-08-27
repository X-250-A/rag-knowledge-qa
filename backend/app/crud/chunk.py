from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.app.models import Chunk


async def create_chunk(
    db: AsyncSession,
    document_id: int,
    content: str,
    seq_no: int,
    char_count: int,
    metadata: dict
):
    chunk = Chunk(
        document_id=document_id,
        content=content,
        seq_no=seq_no,
        char_count=char_count,
        metadata_json=metadata
    )
    db.add(chunk)
    await db.commit()
    await db.refresh(chunk)
    return chunk


async def get_chunk_by_document_id(
    db: AsyncSession,
    document_id: int
):
    query = select(Chunk).where(Chunk.document_id == document_id)
    result = await db.execute(query)
    return result.scalars().all()

async def delete_chunk_by_document_id(
    db: AsyncSession,
    document_id: int
):
    await db.execute(
        delete(Chunk).where(Chunk.document_id == document_id)
    )
    await db.commit()
    return