# RAG 知识库问答平台 API 接口规范

> 项目名：rag-knowledge-qa
> 文档版本：v0.1.0（骨架阶段）
> 配套文档：《RAG知识库问答平台架构设计.md》

---

## 1. 通用约定

### 1.1 请求格式

- Base URL：`http://localhost:8000`（开发）/ `http://backend:8000`（Docker 内网）
- 所有接口为 RESTful，请求/响应体均使用 JSON（`Content-Type: application/json`）
- 文件上传使用 `multipart/form-data`
- 流式问答使用 SSE（Server-Sent Events）

### 1.2 认证体系

- 注册/登录后返回 `access_token`（JWT，Bearer 方案）
- 除 `/api/auth/register`、`/api/auth/login`、`/api/health` 外，所有接口需在请求头携带：

```
Authorization: Bearer <access_token>
```

- Token 有效期建议 24h，过期返回 401，前端跳转登录页

### 1.3 响应格式

普通接口统一封装：

```json
{
  "code": 0,
  "message": "ok",
  "data": { }
}
```

| code | 含义 |
|---|---|
| 0 | 成功 |
| 40001 | 参数错误 |
| 40002 | 认证失败 |
| 40003 | 资源不存在 |
| 40004 | 权限不足 |
| 50000 | 服务端错误 |

> 注：SSE 流接口不套此壳，见 3.3。

### 1.4 HTTP 状态码

| 状态码 | 场景 |
|---|---|
| 200 | 成功 |
| 201 | 创建成功（上传/注册） |
| 400 | 参数错误/文件类型不支持 |
| 401 | 未认证/Token 失效 |
| 403 | 无权限（访问他人资源） |
| 404 | 资源不存在 |
| 413 | 文件超限 |
| 500 | 服务端错误 |

---

## 2. 数据模型

### 2.1 Document（文档）

```json
{
  "id": 1,
  "user_id": 1,
  "filename": "数据结构期末复习.pdf",
  "file_type": "pdf",
  "file_size": 2457600,
  "status": "ready",
  "chunk_count": 128,
  "created_at": "2026-08-18T21:00:00+08:00"
}
```

`status` 枚举：`pending`（待处理）→ `parsing`（解析中）→ `chunking`（分块中）→ `embedding`（向量化中）→ `ready`（就绪）/ `failed`（失败）

### 2.2 Chunk（分块）

```json
{
  "id": 1,
  "document_id": 1,
  "seq_no": 3,
  "content": "……（块文本）",
  "char_count": 420,
  "metadata_json": "{\"strategy\":\"paragraph+overlap\",\"overlap\":50}"
}
```

### 2.3 Citation（引用）

```json
{
  "doc_id": 1,
  "filename": "数据结构期末复习.pdf",
  "chunk_seq": 3,
  "snippet": "……（原文片段，前 100 字）"
}
```

### 2.4 Message（会话消息）

```json
{
  "id": 1,
  "conversation_id": 1,
  "role": "assistant",
  "content": "根据你的资料，二叉树的遍历分三种……[1]",
  "citations": [
    { "doc_id": 1, "filename": "数据结构期末复习.pdf", "chunk_seq": 3, "snippet": "……" }
  ],
  "created_at": "2026-08-18T21:05:00+08:00"
}
```

### 2.5 SSE 事件类型（问答流）

| event | data | 说明 |
|---|---|---|
| `retrieval` | `{"doc_count":2,"chunk_count":5,"elapsed_ms":180}` | 检索完成，前端可展示检索状态 |
| `citation` | `[Citation,...]` | 本次回答的引用列表 |
| `answer` | `{"text":"……"}` | 增量文本块，前端按块拼接 |
| `done` | `{"message_id":1}` | 流结束 |
| `error` | `{"code":50000,"message":"……"}` | 流中断错误 |

---

## 3. 接口详述

### 3.1 认证模块

#### `POST /api/auth/register` — 用户注册

