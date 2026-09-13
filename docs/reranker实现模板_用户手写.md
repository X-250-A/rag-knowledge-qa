# Reranker 实现模板（用户亲手写，Hermes 只提供骨架 + 讲解）

> 你的任务：把标 `# TODO` 的地方补完，写完自测，通过后交 Hermes review + 跑 66 题对比。
> 接入方式：改 `hybrid_retriever.hybrid_retrieve` 内部（RRF 取 20 → rerank → 返回 5），对外签名/返回契约不动。

## 你需要先装的依赖

```bash
uv add sentence-transformers --torch-backend cu130
```

⚠️ 50 系显卡（RTX 5070 Ti）硬性要求 cu130，让 uv 默认解析到 cu12x 会 import 即崩（access violation）。
模型权重首次运行自动下载（~2.3GB），国内先 `export HF_ENDPOINT=https://hf-mirror.com`。

## 知识卡：这轮会用到的新东西

### CrossEncoder（交叉编码器）
```python
from sentence_transformers import CrossEncoder
model = CrossEncoder("BAAI/bge-reranker-v2-m3", max_length=512)
scores = model.predict([("问题文本", "chunk1文本"), ("问题文本", "chunk2文本")])
# 返回 np.ndarray：每个 pair 一个原始分（logit，不是 0~1！）
```
- 原始分是 **logit**，范围不固定。要 0~1 的"相关概率"需过 sigmoid：
  `1 / (1 + math.exp(-s))`，或 `scipy.special.expit(scores)`
- predict 的输入是 **pair 列表**，一次调用批量打分（内部自动 batch，别自己 for 循环逐对调）

### 为什么精度更高（原理回顾）
- Bi-Encoder（bge-m3）：query 和 chunk **各自独立**编码，向量之间只算余弦——两者从未见面
- CrossEncoder：`[query, chunk]` 拼接后一起进模型，逐 token 交互后直接输出相关分——交互充分所以更准，也更贵（不可能全库算，只能精排少量候选）
- 这就是两段式架构：召回走便宜的（向量+BM25 各 20），精排走贵的（20 条 cross-encode 取 5）

### 单例 + 降级（工程要点）
- 模型加载照抄 embedding.py 的模式：模块级变量 + 惰性初始化 + 只加载一次
- **rerank 失败不能让检索挂**：try/except 包住打分调用，失败时返回"RRF 原序"结果（降级路径）
- 加载失败同理：_get_model() 抛异常 → 调用方降级

---

## 模板正文（新文件 `backend/app/services/reranker.py`）

```python
"""CrossEncoder 精排层：对混合检索的召回结果重排序。

输入 pair = (query, chunk_content)，输出 sigmoid 后的 0~1 相关分。
任何失败都降级为"保持 RRF 原序"，绝不让检索整体挂掉。
"""

import math
import logging

logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-reranker-v2-m3"

_model = None  # 模块级单例


def _get_model():
    # TODO 1: 惰性单例——_model 为 None 时加载（参考 embedding.py 的写法），
    #   CrossEncoder(MODEL_NAME, max_length=512)
    ...


def rerank(query: str, hits: list[dict], top_k: int) -> list[dict]:
    """对 hits（RRF 融合后的召回列表）精排，返回前 top_k。

    每个 hit 含 'content'；返回时把原 score 字段替换为 rerank 分（sigmoid 后 0~1）。
    失败时降级：返回 RRF 原序的 hits[:top_k]。
    """
    if not hits:
        return []
    try:
        model = _get_model()
    except Exception:
        logger.exception("reranker load failed, fallback to RRF order")
        return hits[:top_k]

    # TODO 2: 构造 pair 列表 [(query, hit["content"]) for hit in hits]，批量 predict
    # TODO 3: logit 过 sigmoid 转 0~1 分
    # TODO 4: 按新分降序排序，取前 top_k
    # TODO 5: 每个 hit 的 score 字段替换为 rerank 分（保留其他字段原样）
    ...
```

## 接入点（`hybrid_retriever.py` 内部改 3 行）

```python
# 现状：return _rrf_fuse(vec_hits, bm25_hits, top_k)[:top_k] 之类
# 改成：
fused = _rrf_fuse(vec_hits, bm25_hits, top_k=RECALL_AFTER_FUSE)  # 先取 20（新常量）
from backend.app.services.reranker import rerank                  # 函数内延迟 import（避免加载链）
return rerank(question, fused, top_k=top_k)
```

- `RECALL_AFTER_FUSE = 20`：RRF 融合后的候选池大小（给 reranker 精排的原料）
- 现有 `RECALL_PER_PATH = 20`（每路召回）不动
- hybrid_retrieve 的签名、返回契约一律不动——retriever.py / chat 路由 / 评估链零改动

## 自测脚本（写完先跑这个，不用起服务）

```python
# evaluation/scripts/test_reranker_manual.py
# cd backend && HF_ENDPOINT=https://hf-mirror.com ../.venv/Scripts/python.exe 该文件
from app.services.reranker import rerank

query = "哪种结构的查找性能与元素个数无关，靠层数决定"
hits = [
    {"id": "a", "content": "跳表通过多层索引加速有序链表查找，平均复杂度 O(log n)"},
    {"id": "b", "content": "Trie 树逐字符匹配，查找耗时与字符串长度相关"},
    {"id": "c", "content": "哈希表平均 O(1)，但最坏退化为 O(n)"},
]
out = rerank(query, hits, top_k=2)
assert out[0]["id"] == "a", out
assert 0.0 <= out[0]["score"] <= 1.0, out
print("RERANK-OK", [(h["id"], round(h["score"], 4)) for h in out])
```

预期：跳表 chunk 排第一且分数显著高于其他两个（query 描述了跳表的特征但没提名字——正好也是"去实体化"的场景）。

## 降级验证（review 时我会检查）

- 模型加载抛异常 → 返回 RRF 原序（不抛出）
- hits 为空 → 返回 []
- 分数相等时的排序稳定性（sorted 默认稳定即可）

## 验收标准

1. 自测脚本输出 RERANK-OK
2. 66 题评估：MRR ≥ 0.939（不退化），重点看 L4 指代（0.875→?）和 L3（0.875→?）
3. 起服务 chat 一轮，确认 score 字段已是 0~1、前端不再显示 0.03 量级的怪分数
