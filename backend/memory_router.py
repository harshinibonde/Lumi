from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth_router import get_current_user
from database import add_memory, get_user_memories, get_linked_patient_ids
from rag import ingest_pending_memories

router = APIRouter(prefix="/memory", tags=["memory"])
logger = logging.getLogger(__name__)


class MemoryRequest(BaseModel):
    category: str
    content: str
    patient_user_id: int | None = None


def _get_target_user_id(current_user: dict, requested_patient_id: int | None = None) -> int:
    """Determine which user ID the memory belongs to based on role."""
    user_id = int(current_user["id"])
    role = current_user.get("role", "patient")

    if role == "caregiver":
        if requested_patient_id:
            return requested_patient_id
        linked = get_linked_patient_ids(user_id)
        if linked:
            return linked[0]  # default to first linked patient
        raise HTTPException(status_code=400, detail="Caregiver has no linked patients")
    
    return user_id


@router.post("")
def create_memory(payload: MemoryRequest, current_user: dict = Depends(get_current_user)):
    """Create memory for the authenticated user (or their patient) and synchronously ingest into RAG."""
    try:
        if not payload.category.strip() or not payload.content.strip():
            raise HTTPException(status_code=400, detail="category and content cannot be empty")

        target_user_id = _get_target_user_id(current_user, payload.patient_user_id)
        caregiver_id = int(current_user["id"]) if current_user.get("role") == "caregiver" else target_user_id

        memory_id = add_memory(
            user_id=target_user_id,
            caregiver_id=caregiver_id,
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
    """List memories for the authenticated user (or their patient if caregiver)."""
    try:
        target_user_id = _get_target_user_id(current_user)
        return get_user_memories(target_user_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in GET /memory")
        raise HTTPException(status_code=500, detail="Failed to list memories")


# Keep the old path-param endpoint alive for backward compatibility
@router.get("/{patient_user_id}")
def list_memories_legacy(patient_user_id: int, current_user: dict = Depends(get_current_user)):
    """Legacy endpoint — returns the specified patient's memories if caregiver, or self if patient."""
    try:
        target_user_id = _get_target_user_id(current_user, patient_user_id)
        return get_user_memories(target_user_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /memory/{patient_user_id}")
        raise HTTPException(status_code=500, detail="Failed to list memories")

