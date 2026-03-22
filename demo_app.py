"""
Home — overview and navigation only.
Run: streamlit run demo_app.py
Then use the sidebar pages: Chat, Analytics, Voice, Settings.
"""

import streamlit as st

from ui.streamlit_api import (
    BACKEND_URL,
    check_backend_connection,
    fetch_llm_health,
)
from ui.streamlit_state import ensure_session_state
from ui.streamlit_theme import STREAMLIT_PAGE_STYLE, home_nav_cards_html

st.set_page_config(
    page_title="Cognitive Companion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

ensure_session_state()
st.markdown(STREAMLIT_PAGE_STYLE, unsafe_allow_html=True)

st.markdown('<span class="pill">Local · Private</span>', unsafe_allow_html=True)
st.title("Cognitive companion")
st.caption("Structured workspace: pick a section in the sidebar.")

api_ok = check_backend_connection()
llm = fetch_llm_health() if api_ok else None

c1, c2 = st.columns(2)
with c1:
    st.markdown("**API**")
    if api_ok:
        st.markdown('<p class="status-ok">Reachable</p>', unsafe_allow_html=True)
        st.caption(BACKEND_URL)
    else:
        st.markdown('<p class="status-bad">Offline</p>', unsafe_allow_html=True)
        st.caption(f"Start: `uvicorn app.main:app --reload` → {BACKEND_URL}")
with c2:
    st.markdown("**Ollama**")
    if not api_ok:
        st.caption("—")
    elif llm and llm.get("reachable"):
        st.markdown('<p class="status-ok">Reachable</p>', unsafe_allow_html=True)
    elif llm:
        st.markdown('<p class="status-warn">Check service</p>', unsafe_allow_html=True)
    else:
        st.caption("Unknown")

st.markdown(home_nav_cards_html(), unsafe_allow_html=True)

st.subheader("Go to")
p1, p2, p3, p4 = st.columns(4)
with p1:
    st.page_link("pages/1_Chat.py", label="Chat", icon="💬", use_container_width=True)
with p2:
    st.page_link("pages/2_Analytics.py", label="Analytics", icon="📊", use_container_width=True)
with p3:
    st.page_link("pages/3_Voice.py", label="Voice", icon="🎙️", use_container_width=True)
with p4:
    st.page_link("pages/4_Settings.py", label="Settings", icon="⚙️", use_container_width=True)

st.markdown(
    '<p class="disclaimer">Not medical advice. For wellness-style engagement only; consult a clinician for health concerns.</p>',
    unsafe_allow_html=True,
)
