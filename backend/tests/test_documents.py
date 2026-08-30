# backend/tests/test_documents.py
import io

import pytest
from fastapi import UploadFile

from backend.app.exceptions import BadRequestError
from backend.app.routers.documents import upload_documents


async def test_upload_document(client, auth_headers, mock_rag):
    files = {"file": ("note.txt", io.BytesIO(b"hello world"), "text/plain")}
    r = await client.post("/api/documents/", headers=auth_headers, files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["file_name"] == "note.txt"
    assert body["file_type"] == "txt"
    assert body["status"] == "ready"


async def test_upload_requires_auth(client):
    files = {"file": ("note.txt", io.BytesIO(b"hello world"), "text/plain")}
    r = await client.post("/api/documents/", files=files)
    assert r.status_code == 401


async def test_upload_filename_none_rejected():
    fake = UploadFile(file=io.BytesIO(b"hello world"), filename=None)
    with pytest.raises(BadRequestError) as exc_info:
        await upload_documents(file=fake)
    assert exc_info.value.status_code == 400


async def test_list_documents(client, auth_headers, mock_rag):
    for name in ("a.txt", "b.txt"):
        r = await client.post(
            "/api/documents/",
            headers=auth_headers,
            files={"file": (name, io.BytesIO(b"hello"), "text/plain")},
        )
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
    r = await client.post(
        "/api/documents/",
        headers=auth_headers,
        files={"file": ("del.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert r.status_code == 200
    doc_id = r.json()["id"]

    r = await client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert r.status_code == 200

    r = await client.get("/api/documents/", headers=auth_headers)
    assert r.json() == []


async def test_delete_nonexistent_404(client, auth_headers, mock_rag):
    r = await client.delete("/api/documents/999999", headers=auth_headers)
    assert r.status_code == 404
