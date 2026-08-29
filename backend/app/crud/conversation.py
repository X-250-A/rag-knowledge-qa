# 对某条会话的增删改查
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.exceptions import NotFoundError
from backend.app.models.conversation import Conversation


# 创建会话
async def create_conversation(db: AsyncSession,user_id: int, title: str):
    conversation = Conversation(
        user_id=user_id,
        title=title,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation

# 通过user_id查询用户全部会话
async def find_conversation_by_user_id(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20
):
    query = (select(Conversation)
             .where(Conversation.user_id == user_id)
             .offset((page - 1) * page_size)
             .order_by(Conversation.created_at.desc())
             .limit(page_size)
             )
    result = await db.execute(query)
    return result.scalars().all()

# 通过id查询指定会话
async def find_conversation_by_conversation_id(
        db: AsyncSession,
        conversation_id: int
):
    query = (select(Conversation).where(Conversation.id == conversation_id))
    result = await db.execute(query)
    return result.scalar_one_or_none()

# 删除指定会话
async def delete_conversation(db: AsyncSession, conversation_id: int):
    result = await find_conversation_by_conversation_id(db, conversation_id)
    if result is None:
        raise NotFoundError("Conversation not found")
    await db.delete(result)
    await db.commit()
    return result


# 删除全部会话
async def delete_all_conversations(db: AsyncSession, user_id: int):
    await db.execute(delete(Conversation).where(Conversation.user_id == user_id))
    await db.commit()
    return None




