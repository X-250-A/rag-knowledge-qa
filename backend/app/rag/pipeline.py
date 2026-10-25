import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import CHUNK_OVERLAP, CHUNK_SIZE
from backend.app.crud import create_chunk, get_document, update_document_status
from backend.app.models.document import DocumentStatus
from backend.app.services import (
    add_collection,
    chunk_text,
    get_embedding,
    initializing_client,
)


async def build(db: AsyncSession, text: str, document_id: int, document_name: str, user_id: int):
    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    try:
        # 开始分块
        await update_document_status(
            db=db, document_id=document_id, status=DocumentStatus.CHUNKING, commit=True
        )
        for seq_no, chunk in enumerate(chunks):
            await create_chunk(
                db=db,
                document_id=document_id,
                seq_no=seq_no,
                char_count=len(chunk),
                content=chunk,
                metadata={
                    "strategy": "paragraph+sentence",
                    "chunk_size": CHUNK_SIZE,
                    "overlap": CHUNK_OVERLAP,
                },
            )

        # 向量化并入库
        await update_document_status(
            db=db, document_id=document_id, status=DocumentStatus.EMBEDDING, commit=True
        )
        embedding = await asyncio.to_thread(get_embedding, chunks)
        client = await asyncio.to_thread(initializing_client)
        document = await get_document(db, document_id)
        if document is None:
            raise RuntimeError("document 已被删除，中止 chroma 写入")
        await asyncio.to_thread(
            add_collection,
            client,
            chunks,
            embedding,
            document_id=document_id,
            document_name=document_name,
            user_id=user_id,
        )

        await update_document_status(
            commit=True,
            db=db,
            document_id=document_id,
            status=DocumentStatus.READY,
            chunk_count=len(chunks),
        )
        # BM25 索引是内存缓存，入库后必须失效，下次查询重建
        from backend.app.services.bm25_retriever import invalidate

        invalidate(user_id)
        return len(chunks)

    except Exception:
        await update_document_status(
            db=db, document_id=document_id, status=DocumentStatus.FAILED, commit=True
        )
        raise
