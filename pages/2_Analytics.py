"""
Cognitive performance dashboard — uses GET /users/{id}/analytics
"""

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BACKEND_URL = os.getenv("COGNITIVE_API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = 30

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")

st.title("📊 Cognitive analytics")
st.caption("Latency, blended accuracy trend, and session activity from SQLite logs")

user_id = st.number_input("User ID", min_value=1, max_value=99999, value=1, step=1)
limit = st.slider("Max log rows", 50, 2000, 500, 50)

if st.button("Load analytics", type="primary"):
    st.session_state["analytics_user"] = user_id
    st.session_state["analytics_limit"] = limit

uid = st.session_state.get("analytics_user", user_id)
lim = st.session_state.get("analytics_limit", limit)

try:
    r = requests.get(
        f"{BACKEND_URL}/users/{uid}/analytics",
        params={"limit": lim},
        timeout=REQUEST_TIMEOUT,
    )
except requests.RequestException as e:
    st.error(f"Cannot reach API: {e}")
    st.stop()

if r.status_code == 404:
    st.warning("User not found. Create the user first (POST /users).")
    st.stop()
if r.status_code != 200:
    st.error(f"API error {r.status_code}: {r.text}")
    st.stop()

data = r.json()
summary = data.get("summary") or {}
series = data.get("series") or []

c1, c2, c3, c4 = st.columns(4)
c1.metric("Chat turns", summary.get("chat_turns", 0))
c2.metric("Proactive opens", summary.get("proactive_opens", 0))
c3.metric("Avg latency (chat)", summary.get("avg_latency_chat") or "—")
c4.metric("Avg accuracy (chat)", summary.get("avg_accuracy_chat") or "—")
st.metric("Current difficulty", f"{summary.get('current_difficulty', '—')} / 5")

if not series:
    st.info("No task logs yet for this user.")
    st.stop()

df = pd.DataFrame(series)
df_chat = df[df["task_type"] == "chat_turn"].copy()

if not df_chat.empty:
    df_chat = df_chat.reset_index(drop=True)
    df_chat["turn_index"] = df_chat.index + 1

    t1, t2 = st.tabs(["Latency & accuracy", "Activity mix"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            fig_l = px.line(
                df_chat,
                x="turn_index",
                y="latency",
                markers=True,
                title="Response latency (s) per chat turn",
            )
            fig_l.update_layout(height=360)
            st.plotly_chart(fig_l, use_container_width=True)
        with c2:
            fig_a = px.line(
                df_chat,
                x="turn_index",
                y="accuracy",
                markers=True,
                title="Blended accuracy score per chat turn",
            )
            fig_a.update_layout(yaxis_range=[0, 1], height=360)
            st.plotly_chart(fig_a, use_container_width=True)
    with t2:
        counts = df.groupby("task_type").size().reset_index(name="count")
        fig_b = px.bar(
            counts,
            x="task_type",
            y="count",
            title="Logged events by task type",
        )
        st.plotly_chart(fig_b, use_container_width=True)
else:
    st.warning("No chat turns logged yet — only proactive or empty history.")
    counts = df.groupby("task_type").size().reset_index(name="count")
    fig_b = px.bar(counts, x="task_type", y="count", title="Events by task type")
    st.plotly_chart(fig_b, use_container_width=True)

with st.expander("Raw series (scrollable)"):
    st.dataframe(df, use_container_width=True, height=320)
