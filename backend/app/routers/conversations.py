from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.crud import (
    find_conversation_by_conversation_id,
    find_conversation_by_user_id,
    get_all_messages,
    get_current_user,
)
from backend.app.db import get_db
from backend.app.exceptions import ForbiddenError, NotFoundError
from backend.app.models import User
from backend.app.schemas.conversation import ConversationOut, MessageOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(get_current_user),
):
    return await find_conversation_by_user_id(db=db, user_id=current_user.id)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: int = Path(..., ge=1),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    conversation = await find_conversation_by_conversation_id(
        db=db, conversation_id=conversation_id
    )

    if conversation is None:
        raise NotFoundError()
    if conversation.user_id != current_user.id:
        raise ForbiddenError()

    return await get_all_messages(db=db, conversation_id=conversation.id)
