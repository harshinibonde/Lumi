"""Backend calls for Streamlit pages (no page layout here)."""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BACKEND_URL = os.getenv("COGNITIVE_API_URL", "http://127.0.0.1:8000")
CHAT_ENDPOINT = f"{BACKEND_URL}/chat"
START_SESSION_ENDPOINT = f"{BACKEND_URL}/sessions/start"
TRANSCRIBE_ENDPOINT = f"{BACKEND_URL}/voice/transcribe"
TTS_ENDPOINT = f"{BACKEND_URL}/voice/tts"
HEALTH_ENDPOINTS = [f"{BACKEND_URL}/health", f"{BACKEND_URL}/"]
REQUEST_TIMEOUT = 120

TASK_FOCUS_OPTIONS = [
    "",
    "general engagement",
    "memory_recall",
    "language_fluency",
    "attention",
    "social_conversation",
    "problem_solving",
]


def check_backend_connection() -> bool:
    for url in HEALTH_ENDPOINTS:
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code in (200, 307, 308):
                return True
        except requests.RequestException:
            continue
    return False


def fetch_user_profile(user_id: int) -> dict | None:
    try:
        resp = requests.get(
            f"{BACKEND_URL}/users/{user_id}",
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def fetch_latest_scheduled_opening(user_id: int) -> dict | None:
    try:
        resp = requests.get(
            f"{BACKEND_URL}/users/{user_id}/latest-scheduled-opening",
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def start_proactive_session(user_id: int) -> dict | None:
    import streamlit as st

    try:
        resp = requests.post(
            START_SESSION_ENDPOINT,
            json={"user_id": user_id},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Could not start proactive session: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                st.error(f"Details: {e.response.json()}")
            except Exception:
                st.error(f"HTTP {e.response.status_code}")
        return None


def fetch_llm_health() -> dict | None:
    try:
        r = requests.get(f"{BACKEND_URL}/health/ollama", timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        return None


def send_chat(
    user_id: int,
    message: str,
    session_id: int | None,
    hints_used: int = 0,
    task_focus: str = "",
) -> dict | None:
    payload: dict = {
        "user_id": user_id,
        "message": message,
        "hints_used": hints_used,
        "task_focus": task_focus or "",
    }
    if session_id is not None:
        payload["session_id"] = session_id
    try:
        resp = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        import streamlit as st

        st.error(f"Backend error: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                st.error(f"Details: {e.response.json()}")
            except Exception:
                st.error(f"Status: {e.response.status_code}")
        return None


def transcribe_audio_file(uploaded_name: str, file_bytes: bytes) -> str | None:
    import streamlit as st

    try:
        files = {"audio": (uploaded_name or "clip.wav", file_bytes)}
        r = requests.post(TRANSCRIBE_ENDPOINT, files=files, timeout=REQUEST_TIMEOUT)
        if r.status_code == 501:
            st.warning(r.json().get("detail", "Speech-to-text not available on server."))
            return None
        r.raise_for_status()
        data = r.json()
        return (data.get("text") or "").strip() or None
    except requests.RequestException as e:
        st.error(f"Transcription failed: {e}")
        return None


def fetch_tts_audio(text: str) -> bytes | None:
    import streamlit as st

    try:
        r = requests.post(
            TTS_ENDPOINT,
            json={"text": text},
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code == 501:
            st.warning(r.json().get("detail", "Text-to-speech not available on server."))
            return None
        r.raise_for_status()
        return r.content
    except requests.RequestException as e:
        st.error(f"TTS failed: {e}")
        return None
