import json

from app import settings
from backend.app.agent.conversation import ConversationManager
from backend.app.services import PromptBuilder, LlmClient, retrieve

"""RAG核心Agent"""
class RAGAgent:
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.llm_client = LlmClient()

    async def handle_message(self, user_input: str, conversation: ConversationManager):

        """保存该会话消息"""
        await conversation.add_message(role="user", content=user_input)

        """给LLM做轻量意图判断，后续再补充关键词正则匹配作为降级兜底处理"""
        intent = await self.llm_intent_classifier(conversation=conversation, user_input=user_input)

        """根据意图处理消息，yield 事件供 SSE 消费"""
        if intent == "rag_query":
            chunk = retrieve(question=user_input, user_id=conversation.user_id)
            messages = self.prompt_builder.build_prompt(question=user_input, content_chunks=chunk)
            if messages is None:
                await conversation.add_message(
                    role="assistant",
                    content="未找到相关文档，请先上传知识库文档。"
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







    # LLM意图识别
    async def llm_intent_classifier(self, conversation: ConversationManager, user_input: str):
        llm_intents_classifier_prompt = self.prompt_builder.llm_intents_classifier_prompt

        # 构造message，以准备注入llm生成回答
        message = [
            {"role" : "system", "content" : llm_intents_classifier_prompt},
        ]
        # 检查会话历史
        context_hint = ""
        if conversation.conversation_id:
            context_hint = (
                f"当前存在一个进行中的会话（ID={conversation.conversation_id}）。"
                f"用户可能在延续上一轮的知识库问答，请结合会话上下文判断意图；"
                f"不要因为问题简短（如追问、代词指代）就误判为 out_of_scope。"
            )
        # 历史存在，则注入prompt
        if context_hint:
            message.append({"role" : "system", "content" : context_hint})
        # 正常注入用户输入
        message.append({"role": "user", "content": user_input})
        # 非流式调用llm生成回答
        try:
            response = await self.llm_client.client.chat.completions.create(
                messages=message,
                temperature=0,
                stream=False,
                response_format={"type": "json_object"},
                model=settings.DEEPSEEK_MODEL
            )

            # 返回JSON格式判断结果
            result = json.loads(response.choices[0].message.content)
            intent = result.get("intent")
            if intent not in ("rag_query", "chitchat", "document_management", "out_of_scope"):
                return "unclear"
            return intent
        except Exception as e:
            print(f"[WARN] LLM 意图分类失败，回退关键词: {e}")
            return None







        



