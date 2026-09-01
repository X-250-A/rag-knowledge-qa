import chromadb
import numpy as np


def initializing_client():
    return chromadb.PersistentClient(path="./chroma_db")


def add_collection(
    client,
    chunks: list,
    embedding: np.ndarray,
    document_id: int = 0,
    document_name: str = "",
    user_id: int = 0,
):
    collection = client.get_or_create_collection("documents")
    # document_id 复用问题：SQLite 删文档后自增 id 会被重新分配，
    # 若 chroma 里还留着同 id 的旧记录，add 会撞 ID 静默失败/覆盖。
    # 写入前先清掉同 document_id 的残留，保证 ID 空间干净。
    delete_collection(client, document_id=document_id, user_id=user_id)
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "document_name": document_name,
            "user_id": user_id,
        }
        for _ in chunks
    ]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embedding,
        metadatas=metadatas,
    )
    # 写入自验证：add 后必须回读核对条数，不一致即抛错。
    # 否则 chroma 侧任何异常/丢写都会变成"API 200 + status=ready 但库里 0 条"的静默失败。
    stored = collection.get(ids=ids, include=[])
    if len(stored["ids"]) != len(ids):
        raise RuntimeError(
            f"向量库写入校验失败: 期望 {len(ids)} 条, 实际落库 {len(stored['ids'])} 条 "
            f"(document_id={document_id}, user_id={user_id})"
        )
    return collection


def query_collection(client, embedding: np.ndarray, top_k: int = 5, user_id: int | None = None):
    collection = client.get_or_create_collection("documents")
    where = {"user_id": user_id} if user_id is not None else None
    query = collection.query(
        query_embeddings=embedding,
        n_results=top_k,
        where=where,
    )
    return query


def delete_collection(client, document_id: int, user_id: int | None = None):
    collection = client.get_or_create_collection("documents")
    where: dict
    if document_id is not None and user_id is not None:
        # chroma 1.x 要求多条件必须显式 $and，直接并列两个键会 ValueError
        where = {"$and": [{"document_id": document_id}, {"user_id": user_id}]}
    elif document_id is not None:
        where = {"document_id": document_id}
    elif user_id is not None:
        where = {"user_id": user_id}
    else:
        return
    collection.delete(where=where)
