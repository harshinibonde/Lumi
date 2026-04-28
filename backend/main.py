from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from slowapi.errors import RateLimitExceeded
from sklearn.ensemble import VotingClassifier
from starlette.middleware.base import BaseHTTPMiddleware

from analytics_router import router as analytics_router
from auth_router import router as auth_router
from chat_router import llm_status, router as chat_router
from database import get_conn, init_db
from memory_router import router as memory_router
from ml_router import load_model_bundle, models_loaded, router as ml_router
from rag import ingest_pending_memories, rag_status
from rate_limiter import limiter
from screening_router import router as screening_router
from voice_router import router as voice_router

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cognitive AI System API", version="1.0.0")
app.state.limiter = limiter

EXPECTED_FEATURE_COUNT = 14

# ---------------------------------------------------------------------------
# CORS — explicit allow-list for dev + regex for Vercel preview deploys
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

# Only allow Vercel subdomains via regex — the * wildcard in allow_origins
# does NOT work for subdomain matching in CORSMiddleware.
VERCEL_ORIGIN_REGEX = r"https://[\w-]+\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=VERCEL_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=600,  # preflight cache: 10 minutes
)


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add baseline security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(screening_router)
app.include_router(ml_router)
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(memory_router)
app.include_router(analytics_router)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    _ = request
    _ = exc
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup_event() -> None:
    """Initialize DB, model bundle, and RAG index on service startup."""
    init_db()

    if not models_loaded():
        from train_model import train
        train()

    bundle = load_model_bundle()

    required_keys = ["model", "scaler", "imputer", "feature_names"]
    if any(k not in bundle or bundle[k] is None for k in required_keys):
        raise RuntimeError("Model bundle missing required artifacts")

    logger.info("MODEL TYPE: %s", type(bundle["model"]).__name__)
    logger.info("SCALER TYPE: %s", type(bundle["scaler"]).__name__)
    logger.info("IMPUTER TYPE: %s", type(bundle["imputer"]).__name__)

    if not isinstance(bundle["model"], VotingClassifier):
        raise RuntimeError("Invalid model type loaded")

    if len(bundle["feature_names"]) != EXPECTED_FEATURE_COUNT:
        raise RuntimeError("Model feature_names count mismatch")

    app.state.model_bundle = bundle

    # Initialize RAG
    ingested = ingest_pending_memories()
    logger.info("Startup completed: model loaded, pending memories ingested=%s", ingested)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    """Return service readiness status for deployment health checks."""
    db_status = "connected"
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception:
        db_status = "disconnected"

    model_status = "loaded" if getattr(app.state, "model_bundle", None) is not None else "missing"

    return {
        "status": "ok",
        "db": db_status,
        "model": model_status,
        "rag": rag_status(),
        "llm": llm_status(),
    }


# ---------------------------------------------------------------------------
# Debug — force ingest (temporary, remove after debugging)
# ---------------------------------------------------------------------------
@app.get("/debug/ingest")
def debug_ingest() -> dict:
    """Force-run memory ingestion and return detailed status."""
    import os
    from database import get_uningest_memories
    from rag import _rag_ready, caregiver_collection, ingest_pending_memories

    pending_before = get_uningest_memories()
    ingested = ingest_pending_memories()
    pending_after = get_uningest_memories()

    return {
        "chroma_dir": os.getenv("CHROMA_DIR", "NOT_SET"),
        "db_path": os.getenv("DB_PATH", "NOT_SET"),
        "rag_ready": _rag_ready,
        "collection_exists": caregiver_collection is not None,
        "pending_before": len(pending_before),
        "ingested_now": ingested,
        "pending_after": len(pending_after),
    }


@app.get("/debug/reingest")
def debug_reingest() -> dict:
    """Reset all memories to pending=0 and re-ingest into correct ChromaDB path."""
    import os
    from database import get_conn, get_uningest_memories
    from rag import ingest_pending_memories

    # Reset all memories to ingested=0 so they get picked up again
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM caregiver_memories").fetchone()[0]
        conn.execute("UPDATE caregiver_memories SET ingested = 0, embedding_id = NULL")

    ingested = ingest_pending_memories()
    pending_after = get_uningest_memories()

    return {
        "total_memories_reset": total,
        "ingested_now": ingested,
        "pending_after": len(pending_after),
        "chroma_dir": os.getenv("CHROMA_DIR", "NOT_SET"),
    }