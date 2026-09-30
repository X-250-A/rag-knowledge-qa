# Release Notes

> 版本号与架构设计文档（RAG知识库问答平台架构设计.md）对齐。倒序排列，最新在上。

## v0.5.1（2026-09-30）

解析质量与代码卫生：

- **docx 表格按文档顺序提取**：parse_docx 改为按 body XML 顺序遍历段落与表格，表格经 table_to_text 转为文本块（行内空格分隔、行间换行），不再甩到文末破坏上下文
- **chunker 过滤空段落**：切分前过滤 strip 后为空的段落（空串/纯空白），避免空块入库污染向量库
- 弱信号疑问词（怎么/如何/为什么/哪些/？）移出关键词快通道，交 LLM 主判，修复「怎么删除文档」误判
- embedding 惰性加载加 double-checked locking，防并发重复初始化
- CRUD 清理：移除 get_documents_list 未生效的 limit 参数

## v0.5.0（2026-09-13）

意图识别 Agent 化：

- 意图识别拆分为独立 `IntentClassifier` 模块：关键词快通道 + LLM 主判 + 默认 rag_query 降级
- gitignore 忽略运行时日志目录

## v0.4.0（2026-09-13）

检索精排与工程化收尾：

- **CrossEncoder reranker 上线**（bge-reranker-v2-m3 本地推理）：两路召回各 20 → RRF 全量融合 → 精排截断
- 检索指标：MRR 0.939 → **0.963**（L4 指代 1.000，L3 0.889）
- 日志体系完整化：crud_log 装饰器（仅写操作）、请求级计时中间件、噪音压制、logger 命名统一
- 统一事务边界：CRUD 只 flush 不 commit、get_db 收尾 commit、Depends 加 function scope
- 沉淀 reranker/混合检索实现模板（docs/reranker实现模板_用户手写.md）

## v0.3.0（2026-09-04）

混合检索：

- **BM25 关键词检索上线**（jieba 分词 + 停用词 + per-user 内存缓存）：与向量检索双路召回，RRF（k=60）融合
- 检索指标：MRR 0.906 → **0.939**（L2 +0.104，L3 +0.119）
- 入库/删除后自动 invalidate BM25 缓存

## v0.2.0（2026-08-28 ~ 09-01）

评估体系与工程化升级：

- **评估集扩至 66 题 + 知识库 7 篇**：evaluator 支持多文件/多标注/分组统计，标注精确到 chunk_seq
- 基线指标：MRR 0.906（Hit@5=1.000 饱和，主指标切 Hit@1 + MRR）
- 向量库写入自验证 + 写入前清残留；delete 兼容 chroma 1.x $and 语法
- 工程化：自定义异常体系替代 HTTPException、统一 logging、pydantic 请求校验加固、未处理异常兜底 500
- 请求级计时中间件（耗时/状态码结构化日志）
- 配置静态校验落地（空值/占位符拦截）
- CI：GitHub Actions 接入（ruff + pyright + pytest）；pyright 18 条报告清零；pre-commit 接入（ruff + 格式守卫）
- 修复 .gitignore 误伤 backend/app/models 导致 ORM 模型未入库的问题

## v0.1.0（2026-08-27）

MVP 首版：

- 基础 RAG 三件套：上传文档（PDF/Word/Markdown）→ 段落优先切分（+句号补切 + 50 字重叠）→ bge-m3 向量化 → ChromaDB 入库
- 在线管线：问题向量化 → 语义检索 top_k → 拼 prompt 让 DeepSeek 带引用作答（SSE 流式：检索事件 → 引用事件 → 增量文本）
- 意图识别四分类雏形（rag_query / chitchat / document_management / out_of_scope）
- 前端四页（Next.js：登录注册 / 文档管理 / 问答 / 会话历史）
- JWT 鉴权 + 用户数据隔离；会话持久化（SQLite）
- 检索评估集与基线、文档删除链路与查重修复、前端批量上传
