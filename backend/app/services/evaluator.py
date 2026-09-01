"""评估集指标计算（阶段一：检索层，不调 LLM）。

只回答一个问题：检索器有没有把"标准答案所在块"找出来。
指标：
  - Hit@k   : 标准块进入前 k 名召回的题目占比
  - MRR     : 标准块排名倒数均值（排越靠前越值钱）

运行入口见 evaluation/run_eval.py。
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path


def load_questions(path: str | Path) -> dict:
    """读取 questions.json，返回 {meta, questions:[...]}。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"评估集不存在: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_questions_multi(paths: Sequence[str | Path]) -> dict:
    """合并多份评估集文件，返回 {meta, questions:[...]}。

    meta 取第一份文件的；questions 按传入顺序拼接；出现重复 id 直接报错。
    """
    if not paths:
        raise ValueError("paths 不能为空")
    merged_meta: dict = {}
    questions: list[dict] = []
    seen: set[str] = set()
    for i, p in enumerate(paths):
        data = load_questions(p)
        if i == 0:
            merged_meta = data.get("meta", {})
        for q in data["questions"]:
            qid = q["id"]
            if qid in seen:
                raise ValueError(f"题目 id 重复: {qid}")
            seen.add(qid)
            questions.append(q)
    return {"meta": merged_meta, "questions": questions}


def _annotations(q: dict) -> list[tuple[str, int]]:
    """题目的全部标准块标注：主标注 + also_documents（L3 跨文档多标注）。"""
    anns = [(q["document_name"], q["chunk_seq"])]
    for extra in q.get("also_documents", []):
        anns.append((extra["document_name"], extra["chunk_seq"]))
    return anns


def _expected_str(q: dict) -> str:
    """期望块展示串：doc[seq]，多标注用 + 连接，如 doc[3]+doc2[7]。"""
    return "+".join(f"{doc}[{seq}]" for doc, seq in _annotations(q))


def _find_rank(results: list[dict], q: dict) -> int | None:
    """在检索结果中查找标准块，返回其排名；未命中返回 None。

    results 为 retriever.retrieve 返回的块列表，每块含 document_name / seq_no。
    q 为评估题：主标注 document_name/chunk_seq，L3 另有 also_documents。
    命中 = 主标注命中 OR 任一 also_documents 标注命中；
    多标注时取其中最靠前的排名（MRR 按最优排名计）。
    """
    anns = _annotations(q)
    best: int | None = None
    for rank, r in enumerate(results):
        if (r["document_name"], r["seq_no"]) in anns and (best is None or rank < best):
            best = rank
    return best


def evaluate_retrieval(questions: list[dict], top_k: int = 5, user_id: int | None = None) -> dict:
    """对每题跑一次检索，汇总 Hit@k / MRR，并附按类别(category)/难度(level)细分。

    只用题面的 question 做检索：L4 的 context 不参与检索（评估"裸问题"检索能力，
    context 留给后续 query 改写实验），仅透传到 details 供分析。
    旧题无 level 字段时按 "baseline" 统计。
    """
    # 延迟导入：retriever 的 import 链会加载 bge-m3 模型（约 2.3GB），
    # 只在真正评估时才触发，避免 import 本模块就卡住。
    from backend.app.services.retriever import retrieve

    details: list[dict] = []
    per_cat: dict[str, dict] = {}
    per_level: dict[str, dict] = {}
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
                "expected": _expected_str(q),
                "rank": rank,  # None 表示未命中
                "hit": hit,
                "rr": rr,
                "level": q.get("level", "baseline"),
                "context": q.get("context"),
            }
        )

        cat = q.get("category", "other")
        bucket = per_cat.setdefault(cat, {"total": 0, "hits": 0, "mrr": 0.0})
        bucket["total"] += 1
        bucket["hits"] += int(hit)
        bucket["mrr"] += rr

        level = q.get("level", "baseline")
        bucket = per_level.setdefault(level, {"total": 0, "hits": 0, "mrr": 0.0})
        bucket["total"] += 1
        bucket["hits"] += int(hit)
        bucket["mrr"] += rr

    total = len(questions)
    for b in (*per_cat.values(), *per_level.values()):
        b["hit_rate"] = b["hits"] / b["total"]
        b["mrr"] = b["mrr"] / b["total"]

    return {
        "top_k": top_k,
        "total": total,
        "hits": hits,
        "hit_rate": hits / total if total else 0.0,
        "mrr": mrr_sum / total if total else 0.0,
        "by_category": per_cat,
        "by_level": per_level,
        "details": details,
    }
