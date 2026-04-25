from __future__ import annotations

import logging
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from database import get_uningest_memories, mark_ingested

BASE_DIR = Path(__file__).parent
logger = logging.getLogger(__name__)
PERSIST_DIRECTORY = "chroma_db"
CHROMA_PATH = BASE_DIR / PERSIST_DIRECTORY

_client: chromadb.PersistentClient | None = None
_encoder: SentenceTransformer | None = None
caregiver_collection = None
chat_collection = None
_rag_ready = False


def _initialize_rag() -> None:
    """Initialize Chroma and embedding model using one fixed persist directory."""
    global _client, _encoder, caregiver_collection, chat_collection, _rag_ready
    try:
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _client.heartbeat()

        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
        caregiver_collection = _client.get_or_create_collection("caregiver_memories")
        chat_collection = _client.get_or_create_collection("chat_memories")
        _rag_ready = True
        logger.info("RAG initialized with persist_directory=%s", PERSIST_DIRECTORY)
    except Exception:
        _rag_ready = False
        logger.exception("RAG initialization failed")


_initialize_rag()


def ingest_pending_memories() -> int:
    """Ingest all pending caregiver memories into the vector store."""
    if not _rag_ready or _encoder is None or caregiver_collection is None:
        logger.warning("Skipping memory ingestion because RAG is not ready")
        return 0

    pending = get_uningest_memories()
    if not pending:
        logger.info("RAG ingestion: no pending memories")
        return 0

    count = 0
    for item in pending:
        text = f"[{item['category']}] {item['content']}"
        embedding = _encoder.encode(text).tolist()
        doc_id = f"memory-{item['id']}"
        caregiver_collection.add(
            ids=[doc_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[{"user_id": int(item["user_id"]), "caregiver_id": int(item["caregiver_id"] or 0)}],
        )
        mark_ingested(int(item["id"]), doc_id)
        count += 1
    logger.info("RAG ingestion: ingested %s memory records", count)
    return count


def ingest_chat_message(user_id: int, message_id: int, content: str, role: str) -> None:
    """Index user chat message in vector store for later retrieval."""
    if role != "user" or not _rag_ready or _encoder is None or chat_collection is None:
        return

    text = content
    embedding = _encoder.encode(text).tolist()
    doc_id = f"chat_{message_id}"
    chat_collection.add(
        ids=[doc_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[{"user_id": int(user_id), "message_id": str(message_id), "role": role}],
    )


def retrieve_top_k_memories(user_id: int, query: str, k: int = 3) -> str:
    """Retrieve top-K most relevant memories for the user based on the query.
    Searches both caregiver memory vault AND past chat messages.
    """
    if not _rag_ready or _encoder is None or caregiver_collection is None:
        return ""

    q_emb = _encoder.encode(query).tolist()
    lines: list[str] = []

    # ── 1. Caregiver Memory Vault ──────────────────────────────────────────
    try:
        res = caregiver_collection.query(
            query_embeddings=[q_emb],
            n_results=k,
            where={"user_id": int(user_id)},
        )
        docs = (res.get("documents", [[]]) or [[]])[0]
        dists = (res.get("distances", [[]]) or [[]])[0]
        for doc, dist in zip(docs, dists):
            if dist is None or float(dist) < 0.8:
                lines.append(f"[Memory Vault] {doc}")
    except Exception:
        logger.exception("Caregiver memory retrieval failed")

    # ── 2. Past Chat Messages  ─────────────────────────────────────────────
    if chat_collection is not None:
        try:
            chat_res = chat_collection.query(
                query_embeddings=[q_emb],
                n_results=k,
                where={"user_id": int(user_id)},
            )
            chat_docs = (chat_res.get("documents", [[]]) or [[]])[0]
            chat_dists = (chat_res.get("distances", [[]]) or [[]])[0]
            for doc, dist in zip(chat_docs, chat_dists):
                if dist is None or float(dist) < 1.0:  # slightly looser for chat
                    lines.append(f"[Past conversation] {doc}")
        except Exception:
            logger.exception("Chat memory retrieval failed")

    if not lines:
        return ""

    return "[Relevant context from memory and past conversations:]\n" + "\n".join(lines)


def rag_status() -> str:
    """Return RAG readiness status string for health checks."""
    if not _rag_ready or caregiver_collection is None or chat_collection is None:
        return "not_ready"

    try:
        caregiver_collection.count()
        chat_collection.count()
        return "ready"
    except Exception:
        logger.exception("RAG status check failed")
        return "not_ready"
