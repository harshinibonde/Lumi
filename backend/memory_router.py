from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth_router import get_current_user
from database import add_memory, get_user_memories
from rag import ingest_pending_memories

router = APIRouter(prefix="/memory", tags=["memory"])
logger = logging.getLogger(__name__)


class MemoryRequest(BaseModel):
    category: str
    content: str
    # patient_user_id is accepted but ignored — kept for backward compat
    patient_user_id: int | None = None


@router.post("")
def create_memory(payload: MemoryRequest, current_user: dict = Depends(get_current_user)):
    """Create memory for the authenticated user and synchronously ingest into RAG."""
    try:
        if not payload.category.strip() or not payload.content.strip():
            raise HTTPException(status_code=400, detail="category and content cannot be empty")

        user_id = int(current_user["id"])

        memory_id = add_memory(
            user_id=user_id,
            caregiver_id=user_id,  # self-authored
            category=payload.category,
            content=payload.content,
        )
        ingested = ingest_pending_memories()
        logger.info("Memory endpoint ingested=%s after memory_id=%s", ingested, memory_id)
        return {"memory_id": memory_id}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /memory")
        raise HTTPException(status_code=500, detail="Failed to create memory")


@router.get("")
def list_memories_self(current_user: dict = Depends(get_current_user)):
    """List memories for the authenticated user."""
    try:
        user_id = int(current_user["id"])
        return get_user_memories(user_id)
    except Exception:
        logger.exception("Unhandled error in GET /memory")
        raise HTTPException(status_code=500, detail="Failed to list memories")


# Keep the old path-param endpoint alive for backward compatibility
@router.get("/{patient_user_id}")
def list_memories_legacy(patient_user_id: int, current_user: dict = Depends(get_current_user)):
    """Legacy endpoint — returns the authenticated user's memories regardless of the path param."""
    try:
        user_id = int(current_user["id"])
        return get_user_memories(user_id)
    except Exception:
        logger.exception("Unhandled error in /memory/{patient_user_id}")
        raise HTTPException(status_code=500, detail="Failed to list memories")
