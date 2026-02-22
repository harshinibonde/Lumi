from fastapi import FastAPI
from pydantic import BaseModel
from database.db import initialize_database
from llm.ollama_client import generate_response
from rag.vector_store import add_memory, retrieve_memory
import uuid
import time
import sqlite3


def log_interaction(user_id: int, message: str, response: str, latency: float):
    conn = sqlite3.connect("cognitive_system.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions (user_id, session_type)
        VALUES (?, ?)
    """, (user_id, "chat"))

    session_id = cursor.lastrowid

    # Simple cognitive scoring rule (basic version)
    accuracy = 1.0 if message.lower() in response.lower() else 0.5

    cursor.execute("""
        INSERT INTO task_logs (session_id, task_type, accuracy, latency, hints_used)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, "memory_recall", accuracy, latency, 0))

    conn.commit()
    conn.close()
    
def update_difficulty(user_id: int):
    conn = sqlite3.connect("cognitive_system.db")
    cursor = conn.cursor()

    # Get last 5 task logs for this user
    cursor.execute("""
        SELECT tl.accuracy
        FROM task_logs tl
        JOIN sessions s ON tl.session_id = s.id
        WHERE s.user_id = ?
        ORDER BY tl.id DESC
        LIMIT 5
    """, (user_id,))

    results = cursor.fetchall()

    if not results:
        conn.close()
        return

    avg_accuracy = sum(r[0] for r in results) / len(results)

    # Get current difficulty
    cursor.execute("SELECT difficulty_level FROM users WHERE id = ?", (user_id,))
    current_difficulty = cursor.fetchone()[0]

    new_difficulty = current_difficulty

    if avg_accuracy > 0.8 and current_difficulty < 5:
        new_difficulty += 1
    elif avg_accuracy < 0.5 and current_difficulty > 1:
        new_difficulty -= 1

    cursor.execute("""
        UPDATE users
        SET difficulty_level = ?
        WHERE id = ?
    """, (new_difficulty, user_id))

    conn.commit()
    conn.close()


app = FastAPI()

@app.on_event("startup")
def startup_event():
    initialize_database()


class ChatRequest(BaseModel):
    user_id: int
    message: str
    
class CreateUserRequest(BaseModel):
    name: str
    age: int
    caregiver_notes: str = ""


@app.get("/")
def root():
    return {"message": "Cognitive AI System Running"}

@app.get("/users")
def get_users():
    conn = sqlite3.connect("cognitive_system.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, age, difficulty_level FROM users")
    users = cursor.fetchall()

    conn.close()

    return {
        "users": [
            {
                "id": u[0],
                "name": u[1],
                "age": u[2],
                "difficulty_level": u[3]
            }
            for u in users
        ]
    }



@app.post("/chat")
def chat(request: ChatRequest):

    start_time = time.time()

    memories = retrieve_memory(request.message, request.user_id)

    # Get current difficulty
    conn = sqlite3.connect("cognitive_system.db")
    cursor = conn.cursor()
    cursor.execute("SELECT difficulty_level FROM users WHERE id = ?", (request.user_id,))
    difficulty = cursor.fetchone()[0]
    conn.close()
    
    full_prompt = f"""
    You are conducting a cognitive training session.
    Current difficulty level: {difficulty}
    (1 = very easy, 5 = very challenging)
    Use the following memory context to answer:
    {context}
    User question:
    {request.message}
    """
    
    
    add_memory(
        text=request.message,
        memory_id=str(uuid.uuid4()),
        user_id=request.user_id
    )

    log_interaction(
        user_id=request.user_id,
        message=request.message,
        response=reply,
        latency=latency
    )
    
    update_difficulty(request.user_id)

    return {
        "response": reply,
        "latency_seconds": round(latency, 2)
    }

@app.post("/users")
def create_user(request: CreateUserRequest):
    conn = sqlite3.connect("cognitive_system.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (name, age, caregiver_notes)
        VALUES (?, ?, ?)
    """, (request.name, request.age, request.caregiver_notes))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "message": "User created successfully",
        "user_id": user_id,
        "difficulty_level": 1
    }
    
