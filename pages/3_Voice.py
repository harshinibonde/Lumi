"""Voice — transcription, mic pipeline, text-to-speech. Does not duplicate the chat transcript UI."""

import io

import streamlit as st

from ui.streamlit_api import (
    BACKEND_URL,
    TASK_FOCUS_OPTIONS,
    check_backend_connection,
    fetch_tts_audio,
    fetch_user_profile,
    transcribe_audio_file,
)
from ui.streamlit_chat import run_chat_turn
from ui.streamlit_state import ensure_session_state, sync_user_change
from ui.streamlit_theme import STREAMLIT_PAGE_STYLE

ensure_session_state()
st.markdown(STREAMLIT_PAGE_STYLE, unsafe_allow_html=True)

st.title("Voice")
st.caption("Speech → text → model → optional audio. Uses the same user session as **Chat**.")

if not check_backend_connection():
    st.error(f"API offline. `{BACKEND_URL}`")
    st.stop()

uid = st.number_input(
    "User ID",
    min_value=1,
    max_value=9999,
    value=int(st.session_state.user_id),
    step=1,
    key="voice_page_uid",
)
sync_user_change(uid)
st.session_state.user_id = uid

if not fetch_user_profile(uid):
    st.warning("Create this user first (`POST /users`).")
    st.stop()

def _tf_i() -> int:
    tf = st.session_state.get("task_focus", "")
    return TASK_FOCUS_OPTIONS.index(tf) if tf in TASK_FOCUS_OPTIONS else 0


st.session_state.hints_used = st.number_input(
    "Hints for voice turns",
    0,
    20,
    int(st.session_state.get("hints_used", 0)),
)
st.session_state.task_focus = st.selectbox(
    "Cognitive focus for voice turns",
    TASK_FOCUS_OPTIONS,
    index=_tf_i(),
    format_func=lambda x: "(balanced)" if x == "" else x.replace("_", " "),
)

st.divider()
st.subheader("1 · Upload file")
up = st.file_uploader(
    "Audio file",
    type=["wav", "mp3", "m4a", "webm", "ogg", "flac"],
    key="voice_upload",
)
if up and st.button("Transcribe file", key="btn_tr_file"):
    txt = transcribe_audio_file(up.name, up.getvalue())
    if txt:
        st.session_state["voice_staging"] = txt

st.divider()
st.subheader("2 · Microphone")
auto_tts = st.checkbox("After reply: auto-play TTS", value=False, key="voice_auto_tts")
mic = st.audio_input("Record", key="voice_mic") if hasattr(st, "audio_input") else None
if mic is None:
    st.info("Install a recent Streamlit for `st.audio_input`, or use file upload above.")
elif st.button("Send recording to AI", type="primary", key="btn_mic_send"):
    raw = mic.getvalue() if hasattr(mic, "getvalue") else mic.read()
    if not raw:
        st.warning("Empty clip.")
    else:
        txt = transcribe_audio_file("mic.wav", raw)
        if txt:
            ok, _ = run_chat_turn(
                txt,
                int(st.session_state.hints_used),
                str(st.session_state.task_focus),
                play_tts=auto_tts,
            )
            if ok:
                st.success("Done. Open **Chat** to read the full thread, or play audio below.")
                st.rerun()

st.divider()
st.subheader("3 · Review text before sending")
staging = st.session_state.get("voice_staging", "")
if staging:
    edited = st.text_area("Transcript", value=staging, height=120, key="voice_ta")
    if st.button("Send transcript as chat turn", key="btn_send_staging"):
        ok, _ = run_chat_turn(
            edited.strip(),
            int(st.session_state.hints_used),
            str(st.session_state.task_focus),
        )
        if ok:
            st.session_state.pop("voice_staging", None)
            st.rerun()

st.divider()
st.subheader("4 · Speak last AI reply")
last_ai = next(
    (
        e["content"]
        for e in reversed(st.session_state.chat_history)
        if e.get("role") == "assistant"
    ),
    None,
)
if last_ai:
    if st.button("Generate speech for last reply", key="btn_tts"):
        audio = fetch_tts_audio(last_ai[:8000])
        if audio:
            st.audio(io.BytesIO(audio), format="audio/wav")
else:
    st.caption("No assistant message yet — use Chat or send a voice turn first.")

if st.session_state.get("tts_pending"):
    b = st.session_state.pop("tts_pending")
    if b:
        st.audio(io.BytesIO(b), format="audio/wav")
