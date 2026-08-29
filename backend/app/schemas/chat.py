from pydantic import BaseModel, Field


# ---------- 请求 ----------

class ChatRequest(BaseModel):
    """用户提问"""
    question: str = Field(max_length=100, min_length=1)                         # 用户的问题
    document_ids: list[int] | None = Field(default=None)  # 指定在哪些文档范围内检索，None = 全库检索
    conversation_id: int | None = Field(default=None, ge=1)


# ---------- 响应 ----------

class SourceChunk(BaseModel):
    """引用的原文片段（告诉用户"答案来自哪段原文"）"""
    document_id: int       # 来自哪个文档
    document_name: str     # 文档名
    chunk_seq: int         # 第几块
    content: str           # 原文内容
    score: float           # 相关性得分（越高越相关）


class ChatResponse(BaseModel):
    """完整问答响应（非流式）"""
    answer: str
    sources: list[SourceChunk]


class ChatStreamDelta(BaseModel):
    """SSE 流式响应的每个片段"""
    delta: str = ""            # 本次增量文本（空串表示结束）
    sources: list[SourceChunk] | None = None  # 仅在最后一帧携带引用来源
    done: bool = False         # True = 流结束
