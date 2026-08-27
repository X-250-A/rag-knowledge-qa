# RAG 知识库问答平台 架构设计

> 项目名：rag-knowledge-qa
> 文档版本：v0.1.0（骨架阶段）
> 定位：求职项目二——独立 RAG 知识库问答平台（主攻 RAG 深度，面试弹药项目）

---

## 1. 项目概述

用户上传文档（PDF / Word / Markdown）→ 系统自动解析、分块、向量化入库 → 用户基于知识库提问，获得**带引用溯源**的回答。通用场景，不绑定任何垂直领域。

### 核心能力

| 能力 | 说明 |
|---|---|
| 文档入库 | 上传 PDF/Word/Markdown，自动解析为纯文本并分块 |
| 向量检索 | 本地 BGE 嵌入 + ChromaDB 向量库，语义检索 |
| 混合检索 | 向量检索 + BM25 关键词检索双路合并，BGE-Reranker 重排 |
| 引用溯源 | 回答自动标注来源（哪个文档、第几段），支持点击回看原文 |
| 检索自纠 | 检索质量差时自动改写查询重试（Agentic RAG，LangGraph 编排） |
| 评估集 | 自建 20 题人工标注评估集，量化对比检索方案，产出简历指标 |

### 与 travel-assistant 的关系

- 姊妹项目：技术栈（FastAPI + Next.js + DeepSeek）与工程规范（uv / ruff / pytest / Docker）完全复用
- 差异：travel-assistant 是 Agent 全栈（ReAct + 工具调用），本项目是 RAG 深度专项
- travel-assistant 的向量语义记忆（bge-m3 + KNN 召回）是本项目向量检索的雏形，本项目将其升级为完整 RAG 管线

---

## 2. 系统架构

### 2.1 总体分层

```
┌─────────────────────────────────────────────────────────┐
│                    前端（Next.js 15）                     │
│   文档管理页 · 问答页（SSE 流式） · 引用卡片 · 登录注册     │
└──────────────────────────┬──────────────────────────────┘
                           │ REST / SSE（JWT Bearer）
┌──────────────────────────▼──────────────────────────────┐
│                 API 层（FastAPI routers）                 │
│   auth  ·  documents（上传/入库/管理）·  chat ·  evaluation │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    服务层（services）                     │
│  parser（解析）· chunker（分块）· embedding（嵌入）         │
│  vector_store（向量库）· retriever（检索+重排）· llm_client │
│  prompt_builder（组装）· evaluator（评估）                 │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    编排层（rag）                          │
│   pipeline（建库管线 / 问答管线）· query_rewrite（检索自纠） │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                      存储层                              │
│   SQLite（用户/文档/分块/会话元数据）                      │
│   ChromaDB（向量库，嵌入式持久化到磁盘）                   │
└─────────────────────────────────────────────────────────┘
```

### 2.2 两条核心数据流

**建库管线（离线）**：

```
上传文档 → 文件类型校验 → 解析为纯文本（parser）
       → 分块（chunker：段落切 + 句号补切 + 50 字重叠）
       → 每块生成向量（embedding：bge-m3）
       → 写入 ChromaDB（vector_store）+ 元数据写 SQLite
       → 文档状态置 ready
```

**问答管线（在线）**：

```
用户提问 → 问题转向量 → 向量检索 top-20
        + BM25 关键词检索 top-20
        → 双路合并去重 → BGE-Reranker 重排 → 取 top-5
        → prompt_builder 组装（检索块 + 引用编号 + 问题）
        → DeepSeek 生成回答（回答内标注 [1][2] 引用编号）
        → SSE 流式返回：检索事件 → 引用事件 → 答案文本
```

### 2.3 分层职责

| 层 | 职责 | 关键原则 |
|---|---|---|
| routers | HTTP 入参校验、鉴权、SSE 响应 | 不含业务逻辑，只做编排 |
| services | 单一职责能力（解析/分块/嵌入/检索/生成） | 每个模块可独立测试 |
| rag | 管线编排与跨模块协作 | 建库/问答两条管线在此汇聚 |
| models/schemas | ORM 模型与 API 契约 | 严格分离，不混用 |
| crud | 数据库读写 | 只处理 SQLite 元数据 |

---

## 3. 技术栈

| 模块 | 选型 | 理由 |
|---|---|---|
| 后端框架 | FastAPI（Python ≥3.14） | 与 travel-assistant 一致，异步原生 |
| ORM | SQLAlchemy 2.0 async + aiosqlite | 元数据持久化，轻量零部署 |
| 向量库 | ChromaDB | 纯 Python 嵌入式，零部署；量大可平滑换 Qdrant/Milvus |
| Embedding | BGE（bge-m3，本地） | 中文第一梯队、免费无限制；智谱 embedding-3 API 兜底 |
| 关键词检索 | rank_bm25 | 轻量、无服务，混合检索第二路 |
| 重排 | bge-reranker（本地） | 精排提升 Top-5 准确率 |
| LLM | DeepSeek API（OpenAI 兼容） | 已有 key，零新增成本 |
| 文档解析 | pymupdf（PDF）/ python-docx（Word）/ 原生（Markdown） | 覆盖三种目标格式 |
| 前端 | Next.js 15 + TypeScript + Tailwind 4 | 与 travel-assistant 一致 |
| 编排（后续） | LangGraph | 检索-评估-重试循环（query rewrite） |
| 工程 | uv / ruff / pytest / Docker Compose | 与 travel-assistant 一致 |

