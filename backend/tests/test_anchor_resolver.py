"""锚点序号解析的纯函数测试。"""

from backend.app.services.evaluator import normalize_text, resolve_seq


def test_resolve_seq_unique_hit():
    chunks = [
        (0, "数组使用连续内存。"),
        (1, "链表通过指针连接节点。"),
        (2, "哈希表通过散列函数映射下标。"),
    ]

    assert resolve_seq(2, "指针连接节点", chunks) == 1


def test_resolve_seq_multiple_hits_choose_nearest():
    chunks = [
        (1, "目标内容出现在第一段。"),
        (5, "目标内容出现在第五段。"),
        (9, "目标内容出现在第九段。"),
    ]

    assert resolve_seq(6, "目标内容", chunks) == 5


def test_resolve_seq_returns_none_when_anchor_missing():
    chunks = [
        (0, "数组使用连续内存。"),
        (1, "链表通过指针连接节点。"),
    ]

    assert resolve_seq(1, "完全不存在的锚点", chunks) is None


def test_resolve_seq_normalizes_whitespace_and_newlines():
    chunks = [
        (0, "前文\n\n目标   内容\t出现在这里。"),
    ]

    assert normalize_text("目标 \n 内容") == "目标内容"
    assert resolve_seq(0, "目标\n内容", chunks) == 0
