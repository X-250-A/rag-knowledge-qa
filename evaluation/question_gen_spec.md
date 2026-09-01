# 评估集加难出题 Spec（L2~L5，DeepSeek 执行）

## 任务目标

为 evaluation/questions.json 追加 16 道难题（L2~L5 各 4 道），把基线 Hit@5 从 1.000 打到 0.7~0.85 区间。
L1（口语化改写）由 Hermes 另行完成，不在本任务范围。

## 唯一允许的出题依据

只准读以下 4 篇文档出题，禁止使用任何文档外的知识点（哪怕是你自己知道的正确知识）：

- evaluation/knowledge_base/01_数组与链表.md
- evaluation/knowledge_base/02_栈队列哈希表.md
- evaluation/knowledge_base/03_树与二叉树.md
- evaluation/knowledge_base/04_排序与查找.md

先跑 `evaluation/scripts/chunk_preview.py`（或读 chunker.py 后自行复现 chunk_text(text,300,50) 的切分）确认每篇文档的 chunk 边界，所有 chunk_seq 标注必须与切分结果一致。不确定就标注你实际核对过的 seq，不许猜。

## 输出格式

新建文件 evaluation/questions_hard.json，结构与 questions.json 完全一致：

{
  "meta": { "note": "...", "levels": "L2-L5" },
  "questions": [
    { "id": "H2-01", "question": "...", "document_name": "...", "chunk_seq": N,
      "category": "...", "reference_answer": "...", "level": "L2" }
  ]
}

- id 规则：H2-xx（L2）、H3-xx（L3）、H4-xx（L4）、H5-xx（L5）
- L3 跨文档题标注例外："document_name" 填主文档，额外加 "also_documents": [{"document_name": "...", "chunk_seq": N}]
- category 取值：confusion（L2 干扰）、cross_doc（L3）、anaphora（L4）、long_tail（L5）
- 每题必须带 "level" 字段（现有 24 题没有，新题统一补上）

## 四档难度定义与配额（各 4 道）

### L2 概念混淆干扰（category=confusion）

出与现有 24 题相似概念竞争的题：问题表述与文档中多个 chunk 都有词汇重叠，但正确答案只在其中一处。
例子思路（仅供理解，具体题自己出）：链表插入 O(1) vs 哈希冲突链地址法 vs 循环队列取模——三者都是"链/位置/复杂度"话题，问题要能把向量检索带偏到错误 chunk 上。
设计标准：你预期 bge-m3 有较大概率把错误 chunk 排进 top5 甚至排到正确答案前面。

### L3 跨文档综合（category=cross_doc）

问题需要两个文档的 chunk 才能完整回答，标注主文档 + also_documents。
例子思路：用数组/链表（doc1）+ 哈希表（doc2）的组合特性出一道"设计题"，如"如果用数组实现哈希表，负载因子过高扩容时会遇到数组什么缺点？"（答案要点：数组中间插入删除 O(n) + 扩容需整体复制 + 链地址法弥补）——具体以文档实际内容为准。

### L4 指代消解（category=anaphora）

模拟多轮对话中的追问，问题单独看无法定位答案。每题在 "context" 字段给出上一轮的问答（1~2 句），问题里用代词指代上一轮实体。
例子形态：context: "问：快速排序的平均复杂度是多少？答：O(n log n)..."，question: "那它最坏的情况呢？为什么？"——"它"指快速排序。
设计标准：把 context 里的实体名换掉或删掉，问题就无法唯一确定答案。

### L5 长尾细节（category=long_tail）

挑 chunk 中段/末尾、信息密度低的冷门句子出题（不要挑每个 chunk 开头的主题句——那些现有题目已经覆盖）。
问题用非原文措辞（同义改写 + 语序调整），考察 embedding 对 chunk 边缘弱表达句子的召回能力。

## 硬性禁止

1. 禁止编造 4 篇文档中不存在的知识点、数字、复杂度
2. 禁止与现有 24 题重复或近似（先读 questions.json 排重）
3. 禁止把答案写进问题里（不能出现"是否因为XXX导致YYY？"这种自答式提问）
4. reference_answer 必须是文档原文内容的忠实概括，不引入外部解释
5. 每 chunk 最多出 1 道题，避免扎堆

## 自验要求

完成后自行做一次静态自检并输出报告：
- 每题的 document_name/chunk_seq 与 chunk 切分核对结果（列表形式：题号→核对通过/存疑）
- 与现有 24 题的排重结果
- 16 题分布统计（按 level/category/document）

最多自查重试 2 次，仍存疑就交付并在报告中注明存疑项。
