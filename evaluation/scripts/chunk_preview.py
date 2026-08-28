# -*- coding: utf-8 -*-
"""预览知识库文档的 chunk_text 分块结果，输出每个 chunk 的 seq_no 与内容预览。

用法:  python evaluation/scripts/chunk_preview.py [文档路径...]
不含参数时扫描 evaluation/knowledge_base/*.md。

说明: 内联复制 backend/app/services/chunker.py 的 chunk_text（纯函数），
与入库时 pipeline.build 用到的分块逻辑完全一致，用于精确核对评估集的 chunk_seq。
"""
import sys
from pathlib import Path


def chunk_text(text: str, chunk_size: int, overlap: int = 50) -> list:
    paragraphs = text.split("\n\n")
    chunks = []
    chunk = ""
    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            chunks.append(paragraph)
        else:
            sentences = paragraph.split("。")
            sentences = [s + "。" for s in sentences if s]
            for sentence in sentences:
                if len(chunk) + len(sentence) >= chunk_size:
                    chunks.append(chunk)
                    chunk = chunk[-overlap:]
                chunk += sentence
            if chunk:
                chunks.append(chunk)
    return chunks


def main():
    kb = Path(__file__).resolve().parents[1] / "knowledge_base"
    args = sys.argv[1:]
    targets = [Path(a) for a in args] if args else sorted(kb.glob("*.md"))
    for path in targets:
        print(f"\n{'='*70}\n文件: {path.name}\n{'='*70}")
        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text, 300, 50)
        for seq, c in enumerate(chunks):
            print(f"[{seq:02d}] ({len(c)}字) {c[:60].replace(chr(10),' ')}...")
        print(f"共 {len(chunks)} 块")


if __name__ == "__main__":
    main()
