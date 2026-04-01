# Proactive Voice-Based LLM + RAG Dementia Companion

A proactive voice-first cognitive companion system built using **Llama 3 + Retrieval-Augmented Generation (RAG)** to support structured memory recall and longitudinal cognitive tracking for dementia research.

---

##  Project Purpose

This project explores how a voice-based Large Language Model (LLM) integrated with structured memory retrieval can:

- Initiate proactive daily conversations  
- Support safe recall of personal memories  
- Track cognitive interaction metrics over time  
- Provide structured longitudinal analytics for caregivers  

>  This is a research prototype and NOT a medical device.

---

##  Core Features

-  LumiAI Cognitive Screening (MMSE/MoCA-inspired 30-point pre-check)
-  Voice-first interaction (Speech-to-Text + Text-to-Speech)
-  Structured caregiver-fed personal memory graph
-  Retrieval-only personal memory recall (hallucination-safe)
-  Multi-domain cognitive interaction tracking
-  Longitudinal trend analytics
-  Proactive scheduled sessions
-  Guardrails to prevent fabricated memories

---

##  System Architecture

```
User Speech
    ↓
Speech-to-Text
    ↓
FastAPI Backend
    ↓
Retrieve Memory (ChromaDB + Embeddings)
    ↓
Inject Context + Difficulty Level
    ↓
Llama 3 (Ollama)
    ↓
Structured Logging (SQLite)
    ↓
Adaptive Difficulty Update
    ↓
Text-to-Speech Response
```

---

##  Tech Stack

| Layer        | Technology |
|--------------|------------|
| LLM          | Llama 3 (Ollama) |
| RAG          | ChromaDB + Sentence Transformers |
| Backend      | FastAPI |
| Database     | SQLite |
| Frontend     | Streamlit + HTML + CSS + JavaScript |
| Voice        | Faster-Whisper + pyttsx3 |
| Scheduler    | APScheduler |
| Analytics    | Pandas + Plotly + Streamlit |

---

##  Database Schema

### Users

- `id` (INTEGER)
- `name` (TEXT)
- `age` (INTEGER)
- `caregiver_notes` (TEXT)
- `difficulty_level` (INTEGER 1–5)

### Sessions

- `id` (INTEGER)
- `user_id` (INTEGER)
- `session_type` (TEXT)
- `timestamp` (DATETIME)

### Task Logs

- `id` (INTEGER)
- `session_id` (INTEGER)
- `task_type` (TEXT)
- `accuracy` (REAL)
- `latency` (REAL)
- `hints_used` (INTEGER)

---

##  Adaptive Difficulty Engine

Rules:

- Accuracy > 80% → Increase difficulty
- Accuracy < 50% → Decrease difficulty
- Difficulty range: 1 (easy) to 5 (hard)

Difficulty level is injected directly into the LLM prompt to dynamically control cognitive load.

---

##  Setup Instructions

### 1️ Clone Repository

```bash
git clone https://github.com/harshinibonde/cognitive-ai-system.git
cd cognitive-ai-system
```

---

### 2️ Create Virtual Environment

```bash
python -m venv venv
```

Activate:

**Windows**
```bash
venv\Scripts\activate
```

**Mac/Linux**
```bash
source venv/bin/activate
```

---

### 3️ Install Dependencies

```bash
pip install -r requirements.txt
```

If you do not yet have `requirements.txt`, install manually:

```bash
pip install fastapi uvicorn chromadb sentence-transformers
pip install numpy pandas requests apscheduler
pip install plotly streamlit faster-whisper pyttsx3
```

---

### 4️ Install Ollama

Download from:  
https://ollama.com

Pull Llama 3:

```bash
ollama pull llama3
```

Test:

```bash
ollama run llama3
```

---


### 6️ Start Backend