请求：
```json
{ "username": "an", "password": "pass1234" }
```

响应 201：
```json
{ "code": 0, "message": "ok", "data": { "id": 1, "username": "an" } }
```

| 错误 | 场景 |
|---|---|
| 400 | 用户名已存在 / 密码长度 < 8 |

#### `POST /api/auth/login` — 用户登录

请求：
```json
{ "username": "an", "password": "pass1234" }
```

响应 200：
```json
{ "code": 0, "message": "ok", "data": { "access_token": "<jwt>", "token_type": "bearer" } }
```

#### `GET /api/auth/me` — 当前用户信息

响应 200：
```json
{ "code": 0, "message": "ok", "data": { "id": 1, "username": "an", "created_at": "2026-08-18T20:00:00+08:00" } }
```

### 3.2 文档管理模块

#### `POST /api/documents` — 上传文档（multipart/form-data）

参数：`file`（文件字段），支持 `.pdf` / `.docx` / `.md`，≤20MB。

响应 201：
```json
{ "code": 0, "message": "ok",
  "data": { "id": 1, "filename": "数据结构期末复习.pdf", "file_type": "pdf",
            "file_size": 2457600, "status": "pending", "chunk_count": 0,
            "created_at": "2026-08-18T21:00:00+08:00" } }
```

上传后自动触发建库管线（解析→分块→向量化），状态流转 `pending → parsing → chunking → embedding → ready`；任一环节失败置 `failed` 并在 `message` 中说明原因。

| 错误 | 场景 |
|---|---|
| 400 | 文件类型不支持 |
| 413 | 超过 20MB |

#### `GET /api/documents` — 文档列表（当前用户）

响应 200：
```json
{ "code": 0, "message": "ok", "data": { "items": [Document,...], "total": 12 } }
```

按创建时间倒序；包含各文档当前 `status`（前端渲染状态机进度）。

#### `GET /api/documents/{doc_id}` — 文档详情

响应 200：返回 Document + `chunks`（Chunk 列表摘要：seq_no / char_count）。

#### `DELETE /api/documents/{doc_id}` — 删除文档

级联删除：SQLite 中该文档的 chunks 记录 + ChromaDB 中对应向量（按 metadata.doc_id 过滤删除）。

响应 200：
```json
{ "code": 0, "message": "ok", "data": { "deleted": true } }
```

| 错误 | 场景 |
|---|---|
| 403 | 删除他人文档 |
| 404 | 文档不存在 |

### 3.3 问答模块（核心）

#### `POST /api/chat` — 发起问答（SSE 流式）

请求：
```json
{
  "conversation_id": 1,
  "question": "二叉树有哪几种遍历方式？",
  "top_k": 5,
  "use_hybrid": true
}
```

- `conversation_id`：可空；为空则服务端新建会话
- `top_k`：进 prompt 的块数，默认 5
- `use_hybrid`：是否启用混合检索（向量+BM25+重排），默认 true

响应：`Content-Type: text/event-stream`，按序下发事件：

```
event: retrieval
data: {"doc_count":2,"chunk_count":5,"elapsed_ms":180}

event: citation
data: [{"doc_id":1,"filename":"数据结构期末复习.pdf","chunk_seq":3,"snippet":"……"}]

event: answer
data: {"text":"根据你的资料，二叉树遍历分三种："}

event: answer
data: {"text":"前序、中序、后序[1]。"}

event: done
data: {"message_id":1,"conversation_id":1}
```

**问答内部流程**（服务端）：

```
question → embedding → 向量检索 top-20
         + BM25 检索 top-20（use_hybrid=true 时）
         → 合并去重 → Reranker 重排 → top-k
         → prompt_builder 组装（带 [n] 编号引用）
         → DeepSeek 生成（流式）→ 解析 [n] 引用 → 流式下发
```

**前端消费示例**（fetch + ReadableStream）：

```js
const res = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({ question, use_hybrid: true }),
});
const reader = res.body.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  parseSSE(decoder.decode(value)); // 按 event 分发：retrieval/citation/answer/done
}
```

