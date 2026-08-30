# Pyright 报告修复任务 spec

项目：rag-knowledge-qa（D:/agent个人项目开发/从零开始型/rag-knowledge-qa）
目标：清零 basedpyright 对 backend 的全部 18 条（auth.py 已修完，剩 17 条）。
铁律：
1. 只做类型层面的修复（加判空、改标注、换变量名、补 cast），禁止改任何运行时逻辑/业务行为，禁止重构。
2. 禁止用 `# type: ignore` / `# pyright: ignore` 压制错误，除非某条确认是库 stub 问题且注明原因。
3. 修完必须跑 `npx --yes basedpyright backend` 确认 0 errors，再跑 `uv run pytest backend/tests -x -q` 确认测试全绿。
4. 不要 commit，改完报告即可。

## 逐条修复指引

### 1. backend/app/routers/documents.py（4 条，优先做，有真实运行时风险）
40-57 行：`UploadFile.filename` 类型是 `str | None`，`size` 是 `int | None`。
- 40 行 `Path(...) / file.filename`：先判空，filename 为 None 时抛 `BadRequestError`（或 FastAPI HTTPException 422，跟随项目现有异常风格）。
- 42/52 行同理，判空后再传。
- 52 行 `file_size` 参数：`int | None` 传给 `float` 形参，判空或转 float。
- 57 行 `parse_file` 的 `file_path` 参数要求 str：传 `str(path)` 或改 parse_file 标注为 Path（看哪个更顺，标注允许改）。

### 2. backend/app/services/retriever.py（3 条 reportOptionalSubscript）
12/18/19 行：chroma 返回的查询结果可能是 None 就直接下标。加判空提前返回（如返回空列表/None，跟随函数现有返回约定），不要 assert。

### 3. backend/app/agent/conversation.py（2 条）
- 49 行：token_counter 传了 None，形参是 `(int) -> int`。传一个默认计数函数 `lambda n: n` 或改形参为 `Callable[[int], int] | None` 并在调用点判 None。
- 59 行：str 传给 int 形参，查一下调用约定，转 int 或改对参数位。

### 4. backend/app/rag/pipeline.py（2 条）
38/60 行：numpy ndarray 传给标注为 `list` 的 embedding 形参。首选把 add_collection/query_collection 的 embedding 形参标注改成 `np.ndarray`（跟实际用法一致）；若下游确实需要 list 则传 `.tolist()`。

### 5. backend/app/agent/RAG_agent.py（2 条）
83-84 行：openai client.messages.create 的 messages 标注不匹配。把本地构造的 messages 列表标注为 `list[ChatCompletionMessageParam]`（从 openai.types.chat 导入），元素用 TypedDict 形式构造，不要 cast。

### 6. backend/app/services/llm_client.py（1 条）
20 行：AsyncClient 传给 `AsyncClient | None` 形参报错，多半是 httpx 版本泛型问题（AsyncClient[httpcore...]）。先看具体报错全文再定：能改标注就改标注，确实是 stub 误报才允许 ignore 并注释原因。

### 7. backend/app/exceptions.py（1 条）
57 行：exception_handler 装饰器的 handler 签名类型不匹配（Starlette 泛型 State 问题）。常见修法：handler 的 exc 参数标注放宽为 `Exception`，或标注用 `Request[dict]`；确认运行时行为不变。

## 验收标准
- `npx --yes basedpyright backend` → 0 errors, 0 warnings
- `uv run pytest backend/tests -x -q` → 全部通过
- git diff 里没有任何业务逻辑变更（只允许类型/判空/标注）
