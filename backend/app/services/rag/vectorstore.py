import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.services.rag.embedding import encode_text, encode_texts

_client = None
_collection = None

COLLECTION_NAME = "hr_documents"


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def add_documents(doc_id: int, chunks: list[dict]):
    collection = get_collection()
    texts = [c["content"] for c in chunks]
    embeddings = encode_texts(texts)
    ids = [f"doc_{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id, "chunk_index": i, "keywords": c.get("keywords", "")} for i, c in enumerate(chunks)]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )


def search_similar(query: str, top_k: int = 5) -> list[dict]:
    collection = get_collection()
    if collection.count() == 0:
        return []

    query_embedding = encode_text(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    items = []
    if results and results["documents"]:
        for i in range(len(results["documents"][0])):
            items.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "score": 1 - results["distances"][0][i]
            })
    return items


def delete_document(doc_id: int):
    collection = get_collection()
    try:
        collection.delete(where={"doc_id": doc_id})
    except Exception:
        pass


def get_collection_stats() -> dict:
    collection = get_collection()
    return {
        "total_chunks": collection.count()
    }
