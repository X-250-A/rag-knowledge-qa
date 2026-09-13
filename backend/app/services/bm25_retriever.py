import logging
import jieba

jieba.setLogLevel(logging.WARNING)
from rank_bm25 import BM25Okapi

from backend.app.services import initializing_client

# 模块加载时预载 jieba 词典，避免首次查询卡顿
jieba.initialize()

# ---------------- 分词管线（建索引和查询必须共用同一套） ----------------

# 常见中文停用词，够用即可，不用追求完备
STOPWORDS = {
    "的",
    "了",
    "是",
    "在",
    "和",
    "与",
    "或",
    "有",
    "什么",
    "怎么",
    "如何",
    "为什么",
    "哪个",
    "哪些",
    "这个",
    "那个",
    "它",
    "他",
    "她",
    "吗",
    "呢",
    "吧",
    "啊",
    "的",
    "一",
    "不",
    "没有",
}

_cache: dict[int, dict] = {}


def tokenize(text: str) -> list[str]:
    tokens = jieba.lcut(text)
    result = []
    for token in tokens:
        token = token.strip().lower()
        if token in STOPWORDS:
            continue
        elif token == "":
            continue
        elif not token.isalnum():
            continue
        else:
            result.append(token)
    return result


def load_corpus(client, user_id: int) -> list[dict]:
    collection = client.get_or_create_collection("documents")
    data = collection.get(where={"user_id": user_id}, include=["documents", "metadatas"])
    chunks = [
        {"id": i, "content": d, "metadata": m}
        for i, d, m in zip(data["ids"], data["documents"], data["metadatas"])
    ]
    return chunks


def _build_index(chunks: list[dict]):
    corpus = [tokenize(chunk["content"]) for chunk in chunks]
    return BM25Okapi(corpus)


def get_bm25(user_id: int):
    cached = _cache.get(user_id)
    if cached:
        return cached

    client = initializing_client()
    chunks = load_corpus(client, user_id)
    if not chunks:
        return None
    index = _build_index(chunks)
    _cache[user_id] = {"bm25": index, "chunks": chunks}
    return _cache[user_id]


def invalidate(user_id: int) -> None:
    _cache.pop(user_id, None)
