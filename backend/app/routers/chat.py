import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.RAG_agent import RAGAgent
from backend.app.agent.conversation import ConversationManager
from backend.app.crud import (
    get_current_user,
    create_conversation,
    find_conversation_by_conversation_id,
)
from backend.app.db import get_db
from backend.app.exceptions import NotFoundError
from backend.app.models import User
from backend.app.schemas import ChatRequest


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
async def chat(
    request: ChatRequest,
    db : AsyncSession = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    if request.conversation_id is None:
        conversation = await create_conversation(db, current_user.id, request.question[:20])
        conversation_id = conversation.id
    else:
        conversation = await find_conversation_by_conversation_id(db, request.conversation_id)
        if conversation is None:
            raise NotFoundError()
        conversation_id = request.conversation_id

    conversation_manager = ConversationManager(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        title=request.question
    )



    agent = RAGAgent()

    # SSE流式聊天
    async def sse_event_generator():
        try:
            async for event in agent.handle_message(request.question, conversation_manager):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({"type": "error", "details" : str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )





