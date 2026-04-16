import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel

from auth_router import get_current_user, require_role
from database import (
    add_memory,
    get_chat_history,
    get_conn,
    get_signals,
    get_user_by_id,
    get_user_memories,
    is_caregiver_linked_to_patient,
    save_chat,
)
from rate_limiter import limiter
from rag import ingest_chat_message, ingest_pending_memories, retrieve_context
from signal_extractor import extract_signals
            
router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
LLM_RETRY_COUNT = 1

CONFIG_FALLBACK_MESSAGE = "Chat service is not configured yet. Please try again later."
GENERIC_FALLBACK_MESSAGE = (
    "I'm here with you. Would you like help with something, or would you like to talk?"
)


def _has_valid_groq_key(value: str) -> bool:
    key = (value or "").strip()
    if not key:
        return False
    if key.lower().startswith("your-"):
        return False
    return True


def _get_client_and_model() -> tuple[Groq | None, str]:
    api_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY)
    model_name = os.getenv("GROQ_MODEL", GROQ_MODEL)
    if not _has_valid_groq_key(api_key):
        return None, model_name
    try:
        return Groq(api_key=api_key, timeout=LLM_TIMEOUT_SECONDS, max_retries=0), model_name
    except TypeError:
        # Backward-compatible construction for older SDK versions.
        return Groq(api_key=api_key), model_name


def llm_status() -> str:
    """Return high-level LLM configuration status for health checks."""
    return "configured" if _has_valid_groq_key(os.getenv("GROQ_API_KEY", GROQ_API_KEY)) else "missing"

STYLE_MAP = {
    "Normal": "Coach: concise, encouraging, challenge-oriented.",
    "Mild": "Guide: gentle structure, short reminders, confirm understanding.",
    "Moderate": "Comfort: calm, reassuring, one-step instructions.",
    "Severe": "Presence: very simple, warm, grounding, low cognitive load.",
}


class ChatRequest(BaseModel):
    message: str


class MemoryRequest(BaseModel):
    patient_user_id: int
    category: str
    content: str


def _latest_classification(user_id: int) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT ml_prediction FROM screening_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    return row["ml_prediction"] if row else "Mild"


def _build_prompt(classification: str, context: str, message: str) -> str:
    style = STYLE_MAP.get(classification, STYLE_MAP["Mild"])
    return (
        "You are an AI companion for a dementia patient.\n"
        f"Communication mode: {style}\n"
        "Ground your response in personal memory and recent conversation.\n"
        f"Context:\n{context}\n\n"
        f"Patient message: {message}\n"
        "Respond with empathy and clarity in 2-4 short sentences."
    )


def _analyze_and_store_signals(user_id: int, message_id: int, patient_message: str) -> None:
    extract_signals(patient_message, user_id, message_id)


def _send_message_impl(
    payload: ChatRequest,
    user: dict = Depends(get_current_user),
):
    if not (payload.message or "").strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    ingest_pending_memories()

    user_id = int(user["id"])
    classification = _latest_classification(user_id)
    context = retrieve_context(user_id=user_id, query=payload.message, n_results=4)

    user_msg_id = save_chat(
        user_id=user_id,
        role="user",
        content=payload.message,
        rag_context=context,
    )

    prompt = _build_prompt(classification, context, payload.message)
    client, model_name = _get_client_and_model()
    reply = ""
    if client is None:
        logger.warning("Chat fallback used: GROQ_API_KEY missing")
        reply = CONFIG_FALLBACK_MESSAGE
    else:
        for attempt in range(LLM_RETRY_COUNT + 1):
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=220,
                    timeout=LLM_TIMEOUT_SECONDS,
                )

                if completion.choices and completion.choices[0].message:
                    reply = (completion.choices[0].message.content or "").strip()

                if reply:
                    break

                logger.warning("Groq returned empty reply on attempt %s", attempt + 1)
            except Exception:
                logger.error("Groq request failed on attempt %s", attempt + 1, exc_info=True)

        if not reply:
            logger.warning("Chat fallback used: Groq request failed after retry")
            reply = GENERIC_FALLBACK_MESSAGE

    if not reply:
        reply = GENERIC_FALLBACK_MESSAGE

    save_chat(
        user_id=user_id,
        role="assistant",
        content=reply,
        rag_context=context,
    )

    # Keep ingestion and signals robust in-process for predictable reliability.
    ingest_chat_message(user_id, user_msg_id, payload.message, "user")
    _analyze_and_store_signals(user_id, user_msg_id, payload.message)

    return {
        "reply": reply,
        "classification": classification,
        "communication_mode": STYLE_MAP.get(classification),
        "context_used": context,
    }


