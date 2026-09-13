import json

from openai.types.chat import ChatCompletionMessageParam

from backend.app.agent.conversation import ConversationManager
from backend.app.config import settings
from backend.app.logging_config import logger
from backend.app.services import LlmClient, PromptBuilder


class IntentClassifier:
    def __init__(self):
        self.llm_client = LlmClient()
        self.prompt_builder = PromptBuilder()

    # LLM意图识别
    async def llm_intent_classifier(self, conversation: ConversationManager, user_input: str):
        # 构造messages存上下文
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.prompt_builder.llm_intents_classifier_prompt},
        ]

        # 查上下文
        context_hint = ""
        if conversation.conversation_id:
            context_hint += (
                f"当前存在一个进行中的会话（ID={conversation.conversation_id}）。"
                f"用户可能在延续上一轮的知识库问答，请结合会话上下文判断意图；"
                f"不要因为问题简短（如追问、代词指代）就误判为 out_of_scope。"
            )

        if context_hint != "":
            messages.append({"role": "system", "content": context_hint})

        # 注入用户输入
        messages.append({"role": "user", "content": user_input})
        try:
            response = await self.llm_client.client.chat.completions.create(
                messages=messages,
                temperature=0,
                model=settings.DEEPSEEK_MODEL,
                stream=False,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content is None:
                return None

            result = json.loads(content)
            intent = result.get("intent")
            if intent not in ("rag_query", "chitchat", "document_management", "out_of_scope"):
                return "unclear"
            return intent
        except Exception as e:
            logger.exception("LLM 意图分类失败：%s", e)
            return None

    # 关键词匹配
    def keyword_intent_classifier(self, user_input: str):
        text = user_input.strip()
        if text == "":
            return None

        query_keyword = [
            "什么是",
            "是什么",
            "怎么样",
            "如何",
            "为什么",
            "讲讲",
            "介绍一下",
            "区别",
            "怎么",
            "哪些",
            "?",
            "？",
        ]
        if any(kw in text for kw in query_keyword):
            return "rag_query"

        chichat_keyword = [
            "你好",
            "您好",
            "谢谢",
            "感谢",
            "再见",
            "拜拜",
            "早上好",
            "下午好",
            "晚上好",
            "嗨",
            "哈喽",
            "在吗",
            "哈哈",
            "嗯嗯",
        ]
        if any(kw in text for kw in chichat_keyword):
            return "chitchat"

        document_keyword = [
            "删除",
            "上传",
            "导入",
            "新建文档",
            "添加文档",
            "列出",
            "查看文档",
            "我的文档",
            "重命名",
            "清理",
            "清空",
            "文档管理",
            "更新",
            "覆盖",
        ]
        if any(kw in text for kw in document_keyword):
            return "document_management"

        # 没命中任何强信号关键词：交给 LLM 判定，不要擅自判 out_of_scope
        return None
