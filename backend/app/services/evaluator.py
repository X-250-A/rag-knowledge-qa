"""评估集指标计算（阶段一：检索层，不调 LLM）。

只回答一个问题：检索器有没有把"标准答案所在块"找出来。
指标：
  - Hit@k   : 标准块进入前 k 名召回的题目占比
  - MRR     : 标准块排名倒数均值（排越靠前越值钱）

运行入口见 evaluation/run_eval.py。
"""

from __future__ import annotations

import json
from pathlib import Path


def load_questions(path: str | Path) -> dict:
    """读取 questions.json，返回 {meta, questions:[...]}。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"评估集不存在: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _find_rank(results: list[dict], q: dict) -> int | None:
    """在检索结果中查找标准块，返回其排名；未命中返回 None。

    results 为 retriever.retrieve 返回的块列表，每块含 document_name / seq_no。
    q 为评估题，标注了 document_name / chunk_seq。二者需同时匹配才算命中。
    """
    for rank, r in enumerate(results):
        if r["document_name"] == q["document_name"] and r["seq_no"] == q["chunk_seq"]:
            return rank
    return None


def evaluate_retrieval(questions: list[dict], top_k: int = 5, user_id: int | None = None) -> dict:
    """对每题跑一次检索，汇总 Hit@k / MRR，并附按类别(category)细分。"""
    # 延迟导入：retriever 的 import 链会加载 bge-m3 模型（约 2.3GB），
    # 只在真正评估时才触发，避免 import 本模块就卡住。
    from backend.app.services.retriever import retrieve

    details: list[dict] = []
    per_cat: dict[str, dict] = {}
    hits, mrr_sum = 0, 0.0

    for q in questions:
        results = retrieve(q["question"], top_k=top_k, user_id=user_id)
        rank = _find_rank(results, q)
        hit = rank is not None
        rr = 1.0 / (rank + 1) if hit else 0.0

        hits += int(hit)
        mrr_sum += rr

        details.append(
            {
                "id": q["id"],
                "question": q["question"],
                "expected": f"{q['document_name']}[{q['chunk_seq']}]",
                "rank": rank,  # None 表示未命中
                "hit": hit,
                "rr": rr,
            }
        )

        cat = q.get("category", "other")
        bucket = per_cat.setdefault(cat, {"total": 0, "hits": 0, "mrr": 0.0})
        bucket["total"] += 1
        bucket["hits"] += int(hit)
        bucket["mrr"] += rr

    total = len(questions)
    for b in per_cat.values():
        b["hit_rate"] = b["hits"] / b["total"]
        b["mrr"] = b["mrr"] / b["total"]

    return {
        "top_k": top_k,
        "total": total,
        "hits": hits,
        "hit_rate": hits / total if total else 0.0,
        "mrr": mrr_sum / total if total else 0.0,
        "by_category": per_cat,
        "details": details,
    }
