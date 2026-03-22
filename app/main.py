import logging
import os
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from starlette.requests import Request

from cognitive.scoring import blended_turn_accuracy
from database.db import (
    create_session,
    fetch_user_task_history,
    get_connection,
    get_user,
    initialize_database,
    log_task,
    session_belongs_to_user,
)
from llm.ollama_client import (
    OllamaGenerationError,
    check_ollama_reachable,
    generate_response,
)
from rag.vector_store import add_memory, retrieve_memory

logger = logging.getLogger(__name__)


def update_difficulty(user_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT tl.accuracy
        FROM task_logs tl
        JOIN sessions s ON tl.session_id = s.id
        WHERE s.user_id = ? AND tl.task_type = 'chat_turn'
        ORDER BY tl.id DESC
        LIMIT 5
        """,
        (user_id,),
    )
    results = cursor.fetchall()
    if not results:
        conn.close()
        return

    avg_accuracy = sum(r[0] for r in results) / len(results)
    cursor.execute("SELECT difficulty_level FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    current_difficulty = row[0]
    new_difficulty = current_difficulty
    if avg_accuracy > 0.8 and current_difficulty < 5:
        new_difficulty += 1
    elif avg_accuracy < 0.5 and current_difficulty > 1:
        new_difficulty -= 1
    cursor.execute(
        "UPDATE users SET difficulty_level = ? WHERE id = ?",
        (new_difficulty, user_id),
    )
    conn.commit()
    conn.close()


def _memory_context_for_query(query: str, user_id: int) -> str:
    memories = retrieve_memory(query, user_id)
    if memories:
        return "\n".join(memories)
    return "(No relevant memories stored yet.)"


def run_proactive_session(user_id: int, session_type: str) -> dict:
    user = get_user(user_id)
    if not user:
        raise ValueError("User not found")
    rag_query = f"{user['name']} {user['caregiver_notes']}".strip() or user["name"]
    context = _memory_context_for_query(rag_query, user_id)
    difficulty = user["difficulty_level"]
    notes = user["caregiver_notes"] or "None provided."
    prompt = f"""You are a warm cognitive engagement companion starting a new conversation.
The user is {user['name']}, age {user['age']}.
Caregiver context (private): {notes}
Current cognitive activity difficulty level: {difficulty} (1 = very easy, 5 = challenging).
Relevant long-term memory snippets:
{context}

Instructions: Send ONE opening message only. Greet them by name if it feels natural, briefly acknowledge something from memory if relevant, then include one gentle cognitive prompt or question suited to difficulty level {difficulty}. Keep it concise and friendly."""
    start = time.time()
    reply = generate_response(prompt)
    latency = time.time() - start
    session_id = create_session(user_id, session_type)
    log_task(
        session_id,
        "proactive_open",
        "[proactive_start]",
        reply,
        accuracy=0.75,
        latency=latency,
        hints_used=0,
    )
    return {
        "response": reply,
        "session_id": session_id,
        "latency_seconds": round(latency, 2),
    }


def scheduled_opening_job() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    user_ids = [r[0] for r in cursor.fetchall()]
    conn.close()
    for uid in user_ids:
        try:
            run_proactive_session(uid, "scheduled_proactive")
            logger.info("Scheduled proactive session created for user %s", uid)
        except Exception:
            logger.exception("Scheduled proactive failed for user %s", uid)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    scheduler = BackgroundScheduler()
    scheduler_started = False
    if os.getenv("ENABLE_PROACTIVE_SCHEDULER", "").lower() in ("1", "true", "yes"):
        hour = int(os.getenv("SCHEDULE_HOUR", "9"))
        minute = int(os.getenv("SCHEDULE_MINUTE", "0"))
        scheduler.add_job(
            scheduled_opening_job,
            "cron",
            hour=hour,
            minute=minute,
            id="proactive_daily",
            replace_existing=True,
        )
        scheduler.start()
        scheduler_started = True
        logger.info(
            "Proactive scheduler on: daily at %02d:%02d (server local time)",
            hour,
            minute,
        )
    yield
    if scheduler_started:
        scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)


@app.exception_handler(OllamaGenerationError)
async def ollama_generation_error_handler(
    request: Request, exc: OllamaGenerationError
):
    return JSONResponse(
        status_code=503,
        content={
            "detail": exc.message,
            "error": "ollama",
        },
    )


class ChatRequest(BaseModel):
    user_id: int
    message: str
    session_id: int | None = None
    hints_used: int = Field(default=0, ge=0)


class CreateUserRequest(BaseModel):
    name: str
    age: int
    caregiver_notes: str = ""


class StartSessionRequest(BaseModel):
    user_id: int


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)


@app.get("/health")
def health():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}


@app.get("/health/ollama")
def health_ollama():
    return check_ollama_reachable()


@app.get("/")
def root():
    return {"message": "Cognitive AI System Running"}


@app.get("/users")
def list_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, age, difficulty_level FROM users")
    users = cursor.fetchall()
    conn.close()
    return {
        "users": [
            {
                "id": u[0],
                "name": u[1],
                "age": u[2],
                "difficulty_level": u[3],
            }
            for u in users
        ]
    }


@app.get("/users/{user_id}")
def user_profile(user_id: int):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/{user_id}/analytics")
def user_analytics(user_id: int, limit: int = 500):
    if not get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if limit < 1 or limit > 2000:
        raise HTTPException(status_code=400, detail="limit must be 1–2000")
    rows = fetch_user_task_history(user_id, limit=limit)
    chat_rows = [r for r in rows if r["task_type"] == "chat_turn"]
    latencies = [r["latency"] for r in chat_rows if r["latency"] is not None]
    accs = [r["accuracy"] for r in chat_rows if r["accuracy"] is not None]
    summary = {
        "total_logs": len(rows),
        "chat_turns": len(chat_rows),
        "proactive_opens": sum(1 for r in rows if r["task_type"] == "proactive_open"),
        "avg_latency_chat": round(sum(latencies) / len(latencies), 3) if latencies else None,
        "avg_accuracy_chat": round(sum(accs) / len(accs), 3) if accs else None,
        "current_difficulty": get_user(user_id)["difficulty_level"],
    }
    sessions_count = len({r["session_timestamp"] + r["session_type"] for r in rows})
    summary["approx_distinct_sessions"] = sessions_count
    return {"summary": summary, "series": rows}


@app.get("/users/{user_id}/latest-scheduled-opening")
def latest_scheduled_opening(user_id: int):
    if not get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT tl.assistant_message, s.id
        FROM task_logs tl
        JOIN sessions s ON tl.session_id = s.id
        WHERE s.user_id = ?
          AND s.session_type = 'scheduled_proactive'
          AND tl.task_type = 'proactive_open'
        ORDER BY tl.id DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"opening": None, "session_id": None}
    return {"opening": row[0], "session_id": row[1]}


@app.post("/voice/transcribe")
async def voice_transcribe(audio: UploadFile = File(...)):
    from voice.stt import transcribe_file

    suffix = Path(audio.filename or "clip.wav").suffix or ".wav"
    if suffix.lower() not in (".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio type; try wav, mp3, m4a, webm, ogg, flac",
        )
    fd, path_str = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    path = Path(path_str)
    try:
        data = await audio.read()
        path.write_bytes(data)
        try:
            text = transcribe_file(str(path))
        except RuntimeError as e:
            raise HTTPException(status_code=501, detail=str(e)) from e
        return {"text": text}
    finally:
        path.unlink(missing_ok=True)


@app.post("/voice/tts")
def voice_tts(body: TtsRequest):
    from voice.tts import synthesize_wav_bytes

    try:
        wav = synthesize_wav_bytes(body.text)
    except RuntimeError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return Response(content=wav, media_type="audio/wav")


@app.post("/sessions/start")
def start_session(body: StartSessionRequest):
    try:
        return run_proactive_session(body.user_id, "proactive_manual")
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found") from None


@app.post("/chat")
def chat(request: ChatRequest):
    if not get_user(request.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if request.session_id is not None and not session_belongs_to_user(
        request.session_id, request.user_id
    ):
        raise HTTPException(
            status_code=400, detail="session_id does not belong to this user"
        )

    start_time = time.time()
    session_id = request.session_id

    context = _memory_context_for_query(request.message, request.user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT difficulty_level FROM users WHERE id = ?", (request.user_id,)
    )
    difficulty = cursor.fetchone()[0]
    conn.close()

    full_prompt = f"""
    You are conducting a cognitive training session.
    Current difficulty level: {difficulty}
    (1 = very easy, 5 = very challenging)
    Use the following memory context to answer:
    {context}
    User question:
    {request.message}
    """

    reply = generate_response(full_prompt)
    latency = time.time() - start_time

    if session_id is None:
        session_id = create_session(request.user_id, "chat")

    add_memory(
        text=request.message,
        memory_id=str(uuid.uuid4()),
        user_id=request.user_id,
    )

    accuracy = blended_turn_accuracy(request.message, reply)
    log_task(
        session_id,
        "chat_turn",
        request.message,
        reply,
        accuracy,
        latency,
        request.hints_used,
    )

    update_difficulty(request.user_id)

    return {
        "response": reply,
        "latency_seconds": round(latency, 2),
        "session_id": session_id,
    }


@app.post("/users")
def create_user(request: CreateUserRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (name, age, caregiver_notes)
        VALUES (?, ?, ?)
        """,
        (request.name, request.age, request.caregiver_notes),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "message": "User created successfully",
        "user_id": user_id,
        "difficulty_level": 1,
    }