**错误**：401 未认证；400 问题为空或知识库为空（提示先上传文档）；500 检索/生成失败（error 事件）。

#### `GET /api/conversations` — 会话列表

响应 200：`{ "items": [{ "id": 1, "title": "二叉树遍历", "created_at": "..." }], "total": 5 }`

#### `GET /api/conversations/{conv_id}/messages` — 会话消息历史

响应 200：`{ "items": [Message,...] }`（含 citations）

### 3.4 评估模块

#### `POST /api/evaluation/run` — 运行评估集

请求：
```json
{ "strategy": "hybrid" }
```

`strategy`：`vector`（纯向量）/ `hybrid`（混合+重排），用于对比实验。

响应 200：
```json
{ "code": 0, "message": "ok",
  "data": { "total": 20, "top5_hit": 18, "top5_hit_rate": 0.9, "elapsed_ms": 32000 } }
```

#### `GET /api/evaluation/results` — 评估历史

响应 200：`{ "items": [EvaluationResult,...] }`（含各策略历次指标，供对比图表）

### 3.5 健康检查

#### `GET /api/health`

响应 200：
```json
{ "status": "ok", "version": "0.1.0", "vector_store": "ready" }
```

`vector_store` 字段探测 ChromaDB 连接状态（`ready` / `unavailable`）。

---

## 4. 接口总览

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | /api/auth/register | 否 | 注册 |
| POST | /api/auth/login | 否 | 登录 |
| GET | /api/auth/me | 是 | 当前用户 |
| POST | /api/documents | 是 | 上传文档（自动入库） |
| GET | /api/documents | 是 | 文档列表 |
| GET | /api/documents/{id} | 是 | 文档详情 |
| DELETE | /api/documents/{id} | 是 | 删除文档（级联清向量） |
| POST | /api/chat | 是 | 问答（SSE 流式） |
| GET | /api/conversations | 是 | 会话列表 |
| GET | /api/conversations/{id}/messages | 是 | 会话消息历史 |
| POST | /api/evaluation/run | 是 | 运行评估集 |
| GET | /api/evaluation/results | 是 | 评估历史 |
| GET | /api/health | 否 | 健康检查 |

---

## 5. 前端错误处理指南

| 场景 | 处理 |
|---|---|
| 401 | 清除本地 token，跳转 /login |
| 400 知识库为空 | 聊天页展示引导：「知识库为空，请先到文档管理上传文档」 |
| 413 文件超限 | 上传组件前端先校验大小，拦截提示 |
| 文档 failed | 列表状态徽标变红，tooltip 显示失败原因，可删除重传 |
| SSE error 事件 | 聊天流中断，保留已渲染文本，展示「生成中断」重试按钮 |
| 网络断开 | fetch 异常捕获，提示检查后端服务是否启动 |

---

## 6. 环境变量

| 变量 | 必填 | 默认 | 说明 |
|---|---|---|---|
| DEEPSEEK_API_KEY | 是 | - | DeepSeek 密钥 |
| DEEPSEEK_BASE_URL | 否 | https://api.deepseek.com | LLM 端点 |
| EMBEDDING_PROVIDER | 否 | bge_local | bge_local / zhipu |
| ZHIPU_EMBEDDING_API_KEY | 条件 | - | EMBEDDING_PROVIDER=zhipu 时必填 |
| DATABASE_URL | 否 | sqlite+aiosqlite:///./rag_qa.db | 元数据库 |
| CHROMA_PERSIST_DIR | 否 | ./chroma_data | 向量库持久化目录 |
| JWT_SECRET | 是 | - | JWT 签名密钥 |
| JWT_EXPIRE_HOURS | 否 | 24 | Token 有效期 |
| MAX_UPLOAD_MB | 否 | 20 | 上传大小上限 |

---

*文档完。与架构设计文档配套，实现时以实际接口为准，有出入先改本文档再改代码。*
