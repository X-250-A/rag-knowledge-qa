from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from backend.app.crud import (
    get_current_user,
    find_conversation_by_user_id,
    find_conversation_by_conversation_id,
    get_all_messages,
)
from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas.conversation import ConversationOut, MessageOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await find_conversation_by_user_id(
        db=db,
        user_id=current_user.id
    )

@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: int,
    current_user = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)
):
    conversation = await find_conversation_by_conversation_id(
        db=db,
        conversation_id=conversation_id
    )

    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return await get_all_messages(
        db=db,
        conversation_id=conversation.id
    )

