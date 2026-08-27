import chromadb


def initializing_client():
    return chromadb.PersistentClient(path="./chroma_db")


def add_collection(client, chunks: list, embedding: list,
                   document_id: int = 0, document_name: str = "",
                   user_id: int = 0):
    collection = client.get_or_create_collection("documents")
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
    return collection


def query_collection(client, embedding: list, top_k: int = 5,
                     user_id: int | None = None):
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
    where = {"document_id": document_id}
    if user_id is not None:
        where["user_id"] = user_id
    collection.delete(where=where)