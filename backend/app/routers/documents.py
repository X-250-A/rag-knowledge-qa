from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from backend.app.crud import (
    create_document,
    get_documents_list,
    delete_document,
    get_document,
    get_current_user,
    update_document_status,
)
from backend.app.db import get_db
from backend.app.models import User
from backend.app.rag.pipeline import build
from backend.app.services import (
    initializing_client,
    delete_collection,
    parse_file,
)

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploads"


@router.post("/")
async def upload_documents(
    file : UploadFile = File(...),
    db : AsyncSession = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    Path(UPLOAD_DIR).mkdir(exist_ok=True)
    file_path = Path(UPLOAD_DIR) / file.filename
    with open(file_path, "wb") as f:
        f.write(await file.read())

    suffix = file_path.suffix.lstrip(".")
    documents = await create_document(db, current_user.id, file.filename, suffix, file_size=file.size)

    await update_document_status(db=db, document_id=documents.id, status="parsing")
    try:
        text = parse_file(file_path)
        await build(db=db, text=text, document_id=documents.id,
                    document_name=documents.file_name, user_id=current_user.id)
        await update_document_status(db=db, document_id=documents.id, status="ready")

        return documents
    except Exception as e:
        await update_document_status(db=db, document_id=documents.id, status="failed")
        raise e


@router.get("/")
async def list_document(
    page : int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    documents = await get_documents_list(db=db, page=page, page_size=page_size, user_id=current_user.id)
    if documents is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return documents


@router.delete("/{document_id}")
async def delete_some_document(
    document_id: int,
    db : AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    documents = await get_document(db=db, document_id=document_id)
    if documents is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await delete_document(document_id=document_id, db=db)

    client = initializing_client()
    delete_collection(client=client, document_id=document_id, user_id=current_user.id)

    (Path(UPLOAD_DIR) / documents.file_name).unlink(missing_ok=True)

    return documents