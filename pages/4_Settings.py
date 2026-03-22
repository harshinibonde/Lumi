"""Environment and runbook — no chat."""

import streamlit as st

from ui.streamlit_api import BACKEND_URL
from ui.streamlit_state import ensure_session_state
from ui.streamlit_theme import STREAMLIT_PAGE_STYLE

ensure_session_state()
st.markdown(STREAMLIT_PAGE_STYLE, unsafe_allow_html=True)

st.title("Settings")
st.caption("Configuration reference. Change values in `.env` and restart Streamlit + API.")

st.subheader("Backend URL")
st.code(BACKEND_URL, language="text")
st.markdown(
    "Set `COGNITIVE_API_URL` in `.env` if the API is not on this machine (e.g. LAN server)."
)

st.subheader("Run commands")
st.markdown(
    """
**API (terminal 1)**  
`uvicorn app.main:app --reload`

**UI (terminal 2)**  
`streamlit run demo_app.py`
"""
)

st.subheader("Create a user")
st.markdown("Swagger: open `{}/docs` and use **POST /users**.".format(BACKEND_URL.rstrip("/")))

st.subheader("Optional")
st.markdown(
    """
- **Ollama:** `OLLAMA_MODEL`, `OLLAMA_BASE_URL` in `.env`  
- **Scheduler:** `ENABLE_PROACTIVE_SCHEDULER`, `SCHEDULE_HOUR`  
- **Email reminders:** `SMTP_*` (see `.env.example`)  
- **Voice:** `faster-whisper` + `pyttsx3` on the API host  
"""
)
