"""评估集指标计算（阶段一：检索层，不调 LLM）。

只回答一个问题：检索器有没有把"标准答案所在块"找出来。
指标：
  - Hit@k   : 标准块进入前 k 名召回的题目占比
  - MRR     : 标准块排名倒数均值（排越靠前越值钱）

运行入口见 evaluation/run_eval.py。
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from backend.app.config import DEFAULT_TOP_K


def normalize_text(s: str) -> str:
    """去掉全部空白字符，用于锚点与块内容的无空白比较。"""
    return re.sub(r"\s+", "", s)


def resolve_seq(
    recorded_seq: int,
    anchor: str,
    chunks: list[tuple[int, str]],
) -> int | None:
    """在块列表中查找包含锚点的块，多个命中时取序号最接近 recorded_seq 的块。"""
    needle = normalize_text(anchor)
    if not needle:
        return None

    matches = [seq for seq, content in chunks if needle in normalize_text(content)]
    if not matches:
        return None
    return min(matches, key=lambda seq: (abs(seq - recorded_seq), seq))


def build_anchor_index(
    db_path: str,
    user_id: int | None,
) -> dict[str, list[tuple[int, str]]]:
    """按文件名聚合文档块，供锚点解析使用。"""
    sql = """
        SELECT d.file_name, c.seq_no, c.content
        FROM documents AS d
        JOIN chunks AS c ON c.document_id = d.id
    """
    params: tuple[int, ...] = ()
    if user_id is not None:
        sql += " WHERE d.user_id = ?"
        params = (user_id,)
    sql += " ORDER BY d.file_name, c.seq_no"

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    index: dict[str, list[tuple[int, str]]] = {}
    for file_name, seq_no, content in rows:
        index.setdefault(str(file_name), []).append((int(seq_no), content))
    return index


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


def _resolve_annotation(
    document_name: str,
    recorded_seq: int,
    anchor: str | None,
    anchor_index: dict[str, list[tuple[int, str]]] | None,
) -> tuple[int, bool]:
    """解析单条标注的实际序号；无锚点、无索引或未命中时回退原序号。"""
    seq = int(recorded_seq or 0)
    if isinstance(anchor, str) and anchor and anchor_index is not None:
        resolved = resolve_seq(seq, anchor, anchor_index.get(document_name, []))
        if resolved is not None:
            return resolved, True
    return seq, False


def _annotations(
    q: dict,
    anchor_index: dict[str, list[tuple[int, str]]] | None = None,
) -> list[tuple[str, int]]:
    """题目的全部标准块标注：主标注 + also_documents（L3 跨文档多标注）。"""
    main_seq, _ = _resolve_annotation(
        q["document_name"], q.get("chunk_seq", 0), q.get("anchor"), anchor_index
    )
    anns = [(q["document_name"], main_seq)]
    for extra in q.get("also_documents", []):
        extra_seq, _ = _resolve_annotation(
            extra["document_name"],
            extra.get("chunk_seq", 0),
            extra.get("anchor"),
            anchor_index,
        )
        anns.append((extra["document_name"], extra_seq))
    return anns


def _expected_str(
    q: dict,
    anchor_index: dict[str, list[tuple[int, str]]] | None = None,
) -> str:
    """期望块展示串：doc[seq]，多标注用 + 连接，如 doc[3]+doc2[7]。"""
    return "+".join(f"{doc}[{seq}]" for doc, seq in _annotations(q, anchor_index))


def _find_rank(
    results: list[dict],
    q: dict,
    anchor_index: dict[str, list[tuple[int, str]]] | None = None,
) -> int | None:
    """在检索结果中查找标准块，返回其排名；未命中返回 None。

    results 为 retriever.retrieve 返回的块列表，每块含 document_name / seq_no。
    q 为评估题：主标注 document_name/chunk_seq，L3 另有 also_documents。
    命中 = 主标注命中 OR 任一 also_documents 标注命中；
    多标注时取其中最靠前的排名（MRR 按最优排名计）。
    """
    anns = _annotations(q, anchor_index)
    best: int | None = None
    for rank, r in enumerate(results):
        if (r["document_name"], r["seq_no"]) in anns and (best is None or rank < best):
            best = rank
    return best


def _has_anchor(q: dict) -> bool:
    """题目或其附加标注是否带有非空锚点。"""
    if isinstance(q.get("anchor"), str) and q["anchor"]:
        return True
    return any(
        isinstance(extra.get("anchor"), str) and extra["anchor"]
        for extra in q.get("also_documents", [])
    )


def evaluate_retrieval(
    questions: list[dict],
    top_k: int = DEFAULT_TOP_K,
    user_id: int | None = None,
    anchor_index: dict[str, list[tuple[int, str]]] | None = None,
) -> dict:
    """对每题跑一次检索，汇总 Hit@k / MRR，并附按类别(category)/难度(level)细分。

    只用题面的 question 做检索：L4 的 context 不参与检索（评估"裸问题"检索能力，
    context 留给后续 query 改写实验），仅透传到 details 供分析。
    旧题无 level 字段时按 "baseline" 统计。
    """
    # 延迟导入：retriever 的 import 链会加载 bge-m3 模型（约 2.3GB），
    # 只在真正评估时才触发，避免 import 本模块就卡住。
    from backend.app.services.retriever import retrieve

    if anchor_index is None and any(_has_anchor(q) for q in questions):
        from backend.app.config import settings

        db_path = settings.DATABASE_URL.removeprefix("sqlite+aiosqlite:///")
        anchor_index = build_anchor_index(str(Path(db_path).resolve()), user_id)

    details: list[dict] = []
    per_cat: dict[str, dict] = {}
    per_level: dict[str, dict] = {}
    hits, mrr_sum = 0, 0.0
    anchor_stats = {"total": 0, "resolved": 0, "fallback": 0}

    for q in questions:
        results = retrieve(q["question"], top_k=top_k, user_id=user_id)
        resolved_seq, anchor_resolved = _resolve_annotation(
            q["document_name"],
            q.get("chunk_seq", 0),
            q.get("anchor"),
            anchor_index,
        )
        if isinstance(q.get("anchor"), str) and q["anchor"]:
            anchor_stats["total"] += 1
            if anchor_resolved:
                anchor_stats["resolved"] += 1
            else:
                anchor_stats["fallback"] += 1

        rank = _find_rank(results, q, anchor_index)
        hit = rank is not None
        rr = 1.0 / (rank + 1) if hit else 0.0

        hits += int(hit)
        mrr_sum += rr

        details.append(
            {
                "id": q["id"],
                "question": q["question"],
                "expected": _expected_str(q, anchor_index),
                "resolved_seq": resolved_seq,
                "anchor_resolved": anchor_resolved,
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
        "anchor_stats": anchor_stats,
        "details": details,
    }