```bash
uvicorn app.main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

---

##  Current Status

| Component              | Status |
|------------------------|--------|
| LLM Integration        | Complete |
| RAG Memory             | Complete |
| Multi-user Isolation   | Complete |
| Adaptive Difficulty    | Complete |
| Voice Layer (STT/TTS)  | Complete |
| Audio Feature Analysis | Complete |
| Authentication (OTP)   | Complete |
| Session Management     | Complete |
| Scheduler              | Complete |
| Analytics Dashboard    | Complete |
| Email Notifications    | Complete |
| Decision Engine        | Complete |
| Behavioral Insights    | Complete |

---

##  Authentication & Session Management

**OTP-Based Access:**
- Users request OTP via `POST /auth/request-otp` (sent via email)
- Verify with `POST /auth/verify-otp` to receive session token
- Session tokens expire after configurable duration
- Tokens stored in database with user association

**Session Isolation:**
- Each authenticated user receives unique session token
- Backend validates token before processing sensitive operations
- Session state persists across page/browser refreshes

---

##  Analytics & Insights

**Metrics Tracked:**
- **Accuracy per turn** — Correctness of cognitive responses
- **Latency** — Response time per interaction
- **Hints used** — Number of assists per session
- **Difficulty progression** — Adaptive level changes over time
- **Task focus distribution** — Engagement by cognitive domain

**Behavioral Insights:**
- Session frequency trends
- Cognitive decline/improvement signals
- Response pattern analysis (verbal, audio features)
- Caregiver alerts for significant changes

**Audio Feature Analysis:**
Extracted from voice recordings:
- MFCC (Mel-Frequency Cepstral Coefficients) — Speech spectral patterns
- Pitch & Energy — Voice quality metrics
- Speech rate & Pause duration — Fluency indicators
- Lexical diversity & Repetition — Language markers

---

##  Notifications & Alerts

**Email System (SMTP-based):**
- OTP delivery to users
- Caregiver alerts for cognitive decline indicators
- Proactive session reminders
- Assessment review notifications

**Scheduled Triggers:**
- Daily/weekly proactive greeting generation
- Longitudinal assessment reminders
- Caregiver summary reports

---

##  Memory & Context Augmentation

**Personal Memory Management:**
- Caregiver-fed context (family events, preferences, medical history)
- Stored in ChromaDB with semantic embeddings
- Retrieved dynamically to contextualize LLM responses
- Prevents fabricated memories ("hallucination-safe")

**Retrieval Strategy:**
- Query embedding similarity matching
- Top-k context injection into LLM prompt
- User-specific memory isolation

---

##  Decision Engine & Routing

**Post-Assessment Logic:**
- **Normal** → Exit with clearance message
- **Mild Impairment** → Redirect to cognitive support chat
- **Moderate Impairment** → Flag warning + proceed with heightened support
- **Severe Impairment** → Alert caregiver + suggest medical referral

---

##  Longitudinal Data Management

**Schema Highlights:**
- **Users** — Profile, difficulty level, caregiver notes
- **Sessions** — Type, timestamp, proactive vs. prompted
- **Task Logs** — Per-interaction metrics (accuracy, latency, hints)
- **Assessments** — Full test results with question-by-question feedback
- **Difficulty Changes** — History of adaptive adjustments
- **User Sessions** — Auth tokens with expiration

---

##  Privacy & Architecture

- Fully offline  
- No external LLM APIs  
- No cloud storage  
- No telemetry  
- All processing occurs locally  

---

##  Project Structure

```
cognitive-ai-system/
│
├── app/                              # FastAPI backend & business logic
│   ├── main.py                       # Main server, endpoints, scheduler
│   ├── assessment_data.py           # Assessment questions & scoring
│   ├── screening_pipeline.py        # ML scoring pipeline
│   ├── audio_features.py            # Voice feature extraction
│   ├── decision_engine.py           # Post-assessment routing logic
│   ├── otp_utils.py                 # OTP generation & validation
│   └── __pycache__/
│
├── cognitive/                        # Cognitive analytics & insights
│   ├── scoring.py                   # Turn-level accuracy scoring
│   ├── insights.py                  # Behavioral patterns & trends
│   └── __init__.py
│
├── database/
│   └── db.py                        # SQLite schema & queries
│
├── llm/
│   └── ollama_client.py             # Llama 3 API wrapper
│
├── rag/
│   └── vector_store.py              # ChromaDB embeddings & retrieval
│
├── voice/                            # Voice processing
│   ├── stt.py                       # Faster-Whisper for speech-to-text
│   ├── tts.py                       # pyttsx3 for text-to-speech
│   └── __init__.py
│
├── notifications/                    # Alert & reminder system
│   ├── email_reminder.py            # Email notifications (OTP, reminders, alerts)
│   └── __init__.py
│
├── ui/                               # Streamlit UI utilities
│   ├── streamlit_api.py             # Backend API communication
│   ├── streamlit_chat.py            # Chat interaction logic
│   ├── streamlit_state.py           # Session state management
│   ├── streamlit_theme.py           # UI styling
│   └── __init__.py
│
├── pages/                            # Streamlit multi-page app
│   ├── 1_Chat.py                    # Chat & proactive sessions
│   ├── 2_Analytics.py               # Analytics dashboard
│   ├── 3_Voice.py                   # Voice interaction
│   └── 4_Settings.py                # User management & admin
│
├── frontend/                         # Next.js screening UI
│   └── lumi-screening/
│       ├── app/
│       ├── package.json
│       ├── next.config.js
│       └── tsconfig.json
│
├── scripts/
│   ├── train_screening_models.py   # ML model training
│   └── backup.ps1
│
├── tests/
│   ├── test_integration.py
│   └── test_submit.py
│
├── demo_app.py                       # Standalone demo
├── train_models.py                   # Model training script
├── requirements.txt                  # Python dependencies
└── README.md
```

---

##  API Endpoints

### Health & Meta
- `GET /` / `GET /health` — Server health check
- `GET /health/ollama` — Ollama LLM connectivity check
- `GET /meta` — System metadata

### User Management
- `GET /users` — List all users
- `GET /users/{user_id}` — Fetch user profile (name, age, difficulty level)
- `POST /users` — Create new user
- `GET /users/{user_id}/analytics` — Cognitive analytics (sessions, trends, insights)
- `GET /users/{user_id}/latest-scheduled-opening` — Latest proactive greeting

### Cognitive Screening
- `GET /assessment/questions` — Returns 18-question MMSE/MoCA-inspired quiz (30 points total)
- `POST /assessment/submit` — Submit answers, compute score, classify cognitive level
- `GET /assessment/latest/{user_id}` — Fetch most recent assessment
- `POST /assessment/audio/analyze` — Extract audio features from recording

Classification bands:
- `25–30`: **normal**
- `21–24`: **mild_impairment**
- `10–20`: **moderate_impairment**
- `<10`: **severe_impairment**

### Voice Services
- `POST /voice/transcribe` — Convert speech audio to text (Faster-Whisper)
- `POST /voice/tts` — Text-to-Speech conversion

### Chat & Sessions
- `POST /sessions/start` — Start proactive cognitive interaction session
- `POST /chat` — Send message, retrieve LLM response with memory context
- `POST /assessment/audio/analyze` — Analyze voice features for cognitive markers

### Authentication
- `POST /auth/request-otp` — Request one-time password via email
- `POST /auth/verify-otp` — Verify OTP and establish session token
- `POST /auth/logout` — Invalidate session token

---

##  Screening Frontend (Next.js)

Location: `frontend/lumi-screening`

Run:

```bash
cd frontend/lumi-screening
npm install
npm run dev
```

Set API base (optional):

```bash
set NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
set NEXT_PUBLIC_SUPPORT_URL=http://127.0.0.1:8501
```

---

##  Streamlit Multi-Page Application

The Streamlit interface provides interactive cognitive engagement and analytics:

**Pages:**
- **1_Chat.py** — Conversational interface with proactive session initiation, memory-augmented chat, and task focus options
- **2_Analytics.py** — Cognitive analytics dashboard with trend graphs, session history, and behavioral insights
- **3_Voice.py** — Voice interaction page with speech-to-text transcription and audio feature analysis
- **4_Settings.py** — User management, profile creation, difficulty adjustment, and system diagnostics

**Features:**
- Real-time backend health checks
- Session state persistence
- Dynamic difficulty level display
- Proactive greeting generation
- Task focus categorization (memory recall, language fluency, attention, etc.)
- Longitudinal analytics visualizations

Start Streamlit:

```bash
streamlit run ui/streamlit_api.py
```

---

##  Running the Full System

### 1️ Start Ollama Backend

```bash
ollama serve
```

In another terminal:
```bash
ollama run llama3
```

### 2️ Start FastAPI Server

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check:
```
http://127.0.0.1:8000/docs
```

### 3️ Start Streamlit UI

```bash
streamlit run pages/1_Chat.py
```

Automatically opens at:
```
http://127.0.0.1:8501
```

### 4️ (Optional) Run Next.js Screening Frontend

```bash
cd frontend/lumi-screening
npm run dev
```

Runs at:
```
http://127.0.0.1:3000
```

---

##  Environment Configuration

Create `.env` in project root:

```env
# LLM
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3

# Voice
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

# API
COGNITIVE_API_URL=http://127.0.0.1:8000

# Email (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password

# Frontend
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
NEXT_PUBLIC_SUPPORT_URL=http://127.0.0.1:8501
```

---

##  Testing

Run integration tests:

```bash
pytest tests/test_integration.py -v
pytest tests/test_submit.py -v
```

Run demo app:

```bash
streamlit run demo_app.py
```

---


