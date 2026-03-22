"""Shared Streamlit session_state keys for multipage app."""


def ensure_session_state() -> None:
    import streamlit as st

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = 1
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "last_user_id" not in st.session_state:
        st.session_state.last_user_id = st.session_state.user_id
    if "hints_used" not in st.session_state:
        st.session_state.hints_used = 0
    if "task_focus" not in st.session_state:
        st.session_state.task_focus = ""


def sync_user_change(user_id: int) -> None:
    import streamlit as st

    if st.session_state.last_user_id != user_id:
        st.session_state.session_id = None
        st.session_state.chat_history = []
        st.session_state.last_user_id = user_id
