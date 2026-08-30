async def test_register_and_login(client):
    # 注册
    r = await client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    )
    assert r.status_code == 200
    assert r.json()["username"] == "alice"

    # 用同一凭据登录，应拿到 token
    r = await client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "secret123"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["token"]


async def test_register_duplicate_conflict(client):
    payload = {"username": "bob", "password": "secret123"}
    await client.post("/api/auth/register", json=payload)
    r = await client.post("/api/auth/register", json=payload)
    assert r.status_code == 409
    assert "detail" in r.json()


async def test_login_wrong_password(client):
    await client.post(
        "/api/auth/register",
        json={"username": "carol", "password": "secret123"},
    )
    r = await client.post(
        "/api/auth/login",
        json={"username": "carol", "password": "wrongpass"},
    )
    assert r.status_code == 400


async def test_me_requires_token(client):
    r = await client.get("/api/auth/me")
    assert r.status_code == 401


async def test_me_with_token(client, auth_headers):
    r = await client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "tester"


async def test_unknown_route_404_with_auth(client, auth_headers):
    # 带上有效 token 穿透中间件，路由层找不到匹配才真正返回 404
    r = await client.get("/api/noexistent", headers=auth_headers)
    assert r.status_code == 404
    assert "detail" in r.json()
