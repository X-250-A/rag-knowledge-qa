from backend.app.agent.conversation import ConversationManager
from backend.app.agent.intent_classifier import IntentClassifier
from backend.app.services import LlmClient, PromptBuilder, retrieve

"""RAG核心Agent"""


class RAGAgent:
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.llm_client = LlmClient()
        self.intent_classifier = IntentClassifier()

    async def handle_message(self, user_input: str, conversation: ConversationManager):
        """保存该会话消息"""
        await conversation.add_message(role="user", content=user_input)

        """给LLM做轻量意图判断，后续再补充关键词正则匹配作为降级兜底处理"""
        intent = self.intent_classifier.keyword_intent_classifier(user_input=user_input)
        if intent is None:
            intent = await self.intent_classifier.llm_intent_classifier(
                conversation=conversation, user_input=user_input
            )

        if intent is None:
            intent = "rag_query"

        """根据意图处理消息，yield 事件供 SSE 消费"""
        if intent == "rag_query":
            chunk = retrieve(question=user_input, user_id=conversation.user_id)
            messages = self.prompt_builder.build_prompt(question=user_input, content_chunks=chunk)
            if messages is None:
                await conversation.add_message(
                    role="assistant", content="未找到相关文档，请先上传知识库文档。"
                )
                yield {"type": "delta", "text": "未找到相关文档，请先上传知识库文档。"}
                yield {"type": "done", "conversation_id": conversation.conversation_id}
                return

            # 先发检索引用，再流式出答案
            yield {"type": "retrieval", "sources": chunk}
            collected = []
            async for delta in self.llm_client.stream_chat(messages):
                collected.append(delta)
                yield {"type": "delta", "text": delta}
            await conversation.add_message(role="assistant", content="".join(collected))
            yield {"type": "done", "conversation_id": conversation.conversation_id}

        elif intent == "chitchat":
            collected = []
            async for delta in self.llm_client.stream_chat(conversation.history_cache):
                collected.append(delta)
                yield {"type": "delta", "text": delta}
            await conversation.add_message(role="assistant", content="".join(collected))
            yield {"type": "done", "conversation_id": conversation.conversation_id}

        elif intent == "document_management":
            yield {"type": "delta", "text": "请转入文档管理页处理文档相关操作"}
            yield {"type": "done", "conversation_id": conversation.conversation_id}

        else:
            yield {"type": "delta", "text": "该请求与知识库无关"}
            yield {"type": "done", "conversation_id": conversation.conversation_id}
