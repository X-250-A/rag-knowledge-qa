import asyncio
import logging
from pathlib import Path

from backend.app.crud import update_document_status
from backend.app.db import AsyncSessionLocal
from backend.app.models import DocumentStatus
from backend.app.rag.pipeline import build
from backend.app.services import parse_file

_ingest_lock = asyncio.Lock()
logger = logging.getLogger(__name__)


async def process_documents(document_id: int, user_id: int, file_path: Path):
    async with _ingest_lock:
        async with AsyncSessionLocal() as db:
            try:
                await update_document_status(
                    db=db, document_id=document_id, status=DocumentStatus.PARSING, commit=True
                )
                text = await asyncio.to_thread(parse_file, str(file_path))
                await build(
                    db=db,
                    text=text,
                    document_id=document_id,
                    document_name=file_path.name,
                    user_id=user_id,
                )
            except Exception as e:
                try:
                    await update_document_status(
                        db=db, document_id=document_id, status=DocumentStatus.FAILED, commit=True
                    )
                    file_path.unlink(missing_ok=True)
                    if file_path.exists():
                        logger.warning(f"{file_path}删除失败，可能被占用：{e}")
                except Exception as clean_err:
                    logger.error(f"失败清理自身出错: {clean_err}")
                raise e
