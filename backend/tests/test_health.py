async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_unknown_route_requires_auth(client):
    # 中间件先于路由执行：非白名单路径无 token 会先吃 401
    r = await client.get("/api/noexistent")
    assert r.status_code == 401
    assert "detail" in r.json()
