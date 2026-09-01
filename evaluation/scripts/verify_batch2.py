import importlib.util
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("chunker", root / "backend/app/services/chunker.py")
assert spec is not None and spec.loader is not None
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cache = {}


def chunks_of(f):
    if f not in cache:
        cache[f] = m.chunk_text(
            (root / "evaluation/knowledge_base" / f).read_text(encoding="utf-8"), 300, 50
        )
    return cache[f]


hard = json.load(open(root / "evaluation/questions_hard.json", encoding="utf-8"))["questions"]
collo = json.load(open(root / "evaluation/questions_colloquial.json", encoding="utf-8"))[
    "questions"
]
base = json.load(open(root / "evaluation/questions.json", encoding="utf-8"))["questions"]
all_old = {q["id"]: q for q in hard if not q["id"].startswith("X")}
all_old.update({q["id"]: q for q in base})
all_old.update({q["id"]: q for q in collo})
news = [q for q in hard if q["id"].startswith("X")]
print(f"新题 {len(news)} 道")
print("== X 题 chunk 标注核对 ==")
probs = []
for q in news:
    cs = chunks_of(q["document_name"])
    if q["chunk_seq"] >= len(cs):
        probs.append((q["id"], "主chunk超范围"))
    for a in q.get("also_documents", []):
        acs = chunks_of(a["document_name"])
        if a["chunk_seq"] >= len(acs):
            probs.append((q["id"], "also超范围"))
print("chunk 全通过" if not probs else probs)
print("== X 题内容抽查 ==")
for q in news:
    print(f"--- {q['id']} [{q['document_name']} #{q['chunk_seq']}] {q['category']}")
    print("问:", q["question"][:90])
    if q.get("context"):
        print("ctx:", q["context"][:100])
    print("chunk:", chunks_of(q["document_name"])[q["chunk_seq"]][:100].replace("\n", " "))
print("== 排重（X 题 vs 全部旧题 44 道，>=2 个4-gram）==")


def grams(q, n=4):
    ws = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", q)
    return {"".join(ws[i : i + n]) for i in range(len(ws) - n + 1)}


flag = 0
for q in news:
    g = grams(q["question"])
    for bid, b in all_old.items():
        ov = len(g & grams(b["question"]))
        if ov >= 2:
            flag += 1
            print(f"{q['id']} vs {bid}: {ov} | {q['question'][:30]} | {b['question'][:30]}")
print("无重叠>=2" if not flag else f"{flag} 处需人工判断")
# 4字短语检查（问题里出现原文连续4字，排除专有名词）
print("== 词汇距离检查（问题与标注chunk的最长公共子串）==")
PROPER = {
    "快速排序",
    "循环队列",
    "完全二叉树",
    "满二叉树",
    "二叉搜索树",
    "红黑树",
    "哈希冲突",
    "链地址法",
    "开放寻址",
    "双向链表",
    "堆排序",
    "插入排序",
    "归并排序",
    "选择排序",
    "冒泡排序",
    "二分查找",
    "动态数组",
    "层序遍历",
    "时间复杂度",
    "空间复杂度",
    "完全填满",
    "AVL",
    "BST",
    "LIFO",
    "FIFO",
    "ArrayList",
    "TreeMap",
    "LRU",
    "BFS",
    "pivot",
    "push",
    "pop",
    "enqueue",
    "dequeue",
    "rehash",
    "next",
    "prev",
    "O(1)",
    "O(n)",
    "O(log n)",
}
for q in news:
    text = chunks_of(q["document_name"])[q["chunk_seq"]]
    qw = re.sub(r"\s", "", q["question"])
    longest = ""
    for i in range(len(qw)):
        for j in range(i + 4, len(qw) + 1):
            sub = qw[i:j]
            if sub in text and len(sub) > len(longest):
                if not any(p in sub for p in PROPER):
                    longest = sub
    mark = "OK" if len(longest) < 4 else f"!! 4字+非专名: '{longest}'"
    print(q["id"], mark)
