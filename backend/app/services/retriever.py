def retrieve(question: str, top_k: int = 5, user_id: int | None = None) -> list[dict]:
    """检索相关文档块，返回 prompt_builder 可直接使用的格式（混合检索：向量+BM25 RRF）"""
    from backend.app.services.hybrid_retriever import hybrid_retrieve

    return hybrid_retrieve(question, top_k, user_id=user_id)
