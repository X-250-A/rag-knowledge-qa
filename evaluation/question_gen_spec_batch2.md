# 评估集扩题 Spec 第二批（L2~L5 +20 题，DeepSeek 执行）

## 背景

第一批 16 道难题（questions_hard.json）已验收。本批再扩 20 道，全部为高难度题，**不出 L1 口语化题**。
目标：把基线 Hit@5 从 1.000 打到 0.7~0.85；若跑分仍 1.000 说明难度不足。

## 唯一允许的出题依据

只准读以下 4 篇文档，禁止任何文档外知识点：

- evaluation/knowledge_base/01_数组与链表.md
- evaluation/knowledge_base/02_栈队列哈希表.md
- evaluation/knowledge_base/03_树与二叉树.md
- evaluation/knowledge_base/04_排序与查找.md

chunk_seq 必须先用 chunk_preview.py（chunk_text(text,300,50)，零基索引）核对，不许猜。

## 同 chunk 复用规则（本批新规，替代"每 chunk 最多 1 题"）

正文 chunk 已被第一批占满，允许同 chunk 出第 2 题，但必须同时满足：
1. 与第一批该 chunk 那道题**类别不同**（如第一批考 fact 角度，这批考 why/how/cross_doc 角度）
2. **答案要点不同**：引用 chunk 中另一句话，或对原文做更深一层的推理合成
3. 问题措辞与原文的词汇距离更大（同义词改写 + 语序重排，禁止出现原文连续 4 字短语在问题里）

## 输出格式

追加到 evaluation/questions_hard.json（读出现有 16 题，合并后写回，保持 JSON 合法）：
新题 id 规则：X2-01~04（L2）、X3-01~02（L3）、X4-01~04（L4）、X5-01~04（X5 错了是 X5-01~04 L5），共 20 道。
字段与第一批一致：id/question/document_name/chunk_seq/category/reference_answer/level，L3 带 also_documents，L4 带 context。

## 配额与难度要求（总 20 道）

### L2 概念混淆 +4（category=confusion）

换竞争角度重出：第一批 H2 已占 02#3、01#6、04#7、03#7，本批从**其余概念对**里挑竞争（如：满二叉树 vs 完全二叉树、稳定 vs 不稳定排序、队列 vs 双端队列语境、开放寻址 vs 链地址）。要求错误选项 chunk 与正确 chunk 在向量空间高度相邻。

### L3 跨文档综合 +2（category=cross_doc）

尚未用过的跨文档组合优先：03×04（树+排序，如"用 BST 组织数据再中序遍历=排序"若原文有支撑）、01×04（数组+排序，如原地排序对数组的意义）。答案必须真正需要两个文档的 chunk 拼合，标注主文档 + also_documents。

### L4 指代消解 +4（category=anaphora）

同 chunk 可复用但 context 必须换：
- 同一实体换前轮话题（第一批考"撤销"，这批考"函数调用栈"或"表达式求值"作前轮）
- 换实体套同句式（如前轮问 AVL，追问"那红黑树呢？"）
- 至少 1 道做**链式指代**：context 2 轮，问题里的代词指第 1 轮实体（考察对话历史跨度的压力）
每题单独看问题必须无法唯一定位答案。

### L5 长尾细节 +4（category=long_tail）

两种来源各 2 道：
- a) 已被第一批占用的 chunk 里**没考过的句子**出题（标注同 chunk，答案不同）
- b) 各文档 chunk 中段/末尾信息密度最低的句子，问题做同义改写（禁止原文措辞）
优先挑：哨兵节点作用（01#6 后半）、动态数组两种语言示例（01#3 前半）、栈的 LIFO 英文术语（02#1）、快排不稳定的具体含义（04#4 后半）等原文一句带过、从没被现有任何题目考过的点。

## 硬性禁止

1. 禁止编造 4 篇文档外的知识点/数字/复杂度
2. 禁止与现有 44 题（24 基线 + 16 第一批 + 4 口语化草稿）重复或近似——先读 questions.json 和 questions_hard.json 排重
3. 禁止自答式提问
4. reference_answer 忠实于 chunk 原文，合成推理题须在答案里体现两个出处
5. 禁止问题里出现原文连续 4 字短语（强迫同义改写；专有名词如"快速排序""循环队列"不受此限）

## 自验要求

完成后输出静态自检报告：
- 20 题 chunk 核对表（含同 chunk 复用题的"角度不重叠"自查说明）
- 与全部 44 题排重结果
- 分布统计（level/category/document）
- 存疑项注明

自查最多重试 2 次，仍存疑就交付并注明。
