# 工程化排错实录：类型检查接入 + CI 首跑全复盘（2026-08-30）

> 用途：简历素材 / 面试复盘。本次工作为 rag-knowledge-qa 接入 pyright 类型检查、
> 补充核心链路测试、首次跑通 GitHub Actions CI。过程中挖出的每一层问题及根因如下。

## 一、类型层：basedpyright 首扫 18 条（0 errors 收敛）

**工具链**：pyright（basic 模式，挂在 pre-commit + CI 双门禁）。
首扫 54 文件 18 errors，全部修复，分五类根因：

1. **变量遮蔽导致的类型歧义（routers/auth.py）**
   - `user: LoginRequest` 参数被 `user = await verify_user(...)`（返回 `User | None`）重赋值。
   - 运行时碰巧能跑，但类型上 `user.id` 指向错误对象。改名 `db_user` + 判空收窄解决。
   - **教训：参数复用同名变量遮蔽，是"能跑但高危"的典型。**

2. **外部输入的可空性没有在边界拦截（routers/documents.py）**
   - `UploadFile.filename: str | None`、`size: int | None`，直接拼路径/入库。
   - filename 为 None 时会拼出非法路径。修法：入口判空抛 400（BadRequestError）。
   - **教训：类型检查器把"没处理用户输入的异常形态"暴露为类型问题，这恰是它的价值。**

3. **外部调用返回值可空未判（services/retriever.py）**
   - chromadb 的 query 结果字段类型是 `list | None`，代码直接下标。
   - 修法：提取字段统一判空，None 时返回空列表。

4. **标注与实际数据形状不符（vector_store / conversation / RAG_agent）**
   - embedding 形参标 `list` 实际传 `np.ndarray` → 改标注；
   - `token_counter: Callable[[int], int]` 实际回调传 str 且可 None → 标注改对 + 调用点判空回退；
   - openai `messages.create` 的消息列表 → 显式标注 `list[ChatCompletionMessageParam]`，
     类型对齐后还暴露出 `content` 可能为 None 的潜在炸点，加判空。
   - **教训：很多"类型错误"其实是文档——标注修对后，隐藏的逻辑漏洞跟着浮出来。**

5. **框架泛型签名不匹配（exceptions.py）+ 库 stub 误报（llm_client.py）**
   - Starlette `add_exception_handler` 的 handler 签名要求 `Exception`，收窄为 `AppError` 不兼容
     → 参数放宽 + 函数体内 `cast` 回窄类型，运行时不变；
   - openai>=3.x 把 `http_client` 标注为 `httpx2.AsyncClient` 但运行时兼容 `httpx.AsyncClient`
     （源码确认有 `is_legacy_httpx_async_client` 分支）→ 唯一一处 `# type: ignore`，注明原因。
   - **教训：ignore 是最后手段，且必须留注释说明为什么误报。**

## 二、仓库层：.gitignore 误伤，ORM 模型从未进版本库（最严重）

**现象**：本地全绿，CI 首跑 test job 立挂 `ModuleNotFoundError: No module named 'backend.app.models'`。

**根因**：`.gitignore` 写了通配的 `models/`（本意是忽略本地 LLM 权重缓存），
gitignore 规则匹配**任意层级**目录，把 `backend/app/models/`（SQLAlchemy ORM 模型源码）
整个挡在了版本库外。本地能跑纯粹因为文件物理存在，任何 clone/CI 环境必炸。

**修法**：改为锚定规则 `/models/` + `**/hf-models/`，并把 7 个模型文件补入 git。

**教训**：这条属于"环境依赖型 bug"——只在非本机环境暴露。
**CI 的价值第一次真实兑现：它模拟的是"别人 clone 你的仓库"，是唯一能拦住这类问题的门禁。**

## 三、CI 层：两轮失败，两类根因

1. **pyright hook 在 CI 报 66 个 reportMissingImports**
   - 本地排查时用 `--pythonpath .venv/Scripts/python.exe`（Windows 路径）修好本地、搞挂 CI。
   - 正解：`[tool.pyright] venvPath="." / venv=".venv"`，pyright 自辨 bin/Scripts，跨平台。
   - 另外 lint job 原来不装依赖就跑 pre-commit，pyright 无 venv 可解析 → 补 `uv sync`。
   - **教训：修环境问题不要用平台专属路径写死；每个 job 都是独立环境，依赖要自足。**

2. **test job：embedding.py 在 import 时加载 2.3GB 模型**
   - 模块顶层 `model = SentenceTransformer("BAAI/bge-m3")`，import 链：
     conftest → main → routers → services → embedding → **联网拉权重** → CI 断网必炸。
   - 修法：惰性加载（全局变量 + 首次调用 `_get_model()` 才初始化）。
     测试 mock 的正是 `get_embedding`，从此 import 不再触发模型加载。
   - **教训：模块级副作用（import 即执行的 IO/下载/加载）是可测试性的头号杀手；
     惰性初始化一行改动，测试速度和 CI 稳定性同时受益。**

## 四、流程层

- pytest 打包问题：`uv run pytest` 找不到 `backend` 包（setuptools packages.find 配置所致），
  `python -m pytest` 可绕过——CI 命令统一用后者。
- 修复纪律：全部类型修复仅限判空/标注/改名，无一行业务逻辑变更；
  每轮改动本地三重验证（pytest 18 passed / pyright 0 errors / pre-commit 全 Passed）后才 push。

## 最终状态

- pyright：18 errors → **0**，挂入 pre-commit + CI 双门禁
- 测试：8 → **18**（新增 documents 全链路 + conversations 含越权隔离用例，RAG 重依赖全 mock）
- CI：GitHub Actions（ruff + pre-commit + pyright + pytest）从全红到绿
- 面试一句话版本：**"为 RAG 问答平台接入 pyright + CI，通过类型检查和 CI 环境差异
  挖出并修复了 .gitignore 误伤导致 ORM 模型未入库、模块级模型加载破坏可测试性等
  六类问题，最终 18 条类型错误清零、测试翻倍、CI 全绿。"**
