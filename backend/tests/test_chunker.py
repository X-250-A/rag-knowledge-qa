"""chunker 回归测试。

这三类问题是实际踩过的坑：
1) 用 split 会丢掉分隔符，旧实现还额外补「。」，原文被改写；
2) 把 ASCII 分号当句末分隔符，C++ 代码会被切碎；
3) 单个分句超过 chunk_size 时，旧实现先 append 空串，产生空 chunk。
"""

from backend.app.config import CHUNK_OVERLAP, CHUNK_SIZE
from backend.app.services.chunker import chunk_text

# 句末标点集合：必须与 chunker.py 的切句正则 (?<=[？。！；．]) 保持同步
TERMINATORS = ("。", "！", "？", "；", "．")


def test_punctuation_is_preserved():
    """切分不能删除或替换原文标点（含 OI Wiki 使用的 U+FF0E「．」）。"""
    text = (
        "前缀和是一种预处理技巧，用于快速求区间和？"
        "做法！先累加得到 pre 数组；查询时用 pre[r] - pre[l-1]．"
        "注意——下标从 1 开始．"
    ) * 12

    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    joined = "".join(chunks)

    for p in "？！；．":
        assert joined.count(p) >= text.count(p), f"标点 {p} 被删除"
    # 原文没有「。」，输出也不该凭空出现旧实现补的句号
    assert "。" not in joined


def test_ascii_semicolon_is_not_a_sentence_boundary():
    """ASCII ';' 是代码语法，不是中文句子边界，不能丢也不能当切分点。"""
    code = "int main() {\n    int a = 1;\n    int b = 2;\n    return a + b;\n}\n" * 20

    chunks = chunk_text(code, CHUNK_SIZE, CHUNK_OVERLAP)
    joined = "".join(chunks)

    assert joined.count(";") >= code.count(";"), "代码分号被删除"


def test_no_empty_chunks():
    """单个分句超过 chunk_size 时不能产生空 chunk。"""
    text = "前言：" + "超长句" * 200

    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)

    assert chunks, "不应返回空列表"
    assert all(c.strip() for c in chunks), "出现了空 chunk"


def test_prose_chunks_end_at_sentence_boundary():
    """正文块必须落在句末标点上，不能从句子中间截断收尾。"""
    text = "第一句话．第二句话？第三句话！第四句话；" * 20

    chunks = [c for c in chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP) if c.strip()]

    for c in chunks:
        assert c.endswith(TERMINATORS), f"块结尾不是句末标点: {c[-20:]!r}"
