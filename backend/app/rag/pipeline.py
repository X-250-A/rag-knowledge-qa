from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.crud import (
    create_chunk,
    update_document_status,
)
from backend.app.services import (
    add_collection,
    chunk_text,
    get_embedding,
    initializing_client,
    query_collection,
)


async def build(db: AsyncSession, text: str, document_id: int, document_name: str, user_id: int):
    chunks = chunk_text(text, 300, 50)
    try:
        # 开始分块
        await update_document_status(db=db, document_id=document_id, status="chunking")
        for seq_no, chunk in enumerate(chunks):
            await create_chunk(
                db=db,
                document_id=document_id,
                seq_no=seq_no,
                char_count=len(chunk),
                content=chunk,
                metadata={"strategy": "paragraph+sentence", "chunk_size": 300, "overlap": 50},
            )

        # 向量化并入库
        await update_document_status(db=db, document_id=document_id, status="embedding")
        embedding = get_embedding(chunks)
        client = initializing_client()
        add_collection(
            client,
            chunks,
            embedding,
            document_id=document_id,
            document_name=document_name,
            user_id=user_id,
        )

        await update_document_status(
            db=db,
            document_id=document_id,
            status="ready",
            chunk_count=len(chunks),
        )
        return len(chunks)

    except Exception:
        await update_document_status(db=db, document_id=document_id, status="failed")
        raise


def query(question: str, top_k: int = 5, user_id: int | None = None):
    query_vector = get_embedding([question])
    client = initializing_client()
    results = query_collection(client, query_vector, top_k, user_id=user_id)
    return results
