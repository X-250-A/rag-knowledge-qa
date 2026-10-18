"""RAG 意图分类的结构化输出模型 —— 意图清单的单一真源。

Intent 枚举 + IntentResult 模型：四类意图只在此定义一次，
prompt 类别清单、LLM 输出校验、RAG_agent 分发都从 Intent 派生，
避免「清单散落在 prompt / 白名单 / if-elif 三处」的漂移。
"""

from enum import StrEnum

from pydantic import BaseModel


class Intent(StrEnum):
    RAG_QUERY = "rag_query"
    CHITCHAT = "chitchat"
    DOCUMENT_MANAGEMENT = "document_management"
    OUT_OF_SCOPE = "out_of_scope"


class IntentResult(BaseModel):
    """LLM 意图识别输出 —— intent 字段强约束为 Intent 枚举，非法值抛 ValidationError。

    注意：IntentResult 只负责「值域校验」，JSON 语法层错误由调用方先行 json.loads
    捕获（RAG 中 JSON 坏=系统级失败归 None，值非法=语义级兜底归 unclear，两种失败
    语义必须分开，不能都吞进 ValidationError）。
    """

    intent: Intent
