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
print("== also_documents 跨文档标注核对 ==")
for q in hard:
    for a in q.get("also_documents", []):
        cs = chunks_of(a["document_name"])
        s = a["chunk_seq"]
        status = "OK" if s < len(cs) else "超出范围"
        print(q["id"], a["document_name"], f"#{s}", status, "|", cs[s][:80].replace("\n", " "))


def grams(q, n=4):
    ws = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", q)
    return {"".join(ws[i : i + n]) for i in range(len(ws) - n + 1)}


print("\n== 与现有24题重叠 >=2 个4-gram 的新题 ==")
flag = 0
for q in hard + collo:
    g = grams(q["question"])
    for b in base:
        ov = len(g & grams(b["question"]))
        if ov >= 2:
            flag += 1
            print(
                f"{q['id']} vs {b['id']}: 共享{ov}个 | 新题:{q['question'][:35]} | 旧题:{b['question'][:35]}"
            )
print("无重叠>=2" if flag == 0 else f"共{flag}处需人工判断")
