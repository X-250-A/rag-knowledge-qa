"""预览知识库文档的 chunk_text 分块结果，输出每个 chunk 的 seq_no 与内容预览。

用法:  python evaluation/scripts/chunk_preview.py [文档路径...]
不含参数时扫描 evaluation/knowledge_base/*.md。

说明: import 后端真身 chunker.chunk_text（单一真源，2026-10-20 收口），
分块逻辑只此一份，与入库时 pipeline.build 用的完全一致，用于精确核对评估集的 chunk_seq。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # 项目根
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.chunker import chunk_text  # noqa: E402 单一真源：分块逻辑只此一份


def main():
    kb = Path(__file__).resolve().parents[1] / "knowledge_base"
    args = sys.argv[1:]
    targets = [Path(a) for a in args] if args else sorted(kb.glob("*.md"))
    for path in targets:
        print(f"\n{'=' * 70}\n文件: {path.name}\n{'=' * 70}")
        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text, 300, 50)
        for seq, c in enumerate(chunks):
            print(f"[{seq:02d}] ({len(c)}字) {c[:60].replace(chr(10), ' ')}...")
        print(f"共 {len(chunks)} 块")


if __name__ == "__main__":
    main()
