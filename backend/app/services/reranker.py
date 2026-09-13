"""CrossEncoder 精排层：对混合检索的召回结果重排序。

输入 pair = (query, chunk_content)，输出 sigmoid 后的 0~1 相关分。
任何失败都降级为"保持 RRF 原序"，绝不让检索整体挂掉。

本文件骨架由 Hermes 生成，核心逻辑（TODO 标注处）由用户亲手实现。
"""

import logging
import threading

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-reranker-v2-m3"

_model = None  # 模块级单例
_lock = threading.Lock()


def _get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = CrossEncoder(MODEL_NAME)
    return _model

def rerank(query: str, hits: list[dict], top_k: int) -> list[dict]:
    """对 hits（RRF 融合后的召回列表）精排，返回前 top_k。

    每个 hit 含 'content'；返回时把原 score 字段替换为 rerank 分（sigmoid 后 0~1）。
    失败时降级：返回 RRF 原序的 hits[:top_k]。
    """
    if not hits:
        return []
    try:
        model = _get_model()
    except Exception:
        logger.exception("reranker load failed, fallback to RRF order")
        return hits[:top_k]

    # TODO 2: 构造 pair 列表 [(query, hit["content"]) for hit in hits]，批量 predict
    pairs = [(query, hit["content"]) for hit in hits]
    try:
        logits = model.predict(pairs)
    except Exception:
        logger.exception("rerank predict failed, fallback to RRF order")
        return hits[:top_k]

    # 实测+官方文档确认：CrossEncoder(num_labels=1) 的 predict 默认已过 Sigmoid，
    # 输出即 0~1 相关分，这里不能再手动 sigmoid（双重 sigmoid 会把分挤到 0.5~1）
    # TODO 5: 替换 score 前把 RRF 原分存到 rrf_score，前端展示口径可回溯
    scored = []
    for hit, logit in zip(hits, logits):
        h = dict(hit)
        h["rrf_score"] = hit.get("rrf_score", hit.get("score"))  # 保留 fuse 已算的 RRF 分
        h["score"] = float(logit)
        scored.append(h)

    # TODO 4: 按新分降序排序，取前 top_k（sorted 稳定，同分保持 RRF 原序）
    scored.sort(key=lambda h: h["score"], reverse=True)
    return scored[:top_k]
