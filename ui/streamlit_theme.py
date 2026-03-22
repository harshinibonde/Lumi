"""
Slate Meridian — neutral cool grays, indigo primary, amber accent.
Calm, structured; avoids busy gradients on every surface.
"""

STREAMLIT_PAGE_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

:root {
  --bg-app: #0f1117;
  --bg-surface: #181b26;
  --bg-raised: #1f2330;
  --border: rgba(255, 255, 255, 0.07);
  --text: #f1f5f9;
  --text-muted: #94a3b8;
  --indigo: #6366f1;
  --indigo-dim: rgba(99, 102, 241, 0.15);
  --amber: #f59e0b;
  --success: #22c55e;
  --danger: #ef4444;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg-app) !important;
}

.stApp {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  background: var(--bg-app) !important;
}

#MainMenu, footer, header { visibility: hidden; height: 0; }
[data-testid="stHeader"] { background: transparent !important; }

.main .block-container {
  padding: 1.75rem 2rem 4rem;
  max-width: min(960px, 100%);
  margin: 0 auto;
}

[data-testid="stSidebar"] {
  background: var(--bg-surface) !important;
  border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] .stMarkdown { color: var(--text-muted) !important; }

h1 { color: var(--text) !important; font-weight: 700 !important; letter-spacing: -0.03em; font-size: 1.85rem !important; }
h2, h3 { color: var(--text) !important; font-weight: 600 !important; }
.stCaption, [data-testid="stCaption"] { color: var(--text-muted) !important; }

.pill {
  display: inline-block;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: var(--indigo-dim);
  color: #a5b4fc;
  border: 1px solid rgba(99, 102, 241, 0.35);
  margin-bottom: 0.75rem;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin: 1.5rem 0 2rem;
}
.home-card {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem 1.35rem;
}
.home-card h3 {
  margin: 0 0 0.35rem 0;
  font-size: 1rem !important;
  color: var(--text) !important;
}
.home-card p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.45;
}

.status-ok { color: var(--success) !important; font-weight: 600; }
.status-bad { color: var(--danger) !important; font-weight: 600; }
.status-warn { color: var(--amber) !important; font-weight: 600; }

.disclaimer {
  font-size: 0.78rem;
  color: var(--text-muted);
  border-left: 3px solid var(--amber);
  padding: 0.65rem 0 0.65rem 1rem;
  margin: 2rem 0 0;
  background: rgba(245, 158, 11, 0.06);
  border-radius: 0 10px 10px 0;
  line-height: 1.5;
}

.stButton > button[kind="primary"] {
  background: var(--indigo) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
}
.stButton > button[kind="secondary"] {
  background: var(--bg-raised) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}

[data-testid="stChatInput"] textarea {
  background: var(--bg-raised) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}

.stTextInput input, .stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div {
  background: var(--bg-raised) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
  border-radius: 10px !important;
}

.stExpander {
  background: var(--bg-surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}

hr.divider {
  border: none;
  height: 1px;
  background: var(--border);
  margin: 2rem 0;
}
</style>
"""


def home_nav_cards_html() -> str:
    """Static hint cards; real navigation uses st.page_link below."""
    return """
<div class="card-grid">
  <div class="home-card"><h3>Chat</h3><p>Talk with the companion. One thread per user; optional AI opening.</p></div>
  <div class="home-card"><h3>Analytics</h3><p>Latency, accuracy, difficulty history, and rhythm charts.</p></div>
  <div class="home-card"><h3>Voice</h3><p>Transcribe audio and optional spoken replies — separate from text chat.</p></div>
  <div class="home-card"><h3>Settings</h3><p>API URL, defaults, and run instructions.</p></div>
</div>
"""
