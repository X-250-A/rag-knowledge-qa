# evaluation/scripts/test_reranker_manual.py
# cd backend && HF_ENDPOINT=https://hf-mirror.com ../.venv/Scripts/python.exe ../evaluation/scripts/test_reranker_manual.py
from app.services.reranker import rerank

query = "哪种结构的查找性能与元素个数无关，靠层数决定"
hits = [
    {"id": "a", "content": "跳表通过多层索引加速有序链表查找，平均复杂度 O(log n)"},
    {"id": "b", "content": "Trie 树逐字符匹配，查找耗时与字符串长度相关"},
    {"id": "c", "content": "哈希表平均 O(1)，但最坏退化为 O(n)"},
]
out = rerank(query, hits, top_k=2)
assert out[0]["id"] == "a", out
assert 0.0 <= out[0]["score"] <= 1.0, out
print("RERANK-OK", [(h["id"], round(h["score"], 4)) for h in out])
