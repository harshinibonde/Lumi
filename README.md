🧠 Cognitive AI System
Local Multi-User Adaptive Cognitive Engagement Platform

A fully offline, research-oriented cognitive engagement system built using:

🦙 Llama 3 (via Ollama)

🧠 Retrieval-Augmented Generation (ChromaDB + Sentence Transformers)

🗄 SQLite structured cognitive metrics

👥 Multi-user isolation

🔄 Adaptive difficulty engine

⚡ FastAPI backend

Designed as a foundation for dementia research and structured cognitive monitoring.

🎯 Project Goal
To build a:

Local, multi-user, adaptive cognitive engagement system
that tracks structured performance metrics and dynamically adjusts difficulty over time.

The system operates fully offline and supports longitudinal cognitive monitoring for 10–20 users.

🏗 System Architecture
User Request
     ↓
FastAPI Backend
     ↓
Retrieve Memory (ChromaDB + Embeddings)
     ↓
Inject Context + Difficulty Level
     ↓
Llama 3 (via Ollama)
     ↓
Structured Logging (SQLite)
     ↓
Adaptive Difficulty Update
🔧 Core Components
1️⃣ Backend Framework
FastAPI

REST endpoints for:

/users

/chat

/sessions

Modular architecture (app/, database/, rag/, llm/)

2️⃣ Local LLM Integration
Llama 3 served via Ollama

CPU-only configuration (GPU disabled permanently)

Fully offline inference

3️⃣ Retrieval-Augmented Generation (RAG)
Embeddings: sentence-transformers (all-MiniLM-L6-v2)

Vector DB: ChromaDB

Memory stored per user using metadata filtering

Context injected dynamically into prompts

4️⃣ Multi-User Support
Structured users table

Per-user memory isolation

Independent difficulty levels

Session-based tracking

5️⃣ SQLite Database Schema
users
Column	Type
id	INTEGER
name	TEXT
age	INTEGER
caregiver_notes	TEXT
difficulty_level	INTEGER (1–5)
sessions
Column	Type
id	INTEGER
user_id	INTEGER
session_type	TEXT
timestamp	DATETIME
task_logs
Column	Type
id	INTEGER
session_id	INTEGER
task_type	TEXT
accuracy	REAL
latency	REAL
hints_used	INTEGER
6️⃣ Adaptive Difficulty Engine
Rules:

Average accuracy > 80% → Increase difficulty

Average accuracy < 50% → Decrease difficulty

Difficulty range: 1 (easy) to 5 (hard)

Difficulty level is injected directly into the LLM prompt to dynamically control cognitive load.

🚀 Setup Instructions
1️⃣ Clone Repository
git clone https://github.com/YOUR_USERNAME/cognitive-ai-system.git
cd cognitive-ai-system
2️⃣ Create Virtual Environment
python -m venv venv
Activate:

Windows

venv\Scripts\activate
Mac/Linux

source venv/bin/activate
3️⃣ Install Dependencies
pip install fastapi uvicorn
pip install chromadb sentence-transformers
pip install numpy pandas requests
pip install apscheduler
pip install plotly streamlit
pip install faster-whisper
pip install pyttsx3
4️⃣ Install Ollama
Download from:
https://ollama.com

Pull Llama 3:

ollama pull llama3
Test:

ollama run llama3
5️⃣ Disable GPU (Permanent CPU Mode)
Create file:

C:\Users\YOUR_USER\.ollama\config.yaml
Add:

gpu: false
6️⃣ Start Backend
uvicorn app.main:app --reload
Open:

http://127.0.0.1:8000/docs
📊 Current Feature Status
Feature	Status
LLM Integration	✅ Complete
RAG Memory	✅ Complete
Multi-user Isolation	✅ Complete
Structured Logging	✅ Complete
Adaptive Difficulty	✅ Complete
Voice Layer	🔜 Planned
Scheduler	🔜 Planned
Analytics Dashboard	🔜 Planned
🛣 Roadmap
Phase 1
Database stabilization

LLM + RAG integration

Phase 2
Adaptive difficulty controller

Structured cognitive scoring

Phase 3 (Upcoming)
🎤 Speech-to-Text (Faster-Whisper)

🔊 Text-to-Speech

⏰ APScheduler proactive sessions

Phase 4
📈 Streamlit analytics dashboard

Longitudinal cognitive trend visualization

🧪 Research Use Case
This system enables:

Longitudinal cognitive tracking

Memory recall performance measurement

Response latency analysis

Difficulty adaptation over time

Structured session logging

Designed as a foundation for dementia research and cognitive engagement studies.

🔐 Privacy & Architecture
Fully offline

No API calls

No external LLM services

No cloud storage

No telemetry

All processing occurs locally.

📦 Project Structure
cognitive-ai-system/
│
├── app/
│   └── main.py
│
├── database/
│   └── db.py
│
├── llm/
│   └── ollama_client.py
│
├── rag/
│   └── vector_store.py
│
├── chroma_storage/
├── cognitive_system.db
└── README.md
👨‍💻 Author
Developed as a research-grade local cognitive AI system.