---

## 4. 核心设计

### 4.1 分块策略（手写，面试必问）

**算法**：段落优先切分 → 超长段落按句号补切 → 相邻块保留 50 字重叠。

- 为什么段落优先：语义完整单元是段落，硬按字符数切会切断语义
- 为什么句号补切：段落超长（如大段表格文本）时按句号/问号/感叹号在字符上限内回退切分
- 为什么 50 字重叠：跨块语义（指代、上下文衔接）不丢，重叠量是召回与冗余的平衡点
- 参数：目标块长约 300~500 字（中文），上限可配

**面试弹药**：能讲清楚"为什么这么切"+"不同切法对召回的影响"，这是面试官追问链第一环。

### 4.2 Embedding 选型

- 主：**bge-m3 本地**（sentence-transformers / fastembed 加载），中文检索第一梯队，本地运行零成本零限流
- 兜底：**智谱 embedding-3 API**（OpenAI 兼容），本地模型加载失败/磁盘不足时切换
- 设计为抽象接口 `EmbeddingProvider`，实现可替换，评估集可对比不同 embedding 效果

### 4.3 混合检索（进阶亮点）

```
向量检索 top-20 ─┐
                 ├─ 合并去重（按 chunk_id）→ Reranker 精排 → top-5 进 prompt
BM25 检索 top-20 ─┘
```

- 为什么混合：向量检索擅长语义相似，BM25 擅长关键词精确匹配（专有名词、编号、术语），单路都有漏
- 为什么重排：双路合并后候选集噪声多，Reranker 交叉编码精排能显著提升 top-5 准确率
- 简历指标口径：`纯向量 vs 混合检索` 在自建评估集上的 Top-5 命中率对比

### 4.4 引用溯源（大亮点）

- 每个 chunk 入库时记录 `(文档 id, 文件名, 块序号, 原文内容)`
- 检索结果拼入 prompt 时带编号：`[1] 文档A-第3段`、`[2] 文档B-第7段`
- DeepSeek 回答时用编号标注依据 → 后端解析引用 → SSE 下发引用事件 → 前端渲染引用卡片，点击可查看原文片段
- 作用：对齐 JD 高频词"幻觉抑制 + 引用溯源"；回答可验证，用户可自查

### 4.5 检索-评估-重试循环（LangGraph 落点，后续迭代）

```
           ┌────────────────────────────┐
           ▼                            │
   检索(向量+BM25) → 评估(阈值判定) → 通过 → 生成回答
           │ 不通过                     │
           ▼                            │
   改写查询(query rewrite) ─────────────┘  （最多重试 2 次）
```

- 评估信号：检索 top-5 与问题的相似度得分低于阈值，或检索结果为空
- 改写策略：让 DeepSeek 把问题改写为更利于检索的表达（补充实体、去口语化）
- 用 LangGraph 图编排（节点：检索 → 评估 → 通过/改写分支），1-2 天落地，简历写"熟悉 LangGraph"
- 简历写法："使用 LangGraph 编排检索-评估-重试流程，检索失败自动改写 Query，准确率提升 X%"

### 4.6 评估集（杀手锏）

- 自建 20 题人工标注评估集：从真实文档（自己的课件/教材/笔记）抽取 20 个问题，人工标注标准答案与命中文档位置
- 指标：Top-5 命中率（答案所在 chunk 是否在 top-5 召回中）、答案准确率（LLM 生成质量人工打分）
- 对比实验：纯向量 vs 混合检索（+重排），产出量化数据写进简历
- 评估脚本可一键重跑，任何检索参数改动都能复测——"有评估"是区分套壳 demo 的关键

### 4.7 鉴权与中间件

- JWT（python-jose）Bearer Token，与 travel-assistant 同套方案
- 用户数据隔离：文档/会话全部带 user_id，检索只查本人知识库
- 中间件管道：CORS → 鉴权（公开路由白名单：注册/登录/健康检查）

---

## 5. 数据模型

### 5.1 ER 关系

```
User 1 ──── * Document 1 ──── * Chunk
  │
  └──────── * Conversation 1 ──── * Message
```

### 5.2 表结构

**User**
| 字段 | 类型 | 说明 |
|---|---|---|
| id | Integer PK | |
| username | String unique | 用户名 |
| hashed_password | String | bcrypt 哈希 |
| created_at | DateTime | |

**Document**
| 字段 | 类型 | 说明 |
|---|---|---|
| id | Integer PK | |
| user_id | FK → User | 归属用户 |
| filename | String | 原始文件名 |
| file_type | String | pdf / docx / md |
| file_size | Integer | 字节 |
| status | String | pending → parsing → chunking → embedding → ready / failed |
| chunk_count | Integer | 入库块数 |
| created_at | DateTime | |

