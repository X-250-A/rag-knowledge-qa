"""混合检索：向量(bge-m3) + BM25 双路召回 → RRF 融合

两路各自召回 20 条，RRF(k=60) 融合后取 top_k。
RRF 只用排名不用分数，天然免去两路分数的归一化问题：
    score(doc) = sum( 1 / (k + rank_i) )   rank 从 1 起
"""

from backend.app.services import initializing_client
from backend.app.services.bm25_retriever import get_bm25, tokenize
from backend.app.services.embedding import get_embedding
from backend.app.services.vector_store import query_collection
from backend.app.services.reranker import rerank

RRF_K = 60
RECALL_PER_PATH = 20


def _rrf_fuse(vec_hits: list[dict], bm25_hits: list[dict]) -> list[dict]:
    """两路有序命中列表按 chroma ID 聚合 RRF 分数，返回全量候选（不截断，截断交给 rerank）。

    每个元素含 'id'（chroma ID）、'content'、'metadata'。
    """
    scores: dict[str, float] = {}
    first_seen: dict[str, dict] = {}  # id -> 该 chunk 信息（两路同 chunk 不互相覆盖）

    for rank, hit in enumerate(vec_hits, start=1):
        cid = hit["id"]
        scores[cid] = scores.get(cid, 0.0) + 1 / (RRF_K + rank)
        first_seen.setdefault(cid, hit)

    for rank, hit in enumerate(bm25_hits, start=1):
        cid = hit["id"]
        scores[cid] = scores.get(cid, 0.0) + 1 / (RRF_K + rank)
        first_seen.setdefault(cid, hit)

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [first_seen[cid] | {"rrf_score": s} for cid, s in ranked]


def _vector_recall(question: str, user_id: int | None) -> list[dict]:
    embedding = get_embedding([question])
    client = initializing_client()
    results = query_collection(client, embedding, RECALL_PER_PATH, user_id=user_id)
    ids = (results or {}).get("ids")
    if not ids or not ids[0]:
        return []
    docs = results["documents"] or [[]]
    metas = results["metadatas"] or [[]]
    return [
        {"id": cid, "content": doc, "metadata": meta}
        for cid, doc, meta in zip(ids[0], docs[0], metas[0])
    ]


def _bm25_recall(question: str, user_id: int | None) -> list[dict]:
    if user_id is None:
        return []
    cached = get_bm25(user_id)
    if not cached:
        return []
    bm25_index, chunks = cached["bm25"], cached["chunks"]
    scores = bm25_index.get_scores(tokenize(question))
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    order = [i for i in order if scores[i] > 0][:RECALL_PER_PATH]
    return [
        {"id": chunks[i]["id"], "content": chunks[i]["content"], "metadata": chunks[i]["metadata"]}
        for i in order
    ]


def hybrid_retrieve(question: str, top_k: int = 5, user_id: int | None = None) -> list[dict]:
    """混合检索，输出契约与原 retrieve() 一致。"""
    vec_hits = _vector_recall(question, user_id)
    bm25_hits = _bm25_recall(question, user_id)

    # BM25 路不可用（无文档/无命中）时退化为纯向量路，保持接口始终可用；
    # 两条路径都汇合到同一个 rerank，统一精排+截断
    fused = _rrf_fuse(vec_hits, bm25_hits) if bm25_hits else vec_hits

    hits = rerank(top_k=top_k, query=question, hits=fused)

    results = []
    for hit in hits:
        meta = hit["metadata"]
        _, seq_no = hit["id"].rsplit("_", 1)
        results.append(
            {
                "document_id": meta["document_id"],
                "document_name": meta["document_name"],
                "seq_no": int(seq_no),
                "content": hit["content"],
                "score": round(hit["score"], 4),  # rerank 分（0~1）
                "rrf_score": round(hit["rrf_score"], 6) if hit.get("rrf_score") is not None else None,  # RRF 原分，评估回溯用（纯向量退化路径可能没有）
            }
        )
    return results
