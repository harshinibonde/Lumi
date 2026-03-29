import logging
import os
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from starlette.requests import Request

from cognitive.insights import build_behavioral_insights, sessions_per_day_from_logs
from cognitive.scoring import blended_turn_accuracy
from database.db import (
    create_assessment,
    create_session,
    fetch_latest_assessment,
    fetch_difficulty_history,
    fetch_sessions_per_day,
    fetch_user_task_history,
    get_connection,
    get_user,
    initialize_database,
    log_assessment_answer,
    log_difficulty_change,
    log_task,
    session_belongs_to_user,
)
from notifications.email_reminder import send_cognitive_reminder, smtp_configured
from notifications.email_reminder import send_caregiver_alert
from notifications.email_reminder import send_otp_email
from llm.ollama_client import (
    OllamaGenerationError,
    check_ollama_reachable,
    generate_response,
)
from rag.vector_store import add_memory, retrieve_memory
from app.assessment_data import (
    ASSESSMENT_QUESTIONS,
    classify_score,
    score_answer,
    to_question_payload,
)
from app.screening_pipeline import (
    run_screening_pipeline,
    serialize_pipeline_details,
)
from app.audio_features import extract_audio_features
from app.decision_engine import decide_next_step
from app.otp_utils import generate_otp, generate_session_token, is_otp_valid

logger = logging.getLogger(__name__)


