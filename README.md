# Proactive Voice-Based LLM + RAG Dementia Companion

A proactive voice-first cognitive companion system built using **Llama 3 + Retrieval-Augmented Generation (RAG)** to support structured memory recall and longitudinal cognitive tracking for dementia research.

---

## 🎯 Project Purpose

This project explores how a voice-based Large Language Model (LLM) integrated with structured memory retrieval can:

- Initiate proactive daily conversations  
- Support safe recall of personal memories  
- Track cognitive interaction metrics over time  
- Provide structured longitudinal analytics for caregivers  

> ⚠️ This is a research prototype and NOT a medical device.

---

## 🚀 Core Features

- 📝 LumiAI Cognitive Screening (MMSE/MoCA-inspired 30-point pre-check)
- 🎤 Voice-first interaction (Speech-to-Text + Text-to-Speech)
- 🧠 Structured caregiver-fed personal memory graph
- 🔍 Retrieval-only personal memory recall (hallucination-safe)
- 📊 Multi-domain cognitive interaction tracking
- 📈 Longitudinal trend analytics
- ⏰ Proactive scheduled sessions
- 🔒 Guardrails to prevent fabricated memories

---

## 🏗 System Architecture

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

## 🧩 Tech Stack

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

## 🗄 Database Schema

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

## 🔄 Adaptive Difficulty Engine

Rules:

- Accuracy > 80% → Increase difficulty
- Accuracy < 50% → Decrease difficulty
- Difficulty range: 1 (easy) to 5 (hard)

Difficulty level is injected directly into the LLM prompt to dynamically control cognitive load.

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/harshinibonde/cognitive-ai-system.git
cd cognitive-ai-system
```

---

### 2️⃣ Create Virtual Environment

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

### 3️⃣ Install Dependencies

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

### 4️⃣ Install Ollama

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

### 5️⃣ Disable GPU — Force CPU Mode

Create:

```
C:\Users\ASUS\.ollama\config.yaml
```

Add:

```yaml
gpu: false
```

---

### 6️⃣ Start Backend

```bash
uvicorn app.main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

---

## 📊 Current Status

| Component              | Status |
|------------------------|--------|
| LLM Integration        | ✅ Complete |
| RAG Memory             | ✅ Complete |
| Multi-user Isolation   | ✅ Complete |
| Adaptive Difficulty    | ✅ Complete |
| Voice Layer            | 🔜 In Progress |
| Scheduler              | 🔜 In Progress |
| Analytics Dashboard    | 🔜 In Progress |

---

## 🔐 Privacy & Architecture

- Fully offline  
- No external LLM APIs  
- No cloud storage  
- No telemetry  
- All processing occurs locally  

---

## 📂 Project Structure

```
cognitive-ai-system/
│
├── app/
│   ├── main.py
│   └── assessment_data.py
├── database/
│   └── db.py
├── frontend/
│   └── lumi-screening/
├── llm/
│   └── ollama_client.py
├── rag/
│   └── vector_store.py
├── chroma_storage/
├── cognitive_system.db
└── README.md
```

---

## 🧪 Cognitive Screening API

- `GET /assessment/questions`  
  Returns the 18-question MMSE/MoCA-inspired quiz (30 points total).
- `POST /assessment/submit`  
  Accepts answers, computes score/classification, stores assessment + answer review.
- `GET /assessment/latest/{user_id}`  
  Returns most recent stored assessment result for a user.

Classification bands:

- `25–30`: normal
- `21–24`: mild_impairment
- `10–20`: moderate_impairment
- `<10`: severe_impairment

---

## 🖥 Screening Frontend (Next.js)

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

## 👨‍💻 Author

Developed as a research-grade local cognitive AI system.
