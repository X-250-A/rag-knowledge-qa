from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.crud import create_conversation, save_message
from backend.app.crud.messages import get_all_messages


# 会话状态机类的创建，负责会话上下文管理
class ConversationManager:
    def __init__(self, db: AsyncSession, user_id: int, conversation_id: int, title: str):
        self.db = db
        self.user_id = user_id
        self.history_cache: list[dict] = []
        self.conversation_id = conversation_id
        self.title = title
        self.state = "pending"

    #

    # 创建新会话
    async def create_conversation(self):
        conversation = await create_conversation(db=self.db, user_id=self.user_id, title=self.title)
        self.conversation_id = conversation.id
        return conversation

    # 追加历史消息
    async def add_history_item(self, role: str, content: str):
        message = await save_message(
            db=self.db, conversation_id=self.conversation_id, role=role, content=content
        )
        self.history_cache = [{"role": message.role, "content": message.content}]
        return message

    # 追加一条消息到会话
    async def add_message(self, role: str, content: str):
        message = await save_message(
            db=self.db, conversation_id=self.conversation_id, role=role, content=content
        )
        self.history_cache.append({"role": message.role, "content": message.content})
        return message

    # 获取历史上下文
    async def get_history_item(
        self,
        role: str,
        content: str,
        max_token: int = 10000,
        token_counter: Callable[[str], int] | None = None,
    ):
        # 获取并追加历史上下文
        messages = await get_all_messages(db=self.db, conversation_id=self.conversation_id)
        all_history = [{"role": message.role, "content": message.content} for message in messages]
        # 存入缓存，返回结果
        result = []
        current_token = 0
        # 根据max_token裁剪上下文
        for message in reversed(all_history):
            message_token = (
                token_counter(message["content"])
                if token_counter is not None
                else len(message["content"])
            )
            if message_token + current_token > max_token:
                break
            current_token += message_token
            result.insert(0, message)

        self.history_cache = all_history
        return result
