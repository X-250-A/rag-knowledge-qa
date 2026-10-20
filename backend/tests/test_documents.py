# backend/tests/test_documents.py
import io

import pytest
from fastapi import UploadFile

from backend.app.exceptions import BadRequestError
from backend.app.routers.documents import upload_documents


async def _upload(client, headers, name, content=b"hello"):
    """上传单文件到 /api/documents/（返回 response）。"""
    return await client.post(
        "/api/documents/",
        headers=headers,
        files={"file": (name, io.BytesIO(content), "text/plain")},
    )


async def test_upload_document(client, auth_headers, mock_rag):
    r = await _upload(client, auth_headers, "note.txt", b"hello world")
    assert r.status_code == 200
    body = r.json()
    assert body["file_name"] == "note.txt"
    assert body["file_type"] == "txt"
    assert body["status"] == "ready"


async def test_upload_requires_auth(client):
    r = await _upload(client, None, "note.txt")
    assert r.status_code == 401


async def test_upload_filename_none_rejected():
    fake = UploadFile(file=io.BytesIO(b"hello world"), filename=None)
    with pytest.raises(BadRequestError) as exc_info:
        await upload_documents(file=fake)
    assert exc_info.value.status_code == 400


async def test_list_documents(client, auth_headers, mock_rag):
    for name in ("a.txt", "b.txt"):
        r = await _upload(client, auth_headers, name)
        assert r.status_code == 200

    r = await client.get("/api/documents/", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert {d["file_name"] for d in body} == {"a.txt", "b.txt"}
    for d in body:
        for field in ("id", "file_name", "file_type", "file_size", "status", "chunk_count"):
            assert field in d


async def test_delete_document(client, auth_headers, mock_rag):
    r = await _upload(client, auth_headers, "del.txt")
    assert r.status_code == 200
    doc_id = r.json()["id"]

    r = await client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert r.status_code == 200

    r = await client.get("/api/documents/", headers=auth_headers)
    assert r.json() == []


async def test_delete_nonexistent_404(client, auth_headers, mock_rag):
    r = await client.delete("/api/documents/999999", headers=auth_headers)
    assert r.status_code == 404
