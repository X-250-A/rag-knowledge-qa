import json

from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from backend.app.agent.conversation import ConversationManager
from backend.app.config import settings
from backend.app.logging_config import logger
from backend.app.schemas.intent import Intent, IntentResult
from backend.app.services import LlmClient, PromptBuilder


class IntentClassifier:
    def __init__(self):
        self.llm_client = LlmClient.get_instance()
        self.prompt_builder = PromptBuilder()

    # LLM意图识别
    async def llm_intent_classifier(self, conversation: ConversationManager, user_input: str):
        # 构造messages存上下文
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.prompt_builder.build_intents_classifier_prompt()},
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

            # 先 json.loads（JSON 语法坏=系统级失败 → None，区别于值非法），
            # 再 model_validate 校验意图值域（非法 → unclear，语义级兜底）。
            # 两种失败语义分开：RAG_agent 对 None 兜底为 rag_query，对 unclear 走 else 分支。
            result = json.loads(content)
            return IntentResult.model_validate(result).intent
        except ValidationError as e:
            logger.warning("意图值非法，归为 unclear：%s", e)
            return "unclear"
        except Exception as e:
            logger.exception("LLM 意图分类失败：%s", e)
            return None

    # 关键词匹配
    def keyword_intent_classifier(self, user_input: str):
        text = user_input.strip()
        if text == "":
            return None

        # 词表准入标准 P(命中→意图)≈1：只保留"命中即几乎确定意图"的强指向词；
        # 弱信号疑问词（怎么/如何/为什么/哪些/？）命中后分不清是查询还是操作，交给 LLM 主判。
        query_keyword = [
            "什么是",
            "是什么",
            "讲讲",
            "介绍一下",
            "区别",
        ]
        if any(kw in text for kw in query_keyword):
            return Intent.RAG_QUERY

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
            return Intent.CHITCHAT

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
            return Intent.DOCUMENT_MANAGEMENT

        # 没命中任何强信号关键词：交给 LLM 判定，不要擅自判 out_of_scope
        return None
