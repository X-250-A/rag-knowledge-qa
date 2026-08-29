import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.crud import (
    create_document,
    delete_document,
    find_document_by_file_name,
    get_current_user,
    get_document,
    get_documents_list,
    update_document_status,
)
from backend.app.db import get_db
from backend.app.exceptions import ConflictError, NotFoundError
from backend.app.models import User
from backend.app.rag.pipeline import build
from backend.app.services import (
    delete_collection,
    initializing_client,
    parse_file,
)

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"


@router.post("/")
async def upload_documents(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    Path(UPLOAD_DIR).mkdir(exist_ok=True)
    file_path = Path(UPLOAD_DIR) / file.filename
    existing = await find_document_by_file_name(
        db=db, file_name=file.filename, user_id=current_user.id
    )
    if existing:
        raise ConflictError("Document already exists")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    suffix = file_path.suffix.lstrip(".")
    documents = await create_document(
        db, current_user.id, file.filename, suffix, file_size=file.size
    )

    await update_document_status(db=db, document_id=documents.id, status="parsing")
    try:
        text = parse_file(file_path)
        await build(
            db=db,
            text=text,
            document_id=documents.id,
            document_name=documents.file_name,
            user_id=current_user.id,
        )
        await update_document_status(db=db, document_id=documents.id, status="ready")

        return documents
    except Exception as e:
        await update_document_status(db=db, document_id=documents.id, status="failed")
        raise e


@router.get("/")
async def list_document(
    page: int = Query(ge=1, default=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = await get_documents_list(
        db=db, page=page, page_size=page_size, user_id=current_user.id
    )
    if documents is None:
        raise NotFoundError()
    return documents


@router.delete("/{document_id}")
async def delete_some_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = await get_document(db=db, document_id=document_id, user_id=current_user.id)
    if documents is None:
        raise NotFoundError()
    file_name = documents.file_name
    file_path = Path(UPLOAD_DIR) / file_name

    # 清除数据库数据
    await delete_document(document_id=document_id, db=db)

    # 清除向量库数据
    try:
        client = initializing_client()
        delete_collection(client=client, document_id=document_id, user_id=current_user.id)
    except Exception as e:
        logger.error(f"清除向量库失败: {e}")

    # 清除磁盘文件
    try:
        file_path.unlink(missing_ok=True)
        if file_path.exists():
            logger.warning(f"磁盘文件删除后仍存在，可能被占用: {file_path}")
    except Exception as e:
        logger.error(f"删除磁盘文件失败: {file_path} -> {e}")

    return {"message": f"Document {file_name} deleted"}
