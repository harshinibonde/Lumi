"""Chat turn helper (uses session_state)."""

from __future__ import annotations

import streamlit as st

from ui.streamlit_api import fetch_tts_audio, send_chat


def run_chat_turn(
    message: str,
    hints_used: int,
    task_focus: str = "",
    *,
    play_tts: bool = False,
) -> tuple[bool, str | None]:
    st.session_state.chat_history.append({"role": "user", "content": message})
    with st.spinner("Thinking..."):
        result = send_chat(
            st.session_state.user_id,
            message,
            st.session_state.session_id,
            hints_used=hints_used,
            task_focus=task_focus,
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
        if play_tts and response_text:
            audio = fetch_tts_audio(response_text[:8000])
            if audio:
                st.session_state["tts_pending"] = audio
        return True, response_text
    st.session_state.chat_history.pop()
    st.error("Failed to get response from backend.")
    return False, None