@router.post("/send")
@limiter.limit("5/minute")
async def send_message(
    request: Request,
    payload: ChatRequest,
    user: dict = Depends(get_current_user),
):
    """Send a chat message and return assistant reply with context metadata."""
    try:
        _ = request
        return _send_message_impl(payload, user)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /chat/send")
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@router.post("/message")
@limiter.limit("5/minute")
async def message(
    request: Request,
    payload: ChatRequest,
    user: dict = Depends(get_current_user),
):
    """Alias of /chat/send for frontend compatibility."""
    try:
        _ = request
        return _send_message_impl(payload, user)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /chat/message")
        raise HTTPException(status_code=500, detail="Failed to process chat message")



@router.get("/history")
def history(user: dict = Depends(get_current_user)):
    """Return recent chat history for the authenticated patient."""
    return get_chat_history(user_id=int(user["id"]), limit=30)


@router.get("/signals/{user_id}")
def signals(user_id: int, current_user: dict = Depends(get_current_user)):
    """Return signal analytics for self, or linked patient if caller is caregiver."""
    caller_id = int(current_user["id"])
    if caller_id != user_id:
        if current_user.get("role") != "caregiver":
            raise HTTPException(status_code=403, detail="Forbidden")
        if not is_caregiver_linked_to_patient(caller_id, user_id):
            raise HTTPException(status_code=403, detail="Caregiver is not linked to this patient")

    rows = get_signals(user_id=user_id, days=90)

    with get_conn() as conn:
        msg_rows = conn.execute(
            "SELECT id, content FROM chat_history WHERE user_id = ? AND role = 'user'",
            (user_id,),
        ).fetchall()
    msg_lookup = {int(r["id"]): r["content"] for r in msg_rows}

    parsed = []
    for row in rows:
        item = dict(row)
        keywords = item.get("alert_keywords")
        if isinstance(keywords, str):
            try:
                item["alert_keywords"] = json.loads(keywords)
            except json.JSONDecodeError:
                item["alert_keywords"] = []
        item["message_excerpt"] = (msg_lookup.get(int(item.get("message_id") or 0), "") or "")[:180]
        parsed.append(item)

    daily_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    weekly_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for item in parsed:
        dt = datetime.fromisoformat(str(item["created_at"]).replace("Z", "+00:00"))
        day_key = dt.date().isoformat()
        week_key = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"
        daily_bucket[day_key].append(item)
        weekly_bucket[week_key].append(item)

    def _avg(records: list[dict[str, Any]], key: str) -> float:
        values = [float(r.get(key) or 0) for r in records]
        return sum(values) / max(len(values), 1)

    daily_averages = [
        {
            "date": k,
            "confusion_score": _avg(v, "confusion_score"),
            "sentiment_score": _avg(v, "sentiment_score"),
        }
        for k, v in sorted(daily_bucket.items())
    ]

    weekly_averages = [
        {
            "week": k,
            "response_length": _avg(v, "response_length"),
            "vocabulary_diversity": _avg(v, "vocabulary_diversity"),
        }
        for k, v in sorted(weekly_bucket.items())
    ]

    alert_count = sum(1 for r in parsed if r.get("alert_keywords"))

    return {
        "signals": parsed,
        "daily_averages": daily_averages,
        "weekly_averages": weekly_averages,
        "alert_count": alert_count,
    }


@router.post("/memory")
def create_memory(payload: MemoryRequest, caregiver: dict = Depends(require_role("caregiver"))):
    """Create a caregiver memory and synchronously ingest it into RAG."""
    try:
        if not payload.category.strip() or not payload.content.strip():
            raise HTTPException(status_code=400, detail="category and content cannot be empty")

        patient = get_user_by_id(int(payload.patient_user_id))
        if not patient or patient.get("role") != "patient":
            raise HTTPException(status_code=400, detail="patient_user_id must refer to a valid patient")

        memory_id = add_memory(
            user_id=payload.patient_user_id,
            caregiver_id=int(caregiver["id"]),
            category=payload.category,
            content=payload.content,
        )
        ingested = ingest_pending_memories()
        logger.info("Chat memory endpoint ingested=%s after memory_id=%s", ingested, memory_id)
        return {"memory_id": memory_id}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /chat/memory")
        raise HTTPException(status_code=500, detail="Failed to create memory")


@router.get("/memory/{patient_user_id}")
def list_memory(patient_user_id: int, caregiver: dict = Depends(require_role("caregiver"))):
    """Return memory list for a caregiver-linked patient."""
    try:
        caregiver_id = int(caregiver["id"])
        if not is_caregiver_linked_to_patient(caregiver_id, int(patient_user_id)):
            raise HTTPException(status_code=403, detail="Caregiver is not linked to this patient")
        return get_user_memories(patient_user_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /chat/memory/{patient_user_id}")
        raise HTTPException(status_code=500, detail="Failed to list memories")