def _parse_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _get_session_record(session_token: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT us.user_id, us.session_token, us.expires_at, u.name
        FROM user_sessions us
        JOIN users u ON u.id = us.user_id
        WHERE us.session_token = ?
        LIMIT 1
        """,
        (session_token,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    expires_at = _parse_datetime(row[2])
    return {
        "user_id": int(row[0]),
        "session_token": row[1],
        "expires_at": expires_at,
        "name": row[3],
    }


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
    if new_difficulty != current_difficulty:
        log_difficulty_change(user_id, current_difficulty, new_difficulty)
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


def run_proactive_session(
    user_id: int, session_type: str, send_email_reminder: bool = False
) -> dict:
    user = get_user(user_id)
    if not user:
        raise ValueError("User not found")
    rag_query = f"{user['name']} {user['caregiver_notes']}".strip() or user["name"]
    context = _memory_context_for_query(rag_query, user_id)
    difficulty = user["difficulty_level"]
    notes = user["caregiver_notes"] or "None provided."
    prompt = f"""You are an expert, empathetic cognitive engagement companion (not a doctor).
You initiate contact to support memory, language, and social cognition through friendly conversation.

User: {user['name']}, age {user['age']}.
Caregiver notes (private): {notes}
Adaptive difficulty level: {difficulty} (1 = very supportive and simple, 5 = richer vocabulary and multi-step prompts).
Retrieved personal context:
{context}

Compose exactly ONE first message: warm greeting using their name when natural, one sentence that ties to memory context if helpful, then ONE clear cognitive-friendly question or mini-activity matching level {difficulty}. Avoid clinical jargon; be concise; do not mention being an AI or difficulty numbers."""
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
        task_focus="",
    )
    if (
        send_email_reminder
        and user.get("email")
        and smtp_configured()
        and os.getenv("REMINDER_EMAIL_ON_SCHEDULED", "true").lower()
        in ("1", "true", "yes")
    ):
        send_cognitive_reminder(user["email"], user["name"], reply)
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
            run_proactive_session(
                uid, "scheduled_proactive", send_email_reminder=True
            )
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    task_focus: str = Field(
        default="",
        max_length=120,
        description="Optional focus e.g. memory_recall, language_fluency, attention",
    )


class SignupRequest(BaseModel):
    name: str
    age: int
    patient_email: Optional[str] = Field(default=None, max_length=200)
    gender: Optional[str] = Field(default=None, max_length=1)
    education_years: Optional[int] = None
    handedness: Optional[str] = Field(default=None, max_length=8)
    native_language: Optional[str] = Field(default=None, max_length=60)
    lives_alone: Optional[bool] = None
    caregiver_name: Optional[str] = Field(default=None, max_length=200)
    caregiver_email: Optional[str] = Field(default=None, max_length=200)
    caregiver_notes: Optional[str] = ""
    email: Optional[str] = Field(default="", max_length=200)


class StartSessionRequest(BaseModel):
    user_id: int


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)


class AssessmentAnswerInput(BaseModel):
    question_id: str
    answer: str | list[str] | dict | None = ""
    input_mode: str = Field(default="text", max_length=16)
    audio_features: list[float] | None = None
    audio_summary: dict | None = None


class AssessmentSubmitRequest(BaseModel):
    user_id: int
    answers: list[AssessmentAnswerInput]
    session_token: str | None = None


class OTPRequest(BaseModel):
    patient_email: str


class OTPVerify(BaseModel):
    user_id: int
    otp: str


class LogoutRequest(BaseModel):
    session_token: str


class CaregiverNotesRequest(BaseModel):
    caregiver_notes: str
    memories: list[str]
    session_token: str


class AudioFeatureResponse(BaseModel):
    transcript: str
    features: dict


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


@app.get("/meta")
def app_meta():
    return {
        "name": "LumiAI",
        "slogan": "Lighting the path to clearer memories.",
    }


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


@app.get("/assessment/questions")
def get_assessment_questions(include_answer: bool = False):
    return {
        "name": "LumiAI Cognitive Screening",
        "total_questions": len(ASSESSMENT_QUESTIONS),
        "total_points": 30,
        "questions": [
            to_question_payload(q, include_answer=include_answer)
            for q in ASSESSMENT_QUESTIONS
        ],
    }


@app.post("/assessment/submit")
def submit_assessment(body: AssessmentSubmitRequest):
    user = get_user(body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not body.session_token:
        logger.warning("assessment/submit called without session_token for user_id=%s", body.user_id)
    else:
        session = _get_session_record(body.session_token)
        expired = not session or not session.get("expires_at") or session["expires_at"] <= datetime.utcnow()
        wrong_user = bool(session and session.get("user_id") != body.user_id)
        if expired or wrong_user:
            logger.warning(
                "assessment/submit received invalid session_token for user_id=%s (prototype mode: continuing)",
                body.user_id,
            )

    answer_map = {item.question_id: item.answer for item in body.answers}
    input_mode_map = {item.question_id: item.input_mode for item in body.answers}
    audio_feature_map = {}
    for item in body.answers:
        if item.audio_summary:
            audio_feature_map[item.question_id] = item.audio_summary
        elif item.audio_features:
            audio_feature_map[item.question_id] = item.audio_features
    score = 0
    detailed_results = []

    for question in ASSESSMENT_QUESTIONS:
        answer = answer_map.get(question.id, "")
        is_correct, user_answer_text = score_answer(question, answer)
        if is_correct:
            score += question.weight
        detailed_results.append(
            {
                "question_id": question.id,
                "question": question.question,
                "category": question.category,
                "weight": question.weight,
                "user_answer": user_answer_text,
                "correct_answer": question.expected_answer
                if question.expected_answer is not None
                else "Open response",
                "is_correct": is_correct,
            }
        )

    score_classification = classify_score(score)
    pipeline_result = run_screening_pipeline(
        score=score,
        score_classification=score_classification,
        detailed_results=detailed_results,
        input_modes=input_mode_map,
        audio_features=audio_feature_map,
        age=int(user.get("age") or 0),
        gender=str(user.get("gender") or "M"),
        education_years=int(user.get("education_years") or 10),
    )
    final_classification = pipeline_result.final_classification
    decision = decide_next_step(final_classification)
    alert_sent = False
    caregiver_target = (user.get("caregiver_email") or user.get("patient_email") or user.get("email") or "").strip()
    if decision.should_alert_caregiver and user and caregiver_target and smtp_configured():
        send_caregiver_alert(
            to_email=caregiver_target,
            user_name=user["name"],
            classification=final_classification,
            score=score,
            decision_action=decision.action,
        )
        alert_sent = True

    assessment_id = create_assessment(
        body.user_id,
        score,
        final_classification,
        score_classification=score_classification,
        ml_classification="",
        final_classification=final_classification,
        svm_classification=pipeline_result.svm_classification,
        random_forest_classification=pipeline_result.random_forest_classification,
        mlp_classification=pipeline_result.mlp_classification,
        decision_action=decision.action,
        caregiver_alert_sent=alert_sent,
        model_confidence=max(
            pipeline_result.svm_confidence,
            pipeline_result.random_forest_confidence,
            pipeline_result.mlp_confidence,
        ),
        model_breakdown=serialize_pipeline_details(pipeline_result),
        pipeline_version=pipeline_result.pipeline_version,
    )
    for row in detailed_results:
        log_assessment_answer(
            assessment_id,
            row["question_id"],
            row["user_answer"],
            row["is_correct"],
        )

    return {
        "assessment_id": assessment_id,
        "score": score,
        "max_score": 30,
        "classification": final_classification,
        "score_classification": score_classification,
        "svm_classification": pipeline_result.svm_classification,
        "random_forest_classification": pipeline_result.random_forest_classification,
        "mlp_classification": pipeline_result.mlp_classification,
        "svm_confidence": round(pipeline_result.svm_confidence, 4),
        "random_forest_confidence": round(
            pipeline_result.random_forest_confidence, 4
        ),
        "mlp_confidence": round(pipeline_result.mlp_confidence, 4),
        "model_probabilities": pipeline_result.model_probabilities,
        "model_outputs": pipeline_result.model_probabilities,
        "pipeline_version": pipeline_result.pipeline_version,
        "decision": decision.to_dict(),
        "caregiver_alert_sent": alert_sent,
        "voice_answer_count": sum(
            1 for mode in input_mode_map.values() if str(mode).lower() == "speech"
        ),
        "redirect_to_support": decision.should_redirect_to_support,
        "results": detailed_results,
    }


@app.post("/assessment/audio/analyze", response_model=AudioFeatureResponse)
async def analyze_assessment_audio(
    audio: UploadFile = File(...),
    language: str | None = None,
):
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
        path.write_bytes(await audio.read())
        try:
            transcript = transcribe_file(str(path), language=language)
        except RuntimeError:
            transcript = ""
        features = extract_audio_features(str(path), transcript=transcript)
        return AudioFeatureResponse(transcript=transcript, features=features)
    finally:
        path.unlink(missing_ok=True)


@app.get("/assessment/latest/{user_id}")
def latest_assessment(user_id: int):
    if not get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    latest = fetch_latest_assessment(user_id)
    if not latest:
        return {"assessment": None}
    return {"assessment": latest}


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
    difficulty_timeline = fetch_difficulty_history(user_id, limit=200)
    sessions_by_day = fetch_sessions_per_day(user_id, days=90)
    interaction_days = sessions_per_day_from_logs(rows)
    insights = build_behavioral_insights(rows)
    return {
        "summary": summary,
        "series": rows,
        "difficulty_timeline": difficulty_timeline,
        "sessions_by_day": sessions_by_day,
        "interaction_events_by_day": interaction_days,
        "insights": insights,
    }


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

    focus_line = (
        f"Session focus (if empty, balance all skills): {request.task_focus.strip() or 'general engagement'}.\n"
    )
    full_prompt = f"""You are a skilled cognitive engagement coach: supportive, patient, clear, never diagnostic.
Adapt vocabulary and step count to difficulty {difficulty} (1=short simple sentences; 5=gentle complexity).
{focus_line}
Personal memory context (RAG):
{context}

User message:
{request.message}

Respond helpfully: acknowledge them, answer or guide the activity, and when appropriate ask one follow-up that fits their level. Do not claim medical authority."""

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
        request.task_focus or "",
    )

    update_difficulty(request.user_id)

    return {
        "response": reply,
        "latency_seconds": round(latency, 2),
        "session_id": session_id,
    }


@app.post("/users")
def create_user(request: SignupRequest):
    def _error(msg: str):
        return JSONResponse(status_code=400, content={"error": msg})

    name = (request.name or "").strip()
    if not name:
        return _error("Name is required")
    if request.age < 50 or request.age > 100:
        return _error("Age must be between 50 and 100")

    legacy_mode = (
        not request.patient_email
        and bool((request.email or "").strip())
        and request.gender is None
        and request.education_years is None
        and request.handedness is None
        and request.native_language is None
        and request.lives_alone is None
        and request.caregiver_name is None
        and request.caregiver_email is None
    )

    patient_email = (request.patient_email or request.email or "").strip()
    if "@" not in patient_email:
        return _error("patient_email must contain '@'")

    if legacy_mode:
        gender = "M"
        education_years = 10
        handedness = "Right"
        native_language = "English"
        lives_alone = False
        caregiver_name = f"{name} Caregiver"
        caregiver_email = f"caregiver_{abs(hash(patient_email)) % 1000000}@example.com"
        caregiver_notes = (request.caregiver_notes or "").strip()
    else:
        gender = (request.gender or "").strip().upper()
        if gender not in ("M", "F"):
            return _error("Gender must be 'M' or 'F'")

        if request.education_years is None or request.education_years < 0 or request.education_years > 25:
            return _error("education_years must be between 0 and 25")
        education_years = int(request.education_years)

        handedness = (request.handedness or "").strip()
        if handedness not in ("Right", "Left"):
            return _error("handedness must be 'Right' or 'Left'")

        native_language = (request.native_language or "").strip()
        if not native_language:
            return _error("native_language is required")

        caregiver_name = (request.caregiver_name or "").strip()
        if not caregiver_name:
            return _error("caregiver_name is required")

        caregiver_email = (request.caregiver_email or "").strip()
        if "@" not in caregiver_email:
            return _error("caregiver_email must contain '@'")
        caregiver_notes = (request.caregiver_notes or "").strip()
        lives_alone = bool(request.lives_alone)

    if patient_email.lower() == caregiver_email.lower():
        return _error("patient_email and caregiver_email must be different")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (
            name, age, caregiver_notes, difficulty_level, email,
            patient_email, caregiver_name, caregiver_email,
            gender, education_years, handedness, native_language,
            lives_alone, otp_code, otp_expires_at, is_verified
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            int(request.age),
            caregiver_notes,
            3,
            (request.email or patient_email).strip() or patient_email,
            patient_email,
            caregiver_name,
            caregiver_email,
            gender,
            education_years,
            handedness,
            native_language,
            1 if lives_alone else 0,
            None,
            None,
            0,
        ),
    )
    user_id = cursor.lastrowid
    otp_code = generate_otp()
    otp_expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    cursor.execute(
        "UPDATE users SET otp_code = ?, otp_expires_at = ? WHERE id = ?",
        (otp_code, otp_expires_at, user_id),
    )
    conn.commit()
    conn.close()

    send_otp_email(patient_email, otp_code, name)
    return {
        "user_id": user_id,
        "name": name,
        "message": "Account created. OTP sent to patient_email.",
    }


@app.post("/auth/request-otp")
def auth_request_otp(body: OTPRequest):
    patient_email = (body.patient_email or "").strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, COALESCE(patient_email, email)
        FROM users
        WHERE LOWER(COALESCE(patient_email, email)) = LOWER(?)
        LIMIT 1
        """,
        (patient_email,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return JSONResponse(status_code=404, content={"error": "No account found with this email"})

    otp_code = generate_otp()
    otp_expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    cursor.execute(
        "UPDATE users SET otp_code = ?, otp_expires_at = ? WHERE id = ?",
        (otp_code, otp_expires_at, int(row[0])),
    )
    conn.commit()
    conn.close()

    send_otp_email(str(row[2] or patient_email), otp_code, str(row[1] or "User"))
    return {"message": "OTP sent to email", "user_id": int(row[0])}


@app.post("/auth/verify-otp")
def auth_verify_otp(body: OTPVerify):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, otp_code, otp_expires_at FROM users WHERE id = ? LIMIT 1",
        (body.user_id,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return JSONResponse(status_code=404, content={"error": "User not found"})

    otp_code = row[2]
    otp_expires_at = row[3]
    valid = False
    try:
        if otp_code and otp_expires_at:
            valid = is_otp_valid(str(otp_code), str(otp_expires_at), str(body.otp))
    except Exception:
        valid = False
    if not valid:
        conn.close()
        return JSONResponse(status_code=400, content={"error": "Invalid or expired OTP"})

    session_token = generate_session_token()
    expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    cursor.execute(
        "UPDATE users SET is_verified = 1, otp_code = NULL, otp_expires_at = NULL WHERE id = ?",
        (body.user_id,),
    )
    cursor.execute(
        """
        INSERT INTO user_sessions (user_id, session_token, expires_at)
        VALUES (?, ?, ?)
        """,
        (body.user_id, session_token, expires_at),
    )
    conn.commit()
    conn.close()
    return {
        "user_id": int(body.user_id),
        "session_token": session_token,
        "name": str(row[1] or ""),
        "message": "Login successful",
    }


@app.post("/auth/logout")
def auth_logout(body: LogoutRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (body.session_token,))
    conn.commit()
    conn.close()
    return {"message": "Logged out successfully"}


@app.get("/auth/validate-session")
def auth_validate_session(session_token: str):
    session = _get_session_record(session_token)
    if not session:
        return JSONResponse(status_code=401, content={"error": "Invalid session"})
    expires_at = session.get("expires_at")
    if not expires_at or expires_at <= datetime.utcnow():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
        conn.commit()
        conn.close()
        return JSONResponse(status_code=401, content={"error": "Session expired"})
    return {
        "user_id": int(session["user_id"]),
        "name": str(session.get("name") or ""),
        "valid": True,
    }


@app.post("/users/{user_id}/caregiver-notes")
def save_caregiver_notes(user_id: int, body: CaregiverNotesRequest):
    session = _get_session_record(body.session_token)
    if not session or not session.get("expires_at") or session["expires_at"] <= datetime.utcnow():
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if int(session["user_id"]) != int(user_id):
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not get_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET caregiver_notes = ? WHERE id = ?",
        ((body.caregiver_notes or "").strip(), user_id),
    )
    conn.commit()
    conn.close()

    stored = 0
    for memory in body.memories or []:
        text = str(memory or "").strip()
        if not text:
            continue
        add_memory(text=text, memory_id=str(uuid.uuid4()), user_id=user_id)
        stored += 1

    return {
        "user_id": int(user_id),
        "memories_stored": stored,
        "message": "Notes and memories saved",
    }
