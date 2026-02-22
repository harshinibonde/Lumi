import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.Client(Settings(persist_directory="./chroma_storage"))
collection = client.get_or_create_collection(name="memory_collection")


def add_memory(text: str, memory_id: str, user_id: int):
    embedding = embedding_model.encode(text).tolist()

    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[memory_id],
        metadatas=[{"user_id": user_id}]
    )


def retrieve_memory(query: str, user_id: int, top_k: int = 3):
    query_embedding = embedding_model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"user_id": user_id}
    )

    return results["documents"][0] if results["documents"] else []