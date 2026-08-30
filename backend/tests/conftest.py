# backend/tests/conftest.py
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.app.db import get_db
from backend.app.main import app
from backend.app.models import Base


@pytest_asyncio.fixture
async def session_factory():
    # —— 决策1：内存库 + StaticPool ——
    # sqlite+aiosqlite:///:memory: 每个连接会看到"不同的空库"，
    # 加 StaticPool 让所有会话复用同一条连接，建的表才共享。
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # ← 关键
    )

    # 在测试引擎上建表（不碰开发库的 engine）
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory):
    # —— 决策2：dependency_overrides ——
    # 不碰路由代码，把 get_db 依赖整个换成测试会话工厂
    async def override_get_db():
        async with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()  # 用完全覆盖，别让测试互相污染


@pytest_asyncio.fixture
async def auth_headers(client):
    # 复用 client fixture：注册一个测试用户，登录拿 token，返回鉴权头
    await client.post(
        "/api/auth/register",
        json={"username": "tester", "password": "secret123"},
    )
    r = await client.post(
        "/api/auth/login",
        json={"username": "tester", "password": "secret123"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def mock_rag(monkeypatch):
    # 在 app 层把解析/embedding/向量库等重依赖替换掉，
    # 不调真实模型、不连真实 chroma（上传/删除链路都会用到）。
    import backend.app.rag.pipeline as pipeline
    import backend.app.routers.documents as documents

    monkeypatch.setattr(documents, "parse_file", lambda path: "hello world")
    monkeypatch.setattr(documents, "initializing_client", lambda: object())
    monkeypatch.setattr(documents, "delete_collection", lambda *args, **kwargs: None)
    monkeypatch.setattr(pipeline, "get_embedding", lambda chunks: [0.0] * len(chunks))
    monkeypatch.setattr(pipeline, "initializing_client", lambda: object())
    monkeypatch.setattr(pipeline, "add_collection", lambda *args, **kwargs: None)
