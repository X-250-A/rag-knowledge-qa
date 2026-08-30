# backend/tests/test_conversations.py
from backend.app.crud import (
    create_conversation,
    find_user_by_username,
    save_message,
)


async def test_list_conversations_empty(client, auth_headers):
    r = await client.get("/api/conversations/", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


async def test_conversation_messages(client, auth_headers, session_factory):
    async with session_factory() as db:
        user = await find_user_by_username(db, "tester")
        assert user is not None
        conv = await create_conversation(db, user.id, "first question")
        conv_id = conv.id
        await save_message(db, conv_id, "user", "first question")
        await save_message(db, conv_id, "assistant", "first answer")

    r = await client.get(f"/api/conversations/{conv_id}/messages", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert [m["role"] for m in body] == ["user", "assistant"]
    assert body[0]["content"] == "first question"
    assert body[1]["content"] == "first answer"


async def test_conversation_isolation(client, auth_headers, session_factory):
    # 注册并登录另一个用户 B
    await client.post("/api/auth/register", json={"username": "bob", "password": "secret123"})
    r = await client.post("/api/auth/login", json={"username": "bob", "password": "secret123"})
    bob_headers = {"Authorization": f"Bearer {r.json()['token']}"}

    # 用户 A（tester）的私密会话 + 消息
    async with session_factory() as db:
        user_a = await find_user_by_username(db, "tester")
        assert user_a is not None
        conv = await create_conversation(db, user_a.id, "private conversation")
        conv_id = conv.id
        await save_message(db, conv_id, "user", "secret message")

    # 用户 B 查 A 的会话消息 → 403（ForbiddenError）
    r = await client.get(f"/api/conversations/{conv_id}/messages", headers=bob_headers)
    assert r.status_code == 403


async def test_messages_requires_auth(client):
    r = await client.get("/api/conversations/1/messages")
    assert r.status_code == 401
