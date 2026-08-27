from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.messages import Message


# 保存会话消息
async def save_message(db: AsyncSession, conversation_id: int, role: str, content: str, citations_json: str = ""):
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        citations_json=citations_json
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


# 查询所有会话消息
async def get_all_messages(db: AsyncSession, conversation_id: int, page_size: int = 20, page: int = 1):
    query = (select(Message)
             .where(Message.conversation_id == conversation_id)
             .offset((page - 1) * page_size)
             .limit(page_size)
             .order_by(Message.created_at.asc())
             )
    messages = await db.execute(query)
    return messages.scalars().all()


# 删除所有会话消息
async def delete_all_messages(db: AsyncSession, conversation_id: int):
    await db.execute(delete(Message).where(Message.conversation_id == conversation_id))
    await db.commit()
    return None
