"""Conversation — text chat only."""

import streamlit as st

from ui.streamlit_api import (
    BACKEND_URL,
    TASK_FOCUS_OPTIONS,
    check_backend_connection,
    fetch_latest_scheduled_opening,
    fetch_user_profile,
    start_proactive_session,
)
from ui.streamlit_chat import run_chat_turn
from ui.streamlit_state import ensure_session_state, sync_user_change
from ui.streamlit_theme import STREAMLIT_PAGE_STYLE

ensure_session_state()
st.markdown(STREAMLIT_PAGE_STYLE, unsafe_allow_html=True)

st.title("Chat")
st.caption("Messages, proactive opening, and session controls for this page only.")

backend_ok = check_backend_connection()
if not backend_ok:
    st.error(f"API offline. Start the server, then refresh. Expected: `{BACKEND_URL}`")
    st.stop()

uid = st.number_input(
    "User ID",
    min_value=1,
    max_value=9999,
    value=int(st.session_state.user_id),
    step=1,
    key="chat_user_id",
)
sync_user_change(uid)
st.session_state.user_id = uid

def _task_focus_index() -> int:
    tf = st.session_state.get("task_focus", "")
    return TASK_FOCUS_OPTIONS.index(tf) if tf in TASK_FOCUS_OPTIONS else 0


with st.expander("Conversation options", expanded=False):
    st.session_state.hints_used = st.number_input(
        "Hints used (logged per turn)",
        0,
        20,
        int(st.session_state.get("hints_used", 0)),
    )
    st.session_state.task_focus = st.selectbox(
        "Cognitive focus (logged)",
        TASK_FOCUS_OPTIONS,
        index=_task_focus_index(),
        format_func=lambda x: "(balanced)" if x == "" else x.replace("_", " "),
    )

profile = fetch_user_profile(uid)
if profile:
    st.info(f"**{profile.get('name', '')}** · difficulty **{profile.get('difficulty_level', 1)}/5**")
else:
    st.warning("No user with this ID. Create one with `POST /users` (see Settings).")

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    if st.button("Let AI open the chat", use_container_width=True, type="primary"):
        if not profile:
            st.error("Create the user first.")
        else:
            with st.spinner("Generating…"):
                out = start_proactive_session(uid)
            if out:
                st.session_state.chat_history = []
                st.session_state.session_id = out.get("session_id")
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": out.get("response", ""),
                        "latency": out.get("latency_seconds", 0.0),
                    }
                )
                st.rerun()
            else:
                st.error("Could not start session. Check Ollama logs.")
with c2:
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.session_id = None
        st.rerun()
with c3:
    sid = st.session_state.session_id
    st.caption(f"Session id: `{sid}`" if sid else "No active session")

sched = fetch_latest_scheduled_opening(uid)
if sched and sched.get("opening"):
    with st.expander("Latest scheduled check-in"):
        st.write(sched["opening"])

if st.session_state.get("tts_pending"):
    import io

    b = st.session_state.pop("tts_pending")
    if b:
        st.audio(io.BytesIO(b), format="audio/wav")

if not st.session_state.chat_history:
    st.info("Use **Let AI open the chat** or type below. Voice tools live under **Voice** in the sidebar.")

for entry in st.session_state.chat_history:
    role = entry["role"]
    with st.chat_message(
        "user" if role == "user" else "assistant",
        avatar="🧑" if role == "user" else "🤖",
    ):
        st.write(entry["content"])
        if role == "assistant" and entry.get("latency") is not None:
            st.caption(f"{entry['latency']:.2f}s")

msg = st.chat_input("Message…")
if msg and msg.strip():
    run_chat_turn(
        msg.strip(),
        int(st.session_state.get("hints_used", 0)),
        str(st.session_state.get("task_focus", "")),
    )
    st.rerun()
