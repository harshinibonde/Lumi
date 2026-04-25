import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel

from auth_router import get_current_user, require_role
from database import (
    create_chat_session,
    get_user_chat_sessions,
    get_chat_history,
    get_conn,
    get_signals,
    is_caregiver_linked_to_patient,
    save_chat,
)
from rate_limiter import limiter
from rag import ingest_chat_message, ingest_pending_memories, retrieve_top_k_memories
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
    session_id: int
    message: str


class ProactiveRequest(BaseModel):
    session_id: int


def _latest_classification(user_id: int) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT ml_prediction FROM screening_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    return row["ml_prediction"] if row else "Mild"


def _build_prompt(classification: str, context: str, message: str) -> str:
    style = STYLE_MAP.get(classification, STYLE_MAP["Mild"])
    current_time = datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")
    return (
        "You are Lumi, an AI companion for a dementia patient.\n"
        f"Communication mode: {style}\n"
        f"Current Real-World Date and Time: {current_time}\n"
        "You have access to the patient's personal memories and recent conversations below.\n"
        f"Context (ONLY trust what is written here):\n{context}\n\n"
        f"Patient message: {message}\n"
        "Respond with empathy and clarity in 2-4 short sentences.\n"
        "STRICT RULES:\n"
        "1. NEVER invent or assume facts (food, places, names, events) that are not explicitly stated in the Context above.\n"
        "2. If the patient asks about something specific (e.g. what they ate) that is NOT mentioned in the Context, "
        "say warmly that you don\'t have that memory right now, and gently invite them to share it with you.\n"
        "3. Reply ONLY with the spoken message — no notes, disclaimers, or meta-commentary in parentheses or brackets."
    )


def _analyze_and_store_signals(user_id: int, message_id: int, patient_message: str) -> None:
    extract_signals(patient_message, user_id, message_id)


@router.post("/session")
def create_session_endpoint(user: dict = Depends(get_current_user)):
    user_id = int(user["id"])
    session_id = create_chat_session(user_id)
    return {"session_id": session_id}


@router.get("/sessions")
def get_sessions_endpoint(user: dict = Depends(get_current_user)):
    user_id = int(user["id"])
    return get_user_chat_sessions(user_id)


@router.get("/history/{session_id}")
def history(session_id: int, user: dict = Depends(get_current_user)):
    user_id = int(user["id"])
    return get_chat_history(session_id=session_id, limit=30)


@router.post("/message")
@limiter.limit("5/minute")
async def send_message(
    request: Request,
    payload: ChatRequest,
    user: dict = Depends(get_current_user),
):
    try:
        _ = request
        if not (payload.message or "").strip():
            raise HTTPException(status_code=400, detail="message cannot be empty")

        ingest_pending_memories()

        user_id = int(user["id"])
        session_id = payload.session_id
        classification = _latest_classification(user_id)
        context = retrieve_top_k_memories(user_id=user_id, query=payload.message, k=4)

        user_msg_id = save_chat(
            session_id=session_id,
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
                    )
                    if completion.choices and completion.choices[0].message:
                        reply = (completion.choices[0].message.content or "").strip()
                    if reply: break
                except Exception:
                    logger.error("Groq request failed", exc_info=True)

            if not reply:
                reply = GENERIC_FALLBACK_MESSAGE

        save_chat(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=reply,
            rag_context=context,
        )

        ingest_chat_message(user_id, user_msg_id, payload.message, "user")
        _analyze_and_store_signals(user_id, user_msg_id, payload.message)

        return {
            "reply": reply,
            "classification": classification,
            "communication_mode": STYLE_MAP.get(classification),
            "context_used": context,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /chat/message")
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@router.post("/proactive")
async def proactive_message(
    request: Request,
    payload: ProactiveRequest,
    user: dict = Depends(get_current_user),
):
    try:
        _ = request
        user_id = int(user["id"])
        session_id = payload.session_id
        classification = _latest_classification(user_id)
        
        context = retrieve_top_k_memories(user_id=user_id, query="What is something to talk about right now to engage?", k=4)
        style = STYLE_MAP.get(classification, STYLE_MAP["Mild"])
        
        current_time = datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")
        prompt = (
            "You are Lumi, an AI companion for a dementia patient. Start a conversation proactively.\n"
            f"Communication mode: {style}\n"
            f"Current Real-World Date and Time: {current_time}\n"
            "Use the recent memories or state below to pick a relevant, gentle topic.\n"
            f"Context (ONLY trust what is written here):\n{context}\n\n"
            "Respond with a short, warm opener (1-2 sentences) to engage the patient.\n"
            "STRICT RULES:\n"
            "1. NEVER invent or assume facts not explicitly present in the Context above.\n"
            "2. Reply ONLY with the spoken message — no notes, disclaimers, or meta-commentary."
        )

        client, model_name = _get_client_and_model()
        reply = ""
        if client is None:
            reply = "Hello! I was just thinking about you. How is your day going?"
        else:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=150,
                )
                if completion.choices and completion.choices[0].message:
                    reply = (completion.choices[0].message.content or "").strip()
            except Exception:
                logger.error("Proactive Groq request failed", exc_info=True)

        if not reply:
            reply = "Hello! Let's chat."

        save_chat(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=reply,
            rag_context=context,
        )

        return {
            "reply": reply,
            "classification": classification,
            "communication_mode": style,
            "context_used": context,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /chat/proactive")
        raise HTTPException(status_code=500, detail="Failed to initiate proactive chat")


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
