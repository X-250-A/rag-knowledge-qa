def retrieve(question: str, top_k: int = 5, user_id: int | None = None) -> list[dict]:
    """检索相关文档块，返回 prompt_builder 可直接使用的格式"""
    # 延迟导入：pipeline 会反向 import services 包，若在模块顶部导入会与
    # services/__init__ 形成循环导入；推迟到调用时才加载即可断环。
    from backend.app.rag.pipeline import query as pipeline_query

    results = pipeline_query(question, top_k, user_id=user_id)

    metadatas = results["metadatas"]
    documents = results["documents"]
    distances = results["distances"]
    if metadatas is None or documents is None or distances is None:
        return []

    chunks = []
    for i, item_id in enumerate(results["ids"][0]):
        _, seq_no = item_id.rsplit("_", 1)
        meta = metadatas[0][i]
        chunks.append(
            {
                "document_id": meta["document_id"],
                "document_name": meta["document_name"],
                "seq_no": int(seq_no),
                "content": documents[0][i],
                "score": round(1 / (1 + distances[0][i]), 2),
            }
        )

    return chunks
