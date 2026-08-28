# -*- coding: utf-8 -*-
"""一键运行评估集，打印检索层基线报告。

运行方式（在项目根目录）：
    .venv\\Scripts\\python.exe -X utf8 evaluation/run_eval.py
"""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)   # chroma_db / .env 都用相对路径，先切到项目根

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.evaluator import load_questions, evaluate_retrieval


def main() -> None:
    qfile = ROOT / "evaluation" / "questions.json"
    data = load_questions(qfile)
    questions = data["questions"]
    meta = data.get("meta", {})
    top_k = int(meta.get("top_k_default", 5))
    try:
        user_id = int(meta["eval_user"])
    except (KeyError, TypeError, ValueError):
        sys.exit("meta.eval_user 未填，请先在 questions.json 填入评估账号 id")

    print(f"加载评估集: {len(questions)} 题, top_k={top_k}, user_id={user_id}")
    print("首次运行会加载 bge-m3 模型（约 2.3GB），请耐心等待...\n")

    start = time.perf_counter()
    result = evaluate_retrieval(questions, top_k=top_k, user_id=user_id)
    elapsed = time.perf_counter() - start

    print("=" * 56)
    print(f"检索层基线   top_k={result['top_k']}   耗时={elapsed:.1f}s")
    print("=" * 56)
    print(f"题目总数 : {result['total']}")
    print(f"命中数   : {result['hits']}")
    print(f"Hit@{result['top_k']} : {result['hit_rate']:.3f}  ({result['hit_rate']:.1%})")
    print(f"MRR      : {result['mrr']:.3f}")

    if result["by_category"]:
        print("\n按类别:")
        for cat, b in result["by_category"].items():
            print(f"  {cat:<6} n={b['total']:<2} "
                  f"Hit@{result['top_k']}={b['hit_rate']:.2f}  MRR={b['mrr']:.3f}")

    misses = [d for d in result["details"] if not d["hit"]]
    if misses:
        print(f"\n未命中 {len(misses)} 题（标准块未进前 {top_k}）:")
        for d in misses:
            print(f"  {d['id']}  期望 {d['expected']}")
    else:
        print("\n全部命中！")


if __name__ == "__main__":
    main()
