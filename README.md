# RAG 知识库问答平台

手写 RAG 管线（从零实现，不套 LangChain）的知识库问答平台：上传文档 → 自动解析分块、向量化入库 → 基于个人知识库提问，获得带引用溯源的流式回答。

## 功能特性

- **文档入库**：上传 PDF / Word / Markdown，自动解析为纯文本并分块（段落优先切分 + 句号补切 + 50 字重叠），bge-m3 本地向量化后写入 ChromaDB
- **向量检索**：本地 BGE 嵌入 + ChromaDB 向量库语义检索（带 user_id 数据隔离）
- **意图识别 Agent**：LLM 先判断用户意图（知识库问答 / 闲聊 / 文档管理 / 无关），据此分流处理
- **引用溯源**：回答自动标注来源（文档名 + 块序号），前端可点击查看原文片段
- **SSE 流式回答**：检索事件 → 引用事件 → 增量文本 → 完成，前端流式渲染
- **会话持久化**：多轮对话历史存 SQLite，可继续会话
- **JWT 鉴权**：注册/登录 + 用户数据隔离（JWT Bearer + bcrypt 密码哈希）

## 技术栈

| 模块 | 选型 |
|------|------|
| 后端框架 | FastAPI（Python ≥3.12） |
| ORM | SQLAlchemy 2.0 async + aiosqlite |
| 向量库 | ChromaDB（嵌入式，本地持久化） |
| Embedding | bge-m3（本地，sentence-transformers 加载） |
| LLM | DeepSeek API（OpenAI 兼容协议） |
| 文档解析 | pymupdf（PDF）/ python-docx（Word）/ 原生（Markdown） |
| 前端 | Next.js 16 + React 19 + TypeScript + Tailwind 4 |
| 工程 | uv / ruff / pytest |

> 说明：本项目的检索方案以**纯向量检索**为核心（MVP 阶段）。混合检索（BM25 + Reranker 重排）、检索自纠（LangGraph）与评估集为规划中的进阶方向，接口与结构已预留，尚未接入。

## 目录结构

```
rag-knowledge-qa/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口 + 路由挂载 + CORS/JWT 中间件
│   │   ├── config.py          # pydantic-settings 配置（读 .env）
│   │   ├── agent/             # RAGAgent（意图识别 + 问答分流编排）
│   │   ├── rag/               # pipeline（建库/查询管线）
│   │   ├── routers/           # auth / documents / chat / conversations / health
│   │   ├── services/          # parser / chunker / embedding / vector_store / retriever / llm_client / prompt_builder
│   │   ├── crud/              # SQLite 元数据读写
│   │   ├── models/            # ORM 模型（user/document/chunk/conversation/message）
│   │   └── schemas/           # Pydantic API 契约
│   └── tests/                 # 健康检查测试
├── frontend/                  # Next.js 前端（登录/注册/文档管理/问答）
├── RAG知识库问答平台架构设计.md   # 架构设计文档
├── RAG知识库问答平台API接口规范.md # API 接口规范
├── 项目开发历程/               # 开发日记
├── pyproject.toml             # Python 依赖（uv 管理）
└── .env.example               # 环境变量示例
```

## 快速开始

### 环境要求

- Python ≥ 3.12
- Node.js（前端）
- [uv](https://docs.astral.sh/uv/)（Python 包管理器，推荐）
- NVIDIA GPU（可选，bge-m3 本地嵌入用，CPU 亦可但较慢）

### 1. 后端

```bash
# 安装依赖（uv 自动按 pyproject.toml 解析，torch 从 cu130 源装 GPU 版）
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY（必填）与 SECRET_KEY

# 启动（项目根目录下）
uvicorn backend.app.main:app --reload --port 8000
```

> 首次运行 bge-m3 会自动下载约 2.3GB 模型权重。国内网络需先设置镜像：
> ```bash
> export HF_ENDPOINT=https://hf-mirror.com
> ```

### 2. 前端

```bash
cd frontend
npm install
npm run dev     # http://localhost:3000
```

### 3. 使用

1. 浏览器打开前端，注册/登录
2. 进入文档管理页，上传 PDF / Word / Markdown
3. 回到问答页，基于知识库提问，获得带引用溯源的流式回答

## API 接口

接口规范详见 [RAG知识库问答平台API接口规范.md](./RAG知识库问答平台API接口规范.md)。

核心接口一览：

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | 否 | 注册 |
| POST | `/api/auth/login` | 否 | 登录（返回 JWT） |
| GET | `/api/auth/me` | 是 | 当前用户信息 |
| POST | `/api/documents` | 是 | 上传文档（自动入库） |
| GET | `/api/documents` | 是 | 文档列表 |
| DELETE | `/api/documents/{id}` | 是 | 删除文档（级联清向量） |
| POST | `/api/chat` | 是 | 问答（SSE 流式） |
| GET | `/api/conversations` | 是 | 会话列表 |
| GET | `/api/conversations/{id}/messages` | 是 | 会话消息历史 |
| GET | `/api/health` | 否 | 健康检查 |

> 注：以实际运行接口为准，`/api/evaluation/*` 为规划中的评估接口。

## 环境变量

| 变量 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `DEEPSEEK_API_KEY` | 是 | - | DeepSeek 密钥 |
| `SECRET_KEY` | 是 | - | JWT 签名密钥 |
| `DATABASE_URL` | 否 | `sqlite+aiosqlite:///./rag_qa.db` | 元数据库 |
| `BASE_URL` | 否 | `https://api.deepseek.com` | LLM 端点 |
| `DEEPSEEK_MODEL` | 否 | `deepseek-chat` | 模型名 |

## 测试

```bash
uv run pytest
```

## License

[MIT](./LICENSE)
