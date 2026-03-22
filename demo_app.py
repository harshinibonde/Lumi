"""
Cognitive AI Engagement System - Streamlit Demo UI
Connects to FastAPI backend at http://127.0.0.1:8000
"""

import io
import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
BACKEND_URL = os.getenv("COGNITIVE_API_URL", "http://127.0.0.1:8000")
CHAT_ENDPOINT = f"{BACKEND_URL}/chat"
START_SESSION_ENDPOINT = f"{BACKEND_URL}/sessions/start"
TRANSCRIBE_ENDPOINT = f"{BACKEND_URL}/voice/transcribe"
TTS_ENDPOINT = f"{BACKEND_URL}/voice/tts"
HEALTH_ENDPOINTS = [f"{BACKEND_URL}/health", f"{BACKEND_URL}/"]
REQUEST_TIMEOUT = 120

# -----------------------------------------------------------------------------
# Custom CSS - Professional Dark Theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Cognitive AI Engagement System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Root - light theme compatible; use Streamlit dark theme in .streamlit/config.toml for full dark */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Main container styling */
    .main .block-container {
        padding: 2rem 3rem 4rem;
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* Title styling */
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        color: #f0f4f8;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .main-subtitle {
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Chat message container */
    .chat-container {
        background: rgba(30, 41, 59, 0.6);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(100, 116, 139, 0.2);
        min-height: 400px;
        max-height: 55vh;
        overflow-y: auto;
        scroll-behavior: smooth;
    }
    
    /* User message bubble */
    .user-bubble {
        background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
        color: white;
        padding: 0.75rem 1.25rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.75rem 0;
        margin-left: auto;
        max-width: 85%;
        font-size: 0.95rem;
        box-shadow: 0 4px 14px rgba(6, 182, 212, 0.3);
    }
    
    /* AI message bubble */
    .ai-bubble {
        background: rgba(51, 65, 85, 0.9);
        color: #e2e8f0;
        padding: 0.75rem 1.25rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.75rem 0;
        margin-right: auto;
        max-width: 85%;
        font-size: 0.95rem;
        border: 1px solid rgba(100, 116, 139, 0.3);
        line-height: 1.6;
    }
    
    /* Latency badge */
    .latency-badge {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.35rem;
        font-weight: 500;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1419 0%, #1a2332 100%);
        border-right: 1px solid rgba(100, 116, 139, 0.15);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #94a3b8;
    }
    
    /* Status indicator */
    .status-connected {
        color: #34d399 !important;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .status-disconnected {
        color: #f87171 !important;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    /* Input area */
    .stTextInput > div > div > input {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(100, 116, 139, 0.3) !important;
        color: #f0f4f8 !important;
        border-radius: 12px !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
        box-shadow: 0 4px 14px rgba(6, 182, 212, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Number input */
    .stNumberInput > div > div > input {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(100, 116, 139, 0.3) !important;
        color: #f0f4f8 !important;
        border-radius: 10px !important;
    }
    
    /* Error message */
    .error-box {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 12px;
        padding: 1rem;
        color: #fca5a5;
        margin: 1rem 0;
    }
    
    /* Scrollbar styling */
    .chat-container::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: rgba(100, 116, 139, 0.5);
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: rgba(100, 116, 139, 0.7);
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Backend Connection
# -----------------------------------------------------------------------------
def check_backend_connection() -> bool:
    """Ping backend to verify it's running."""
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
    try:
        resp = requests.post(
            START_SESSION_ENDPOINT,
            json={"user_id": user_id},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Backend error: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            try:
                st.error(f"Details: {e.response.json()}")
            except Exception:
                st.error(f"Status: {e.response.status_code}")
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
) -> dict | None:
    """POST /chat with optional session_id for a stable conversation session."""
    payload: dict = {
        "user_id": user_id,
        "message": message,
        "hints_used": hints_used,
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
        st.error(f"Backend error: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            try:
                err_detail = e.response.json()
                st.error(f"Details: {err_detail}")
            except Exception:
                st.error(f"Status: {e.response.status_code}")
        return None


def transcribe_audio_file(uploaded_name: str, file_bytes: bytes) -> str | None:
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


def run_chat_turn(message: str, hints_used: int) -> None:
    st.session_state.chat_history.append({"role": "user", "content": message})
    with st.spinner("Thinking..."):
        result = send_chat(
            st.session_state.user_id,
            message,
            st.session_state.session_id,
            hints_used=hints_used,
        )
    if result is not None:
        response_text = result.get("response", "No response received.")
        latency = result.get("latency_seconds", 0.0)
        if result.get("session_id") is not None:
            st.session_state.session_id = result["session_id"]
        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": response_text,
                "latency": latency,
            }
        )
    else:
        st.session_state.chat_history.pop()
        st.error("Failed to get response from backend. See error above.")


# -----------------------------------------------------------------------------
# Session State
# -----------------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_id" not in st.session_state:
    st.session_state.user_id = 1

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "last_sidebar_user_id" not in st.session_state:
    st.session_state.last_sidebar_user_id = st.session_state.user_id


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧠 Session")
    st.markdown("---")
    
    # User ID display
    user_id = st.number_input(
        "User ID",
        min_value=1,
        max_value=9999,
        value=st.session_state.user_id,
        step=1,
        key="sidebar_user_id",
    )
    st.session_state.user_id = user_id

    if st.session_state.last_sidebar_user_id != user_id:
        st.session_state.session_id = None
        st.session_state.chat_history = []
        st.session_state.last_sidebar_user_id = user_id

    st.markdown("---")

    # Backend connection status
    st.markdown("**Connection Status**")
    backend_connected = check_backend_connection()
    if backend_connected:
        st.markdown(
            '<p class="status-connected">● Connected</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<p class="status-disconnected">● Disconnected</p>',
            unsafe_allow_html=True,
        )
        st.caption("Backend not reachable at " + BACKEND_URL)

    if backend_connected:
        st.markdown("**Ollama (LLM)**")
        llm = fetch_llm_health()
        if llm and llm.get("reachable"):
            st.success("Reachable")
            models = llm.get("models") or []
            if models:
                st.caption("Models: " + ", ".join(models[:5]))
        elif llm:
            st.warning("Not reachable — check Ollama / CUDA")
        else:
            st.caption("Could not query /health/ollama")

    hints_used = st.number_input(
        "Hints used (this turn)",
        min_value=0,
        max_value=20,
        value=0,
        step=1,
        help="Logged with each chat turn for analytics.",
    )
    st.session_state["hints_used"] = hints_used

    st.markdown("---")

    st.markdown("**Difficulty Level**")
    if backend_connected:
        profile = fetch_user_profile(user_id)
        if profile:
            d = profile.get("difficulty_level", 1)
            st.metric("Adaptive level", f"{d} / 5")
            st.caption(f"User: **{profile.get('name', '')}**")
        else:
            st.warning("No user with this ID. Create one via POST /users.")
    else:
        st.info("Connect to the backend to load level.", icon="ℹ️")

    st.markdown("**Session**")
    if st.session_state.session_id is not None:
        st.caption(f"Active session id: `{st.session_state.session_id}`")
    else:
        st.caption("No active session — start below or send a message.")

    if backend_connected and st.button(
        "Let AI start the session",
        use_container_width=True,
        help="Proactive opening from the local LLM (same pipeline as scheduler)",
    ):
        if not fetch_user_profile(user_id):
            st.error("Create this user first (API POST /users).")
        else:
            with st.spinner("Generating opening message..."):
                out = start_proactive_session(user_id)
            if out:
                st.session_state.chat_history = []
                st.session_state.session_id = out.get("session_id")
                lat = out.get("latency_seconds", 0.0)
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": out.get("response", ""),
                        "latency": lat,
                    }
                )
                st.rerun()

    st.markdown("---")

    if backend_connected:
        sched = fetch_latest_scheduled_opening(user_id)
        if sched and sched.get("opening"):
            with st.expander("Latest scheduled check-in"):
                st.write(sched["opening"])
                st.caption(f"Session id: {sched.get('session_id')}")

    st.markdown("---")

    with st.expander("Voice", expanded=False):
        st.caption("Requires `faster-whisper` and `pyttsx3` on the API host.")
        up = st.file_uploader(
            "Upload audio (wav/mp3/…)",
            type=["wav", "mp3", "m4a", "webm", "ogg", "flac"],
        )
        if (
            backend_connected
            and up
            and st.button(
                "Transcribe & preview",
                use_container_width=True,
                key="voice_transcribe_btn",
            )
        ):
            txt = transcribe_audio_file(up.name, up.getvalue())
            if txt:
                st.session_state["voice_draft"] = txt
        draft = st.session_state.get("voice_draft")
        if draft:
            edited = st.text_area("Transcript (edit if needed)", value=draft, height=100)
            if st.button(
                "Send transcript as message",
                use_container_width=True,
                key="voice_send_transcript_btn",
            ):
                if not fetch_user_profile(user_id):
                    st.error("Create this user first.")
                else:
                    run_chat_turn(edited.strip(), st.session_state.get("hints_used", 0))
                    st.session_state.pop("voice_draft", None)
                    st.rerun()
        last_ai = next(
            (
                e["content"]
                for e in reversed(st.session_state.chat_history)
                if e.get("role") == "assistant"
            ),
            None,
        )
        if last_ai and st.button(
            "TTS: last AI reply",
            use_container_width=True,
            key="voice_tts_last_btn",
        ):
            if backend_connected:
                audio = fetch_tts_audio(last_ai[:8000])
                if audio:
                    st.audio(io.BytesIO(audio), format="audio/wav")

    st.markdown("---")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.session_id = None
        st.rerun()


# -----------------------------------------------------------------------------
# Main Content
# -----------------------------------------------------------------------------
st.title("🧠 Cognitive AI Engagement System")
st.caption("Adaptive memory-aware cognitive interaction platform")
st.divider()

# Backend not running warning - show early
if not backend_connected:
    st.error(
        "⚠️ **Backend not reachable** — Start the FastAPI server with `uvicorn app.main:app --reload` "
        f"at {BACKEND_URL}"
    )

# Chat messages - use native Streamlit components for reliable rendering
chat_container = st.container()
with chat_container:
    if not st.session_state.chat_history:
        st.info(
            "Use **Let AI start the session** in the sidebar for a proactive opening, "
            "or type a message below. Backend: http://127.0.0.1:8000"
        )
    else:
        for entry in st.session_state.chat_history:
            role = entry["role"]
            with st.chat_message("user" if role == "user" else "assistant", avatar="🧑" if role == "user" else "🤖"):
                st.write(entry["content"])
                if role == "assistant" and "latency" in entry and entry["latency"] is not None:
                    st.caption(f"⏱ {entry['latency']:.2f}s")

# Chat input - native component pinned to bottom
user_message = st.chat_input("Type your message here...")

if user_message and user_message.strip():
    if not backend_connected:
        st.error("Cannot send: backend is not connected. Start the server first.")
    else:
        # Add user message to history
        run_chat_turn(
            user_message.strip(),
            st.session_state.get("hints_used", 0),
        )
        st.rerun()
