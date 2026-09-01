"""一键运行评估集，打印检索层基线报告。

运行方式（在项目根目录）：
    .venv\\Scripts\\python.exe -X utf8 evaluation/run_eval.py
    .venv\\Scripts\\python.exe -X utf8 evaluation/run_eval.py --file questions_hard.json
    .venv\\Scripts\\python.exe -X utf8 evaluation/run_eval.py --file questions.json --file questions_hard.json
"""

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)  # chroma_db / .env 都用相对路径，先切到项目根

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.evaluator import evaluate_retrieval, load_questions_multi  # noqa: E402

EVAL_DIR = ROOT / "evaluation"


def resolve_paths(file_args: list[str] | None) -> list[Path]:
    """--file 可多次传入；相对路径按 evaluation/ 目录解析，绝对路径原样使用。"""
    if not file_args:
        return [EVAL_DIR / "questions.json"]
    paths = []
    for f in file_args:
        p = Path(f)
        paths.append(p if p.is_absolute() else EVAL_DIR / f)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="运行检索层评估，打印 Hit@k / MRR 报告")
    parser.add_argument(
        "--file",
        action="append",
        metavar="PATH",
        help="评估集文件，可重复传入多份合并评估；相对 evaluation/ 目录或绝对路径。默认 questions.json",
    )
    args = parser.parse_args()

    paths = resolve_paths(args.file)
    for p in paths:
        if not p.exists():
            sys.exit(f"评估集不存在: {p}")
    try:
        data = load_questions_multi(paths)
    except ValueError as e:
        sys.exit(str(e))

    questions = data["questions"]
    meta = data.get("meta", {})
    top_k = int(meta.get("top_k_default", 5))
    try:
        user_id = int(meta["eval_user"])
    except (KeyError, TypeError, ValueError):
        sys.exit("meta.eval_user 未填，请先在评估集 meta 里填入评估账号 id")

    names = ", ".join(p.name for p in paths)
    print(f"加载评估集: {names} 共 {len(questions)} 题, top_k={top_k}, user_id={user_id}")
    print("首次运行会加载 bge-m3 模型（约 2.3GB），请耐心等待...\n")

    start = time.perf_counter()
    result = evaluate_retrieval(questions, top_k=top_k, user_id=user_id)
    elapsed = time.perf_counter() - start

    print("=" * 56)
    print(f"检索层基线   文件: {names}   top_k={result['top_k']}   耗时={elapsed:.1f}s")
    print("=" * 56)
    print(f"题目总数 : {result['total']}")
    print(f"命中数   : {result['hits']}")
    print(f"Hit@{result['top_k']} : {result['hit_rate']:.3f}  ({result['hit_rate']:.1%})")
    print(f"MRR      : {result['mrr']:.3f}")

    if result["by_category"]:
        print("\n按类别:")
        for cat, b in result["by_category"].items():
            print(
                f"  {cat:<6} n={b['total']:<2} "
                f"Hit@{result['top_k']}={b['hit_rate']:.2f}  MRR={b['mrr']:.3f}"
            )

    if result["by_level"]:
        print("\n按难度(level):")
        for lvl, b in result["by_level"].items():
            print(
                f"  {lvl:<8} n={b['total']:<2} "
                f"Hit@{result['top_k']}={b['hit_rate']:.2f}  MRR={b['mrr']:.3f}"
            )

    misses = [d for d in result["details"] if not d["hit"]]
    if misses:
        print(f"\n未命中 {len(misses)} 题（标准块未进前 {top_k}）:")
        for d in misses:
            print(f"  {d['id']}  期望 {d['expected']}")
    else:
        print("\n全部命中！")


if __name__ == "__main__":
    main()
