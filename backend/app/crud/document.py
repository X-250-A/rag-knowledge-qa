from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Documents


# 创建新文件
async def create_document(
    db: AsyncSession, user_id: int, file_name: str, file_type: str, file_size: float
):
    document = Documents(
        user_id=user_id,
        file_name=file_name,
        file_type=file_type,
        file_size=file_size,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


# 查询单个文件
async def get_document(db: AsyncSession, document_id: int, user_id: int | None = None):
    query = select(Documents).where(Documents.id == document_id)
    if user_id is not None:
        query = query.where(Documents.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def find_document_by_file_name(db: AsyncSession, file_name: str, user_id: int | None = None):
    query = select(Documents).where(Documents.file_name == file_name)
    if user_id is not None:
        query = query.where(Documents.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# 查询当前用户的文件列表
async def get_documents_list(
    db: AsyncSession, user_id: int, page: int, page_size: int, limit: int = 100
):
    query = (
        select(Documents)
        .where(Documents.user_id == user_id)
        .order_by(Documents.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


# 更新当前文件
async def update_document(db: AsyncSession, document_id: int, document: Documents):
    document_to_update = await get_document(db, document_id)
    if document_to_update is None:
        return None

    if document.file_name is not None:
        document_to_update.file_name = document.file_name
    if document.file_type is not None:
        document_to_update.file_type = document.file_type
    if document.file_size is not None:
        document_to_update.file_size = document.file_size
    if document.chunk_count is not None:
        document_to_update.chunk_count = document.chunk_count
    if document.status is not None:
        document_to_update.status = document.status

    await db.commit()
    await db.refresh(document_to_update)
    return document_to_update


# 删除指定文件
async def delete_document(db: AsyncSession, document_id: int):
    document_to_delete = await get_document(db, document_id)
    if document_to_delete is None:
        return None
    await db.delete(document_to_delete)
    await db.commit()
    return document_to_delete


# 删除当前用户指定数量文件
async def delete_documents_list(
    db: AsyncSession, user_id: int, page: int, page_size: int, limit: int
):
    documents = (
        select(Documents)
        .where(Documents.user_id == user_id)
        .order_by(Documents.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(limit)
    )
    await db.delete(documents)
    await db.commit()
    return documents


# 更新文件状态
async def update_document_status(
    db: AsyncSession,
    document_id: int,
    *,
    status: str | None = None,
    chunk_count: int | None = None,
):
    document_to_update = await get_document(db, document_id)
    if document_to_update is None:
        return None
    if chunk_count is not None:
        document_to_update.chunk_count = chunk_count
    if status is not None:
        document_to_update.status = status

    db.add(document_to_update)
    await db.commit()
    await db.refresh(document_to_update)
    return document_to_update
