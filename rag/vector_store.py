import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

_CHROMA_DIR = os.getenv(
    "CHROMA_PERSIST_DIR", str(_PROJECT_ROOT / "chroma_storage")
)
_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

embedding_model = SentenceTransformer(_EMBEDDING_MODEL)

client = chromadb.Client(Settings(persist_directory=_CHROMA_DIR))
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