"""
Cognitive performance dashboard — GET /users/{id}/analytics
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

from ui.streamlit_api import BACKEND_URL
from ui.streamlit_state import ensure_session_state
from ui.streamlit_theme import STREAMLIT_PAGE_STYLE

ensure_session_state()
st.markdown(STREAMLIT_PAGE_STYLE, unsafe_allow_html=True)
st.markdown(
    "<style>.main .block-container { max-width: 1180px !important; }</style>",
    unsafe_allow_html=True,
)

REQUEST_TIMEOUT = 30

_PLOT_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(24,27,38,0.95)",
    plot_bgcolor="rgba(15,17,23,0.92)",
    font=dict(color="#f1f5f9"),
    height=360,
    margin=dict(l=40, r=20, t=50, b=40),
)

st.title("Cognitive analytics")
st.caption("Latency, accuracy, difficulty history, session rhythm, and simple behavioral trends.")

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
insights = data.get("insights") or {}
diff_hist = data.get("difficulty_timeline") or []
sess_day = data.get("sessions_by_day") or []
evt_day = data.get("interaction_events_by_day") or []

c1, c2, c3, c4 = st.columns(4)
c1.metric("Chat turns", summary.get("chat_turns", 0))
c2.metric("Proactive opens", summary.get("proactive_opens", 0))
c3.metric("Avg latency (chat)", summary.get("avg_latency_chat") or "—")
c4.metric("Avg accuracy (chat)", summary.get("avg_accuracy_chat") or "—")
st.metric("Current difficulty", f"{summary.get('current_difficulty', '—')} / 5")

st.subheader("Behavioral snapshot (rolling windows)")
i1, i2, i3, i4 = st.columns(4)
i1.metric("Chat turns (7d)", insights.get("chat_turns_7d", "—"))
i2.metric("Active days (30d)", insights.get("active_days_30d", "—"))
i3.metric("Latency trend", str(insights.get("latency_trend", "—")).replace("_", " "))
i4.metric("Accuracy trend", str(insights.get("accuracy_trend", "—")).replace("_", " "))
if insights.get("hints_avg_7d") is not None:
    st.caption(f"Average hints per turn (7d): **{insights['hints_avg_7d']}**")

if not series:
    st.info("No task logs yet for this user.")
    st.stop()

df = pd.DataFrame(series)
df_chat = df[df["task_type"] == "chat_turn"].copy()

tab_a, tab_b, tab_c, tab_d = st.tabs(
    ["Latency & accuracy", "Rhythm & difficulty", "Task mix", "Raw data"]
)

with tab_a:
    if not df_chat.empty:
        df_chat = df_chat.reset_index(drop=True)
        df_chat["turn_index"] = df_chat.index + 1
        c1, c2 = st.columns(2)
        with c1:
            fig_l = px.line(
                df_chat,
                x="turn_index",
                y="latency",
                markers=True,
                title="Response latency (s) per chat turn",
                color_discrete_sequence=["#6366f1"],
            )
            fig_l.update_layout(**_PLOT_LAYOUT)
            st.plotly_chart(fig_l, use_container_width=True)
        with c2:
            fig_a = px.line(
                df_chat,
                x="turn_index",
                y="accuracy",
                markers=True,
                title="Blended accuracy (semantic + heuristic)",
                color_discrete_sequence=["#f59e0b"],
            )
            fig_a.update_layout(yaxis_range=[0, 1], **_PLOT_LAYOUT)
            st.plotly_chart(fig_a, use_container_width=True)
    else:
        st.warning("No chat turns in this window.")

with tab_b:
    c1, c2 = st.columns(2)
    with c1:
        if evt_day:
            dfe = pd.DataFrame(evt_day)
            fig_e = px.bar(
                dfe,
                x="day",
                y="events",
                title="Interaction events per day (from logs)",
                color_discrete_sequence=["#a5b4fc"],
            )
            fig_e.update_layout(**_PLOT_LAYOUT)
            st.plotly_chart(fig_e, use_container_width=True)
        else:
            st.caption("No dated events in series.")
    with c2:
        if sess_day:
            dfs = pd.DataFrame(sess_day)
            fig_s = px.bar(
                dfs,
                x="day",
                y="sessions",
                title="New sessions per day (SQLite)",
                color_discrete_sequence=["#818cf8"],
            )
            fig_s.update_layout(**_PLOT_LAYOUT)
            st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.caption("No session rows in range.")
    if diff_hist:
        dfd = pd.DataFrame(diff_hist)
        dfd["step"] = range(1, len(dfd) + 1)
        fig_d = go.Figure()
        fig_d.add_trace(
            go.Scatter(
                x=dfd["step"],
                y=dfd["new_level"],
                mode="lines+markers",
                name="Difficulty after change",
                line=dict(color="#6366f1", width=2),
                marker=dict(size=8),
            )
        )
        fig_d.update_layout(
            title="Difficulty progression (logged adjustments)",
            xaxis_title="Change #",
            yaxis_title="Level (1–5)",
            yaxis=dict(range=[0.5, 5.5], dtick=1),
            **_PLOT_LAYOUT,
        )
        st.plotly_chart(fig_d, use_container_width=True)
    else:
        st.caption("No difficulty changes recorded yet (stable level).")

with tab_c:
    counts = df.groupby("task_type").size().reset_index(name="count")
    fig_b = px.bar(
        counts,
        x="task_type",
        y="count",
        title="Events by task type",
        color_discrete_sequence=["#6366f1"],
    )
    fig_b.update_layout(**_PLOT_LAYOUT)
    st.plotly_chart(fig_b, use_container_width=True)
    if "task_focus" in df.columns:
        nz = df[df["task_focus"].astype(str).str.len() > 0]
        if not nz.empty:
            st.caption("Task focus mix (chat turns with focus set)")
            st.bar_chart(nz["task_focus"].value_counts())

with tab_d:
    st.dataframe(df, use_container_width=True, height=420)