**Chunk**
| 字段 | 类型 | 说明 |
|---|---|---|
| id | Integer PK | |
| document_id | FK → Document | 所属文档 |
| seq_no | Integer | 块序号（引用定位用） |
| content | Text | 块文本 |
| char_count | Integer | 字符数 |
| metadata_json | Text | 来源/切法等元数据 |
| created_at | DateTime | |

**Conversation / Message**
| 字段 | 类型 | 说明 |
|---|---|---|
| id | Integer PK | |
| conversation_id / user_id | FK | |
| role | String | user / assistant |
| content | Text | 消息正文 |
| citations_json | Text | 引用列表（assistant 消息） |

### 5.3 设计决策：元数据放 SQLite、向量放 ChromaDB

- 文档/块元数据是关系型结构（归属、状态、数量统计），SQLite 天然适合且零部署
- 向量本体与检索放 ChromaDB（自带 HNSW 索引），两者以 chunk_id 关联
- ChromaDB 持久化目录 `./chroma_data`，SQLite 文件 `./rag_qa.db`，均可随仓库迁移

---

## 6. 关键技术决策

| 决策 | 方案 | 原因 |
|---|---|---|
| 手写 RAG 而非 LangChain | 手写全管线 | 套壳 demo 面试必穿帮（双信源面经印证）；原理在脑子里，追问任何细节答得上 |
| ChromaDB 而非 pgvector/Milvus | ChromaDB 嵌入式 | 零部署零成本；接口抽象后量大可平滑换 Qdrant/Milvus |
| SQLite 而非 MySQL | SQLite | 单用户场景足够；避免 travel-assistant 的 MySQL 依赖，Docker 只跑两服务 |
| BGE 本地而非 API embedding | bge-m3 本地 | 免费无限制、中文第一梯队；API 兜底保证可用性 |
| 不引入 LangChain 文本分割器 | 手写分块 | 面试必问切块策略，手写才讲得清；可选做与 LangChain splitter 的对比实验 |
| DeepSeek 而非其他 LLM | DeepSeek API | 已有 key，零新增成本；中文能力强 |

---

## 7. 前端设计系统

| 页面 | 路由 | 核心内容 |
|---|---|---|
| 登录/注册 | /login /register | 同 travel-assistant AuthForm 风格 |
| 文档管理 | /documents | 上传区（拖拽/选择）、文档列表（文件名/大小/状态/块数）、删除 |
| 问答 | /（首页） | 聊天窗口 + 流式回答 + 引用卡片 + 知识库范围提示 |

- 引用卡片：回答文本内 `[1]` 上标可点击，弹出来源（文件名 + 块序号 + 原文片段）
- 文档状态机可视化：pending/parsing/chunking/embedding/ready 实时进度
- 组件结构与 travel-assistant 对齐（components/ui、components/chat、hooks、lib/api.ts）

---

## 8. 开发路线

| 阶段 | 内容 | 时长 |
|---|---|---|
| 1 | 手写 RAG 管线（解析→分块→嵌入→入库→检索→生成） | 3-5 天 |
| 2 | 文档解析 + 引用溯源 + 前端打磨 | 2 天 |
| 3 | 混合检索（BM25 + Reranker）+ 评估集（产出简历指标） | 1-2 天 |
| 4 | LangGraph 扫盲 + 检索自纠循环落地 | 1-2 天 |
| 5 | 简历包装（STAR + 量化指标） | 1 天 |

总计 8-10 天，暑假末前简历可用。

**明确不做**：不学微调/部署（面试知道选型边界即可）；不碰 Dify/Coze 低代码；不套 LangChain 做 RAG；不新开第三个项目。

---

## 9. 安全设计

| 风险 | 对策 |
|---|---|
| 恶意文件上传 | 白名单：pdf/docx/md；大小上限（如 20MB）；解析失败标记 failed 不崩溃 |
| 提示注入（文档内容诱导） | 系统提示固定"仅依据检索内容回答，不确定就说明"；文档内容与指令在 prompt 中明确分隔 |
| 越权访问 | 所有查询带 user_id 过滤；JWT 校验中间件 |
| 检索库污染 | 删除文档时级联清理 ChromaDB 中对应 chunk |
| 传输安全 | 生产环境 HTTPS（反代）；SSE 同 JWT 鉴权 |

---

## 10. 部署

docker-compose.yml 两个服务（ChromaDB/SQLite 嵌入式，无需额外中间件）：

```
services:
  backend:   build ./backend   端口 8000   env_file .env
  frontend:  build ./frontend  端口 3000   NEXT_PUBLIC_API_URL=http://backend:8000
```

本地开发：后端 `uvicorn app.main:app --reload`，前端 `npm run dev`。

---

*文档完。技术选型与规划依据见桌面《AI求职RAG项目规划纪要.md》（2026-08-18 调研定稿）。*
