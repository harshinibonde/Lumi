import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

DB_NAME = os.getenv("COGNITIVE_DB_PATH", str(_PROJECT_ROOT / "cognitive_system.db"))


def get_connection():
    return sqlite3.connect(DB_NAME)


def _migrate_task_logs_text_columns(cursor):
    cursor.execute("PRAGMA table_info(task_logs)")
    cols = {row[1] for row in cursor.fetchall()}
    if "user_message" not in cols:
        cursor.execute("ALTER TABLE task_logs ADD COLUMN user_message TEXT")
    if "assistant_message" not in cols:
        cursor.execute("ALTER TABLE task_logs ADD COLUMN assistant_message TEXT")
    if "task_focus" not in cols:
        cursor.execute("ALTER TABLE task_logs ADD COLUMN task_focus TEXT")


def _migrate_users_email(cursor):
    cursor.execute("PRAGMA table_info(users)")
    cols = {row[1] for row in cursor.fetchall()}
    if "email" not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")


def _ensure_difficulty_history(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS difficulty_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            old_level INTEGER NOT NULL,
            new_level INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)


def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            caregiver_notes TEXT,
            difficulty_level INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            task_type TEXT,
            accuracy REAL,
            latency REAL,
            hints_used INTEGER,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)

    _migrate_task_logs_text_columns(cursor)
    _migrate_users_email(cursor)
    _ensure_difficulty_history(cursor)

    conn.commit()
    conn.close()


def log_difficulty_change(user_id: int, old_level: int, new_level: int) -> None:
    if old_level == new_level:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO difficulty_history (user_id, old_level, new_level)
        VALUES (?, ?, ?)
        """,
        (user_id, old_level, new_level),
    )
    conn.commit()
    conn.close()


def fetch_difficulty_history(user_id: int, limit: int = 200) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT old_level, new_level, created_at
        FROM difficulty_history
        WHERE user_id = ?
        ORDER BY id ASC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"old_level": r[0], "new_level": r[1], "created_at": r[2]} for r in rows
    ]


def fetch_sessions_per_day(user_id: int, days: int = 90) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT date(timestamp) AS d, COUNT(*) AS c
        FROM sessions
        WHERE user_id = ?
          AND date(timestamp) >= date('now', ?)
        GROUP BY date(timestamp)
        ORDER BY d ASC
        """,
        (user_id, f"-{int(days)} days"),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"day": r[0], "sessions": r[1]} for r in rows]


def create_session(user_id: int, session_type: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (user_id, session_type) VALUES (?, ?)",
        (user_id, session_type),
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def log_task(
    session_id: int,
    task_type: str,
    user_message: str,
    assistant_message: str,
    accuracy: float,
    latency: float,
    hints_used: int = 0,
    task_focus: str = "",
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO task_logs (
            session_id, task_type, accuracy, latency, hints_used,
            user_message, assistant_message, task_focus
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            task_type,
            accuracy,
            latency,
            hints_used,
            user_message,
            assistant_message,
            task_focus or "",
        ),
    )
    conn.commit()
    conn.close()


def get_user(user_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, age, caregiver_notes, difficulty_level, email
        FROM users WHERE id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "age": row[2],
        "caregiver_notes": row[3] or "",
        "difficulty_level": row[4],
        "email": row[5] or "",
    }


def fetch_user_task_history(user_id: int, limit: int = 500) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT tl.id, tl.accuracy, tl.latency, tl.task_type, tl.hints_used,
               IFNULL(s.timestamp, ''), s.session_type,
               IFNULL(tl.task_focus, '')
        FROM task_logs tl
        JOIN sessions s ON tl.session_id = s.id
        WHERE s.user_id = ?
        ORDER BY tl.id ASC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "log_id": r[0],
            "accuracy": r[1],
            "latency": r[2],
            "task_type": r[3],
            "hints_used": r[4],
            "session_timestamp": r[5],
            "session_type": r[6],
            "task_focus": r[7],
        }
        for r in rows
    ]


def session_belongs_to_user(session_id: int, user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
    )
    ok = cursor.fetchone() is not None
    conn.close()
    return ok


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
