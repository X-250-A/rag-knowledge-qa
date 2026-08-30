# 补充第一档测试 spec：documents + conversations

项目：rag-knowledge-qa（D:/agent个人项目开发/从零开始型/rag-knowledge-qa）
目标：为 documents（上传/列表/删除）和 conversations（会话列表/消息查询）路由补测试，风格与现有 backend/tests/test_auth.py 一致。

## 铁律
1. 只新增/修改 backend/tests/ 下的文件，禁止改 app/ 任何代码。
2. 遵循现有 fixture 体系：conftest.py 的 `client`（内存 SQLite + dependency_overrides）和 `auth_headers`。需要新 fixture 就加在 conftest.py 里。
3. mock 策略：monkeypatch 在 app 层把 embedding/解析/LLM 等重依赖替换掉，不调真实模型、不连真实 chroma。上传测试用 io.BytesIO 构造内存文件即可，不写磁盘。
4. 断言用项目现有异常体系对应的状态码（BadRequestError→400，Conflict→409 等）。
5. 验收：`uv run python -m pytest backend/tests -q` 全绿（注意必须用 `python -m pytest`，直接 `uv run pytest` 有已知打包问题）；`npx --yes basedpyright backend` 保持 0 errors；`uv run ruff check backend` 通过。
6. 不要 commit。

## documents（backend/tests/test_documents.py）

先读 backend/app/routers/documents.py 确认真实路径前缀（应为 /api/documents）与响应模型字段。

1. **test_upload_document**：登录用户上传小 txt 文件（BytesIO），断言 200，响应含 file_name；mock 掉 parse/ embedding 入库链路（在 vector_store.add_collection 层面 mock）。
2. **test_upload_requires_auth**：不带 token 上传 → 401。
3. **test_upload_filename_none_rejected**：构造 filename 为 None 的上传（httpx 可以发一个没有 filename 的文件 part），断言 400——这正是这次 pyright 修复加的判空，必须有测试锁住。
4. **test_list_documents**：上传 2 个文件后 GET 列表，断言 200 且含 2 条、字段齐。
5. **test_delete_document**：上传后 DELETE，断言 200/204（按实现）；再 GET 确认没了。
6. **test_delete_nonexistent_404**：DELETE 一个不存在的 id → 404（项目有 NotFoundError，确认状态码映射）。

## conversations（backend/tests/test_conversations.py）

先读 backend/app/routers/conversations.py 确认路径与响应字段。

1. **test_list_conversations_empty**：新用户 GET → 200 空数组。
2. **test_conversation_messages**：造一条会话+消息进测试 DB（通过 TestSession 直接插入，或如有现成 POST 接口就走接口；二选一看哪个可行），GET messages → 200 且消息有序。
3. **test_conversation_isolation**：用户 A 的会话，用户 B 查 messages → 404 或空（按实现的真实行为断言，先读代码确认权限检查方式，别猜）。
4. **test_messages_requires_auth**：不带 token → 401。

## 报告要求
完成后汇报：新增测试数、每个测试覆盖的点、验收三条命令的输出摘要。
