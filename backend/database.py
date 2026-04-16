import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("DB_PATH", str(Path(__file__).parent / "dementia_app.db")))
DB_TIMEOUT_SECONDS = float(os.getenv("DB_TIMEOUT_SECONDS", "5"))


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT_SECONDS)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute(f"PRAGMA busy_timeout = {int(DB_TIMEOUT_SECONDS * 1000)};")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                role TEXT DEFAULT 'patient',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS auth_sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS screening_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                status TEXT DEFAULT 'in_progress',
                setting TEXT DEFAULT 'clinical',
                session_number INTEGER DEFAULT 1,
                registration_set TEXT,
                attention_variant TEXT,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                task_number INTEGER,
                domain TEXT,
                answer_text TEXT,
                score_awarded INTEGER,
                max_score INTEGER,
                auto_scored INTEGER DEFAULT 1,
                caregiver_override INTEGER,
                FOREIGN KEY(session_id) REFERENCES screening_sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS screening_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER UNIQUE,
                user_id INTEGER,
                mmse_total REAL,
                domain_scores TEXT,
                ml_prediction TEXT,
                ml_confidence REAL,
                svm_prediction TEXT,
                rf_prediction TEXT,
                mlp_prediction TEXT,
                rule_based TEXT,
                agreement INTEGER,
                ml_features TEXT,
                registration_set TEXT,
                attention_variant TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES screening_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS caregiver_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                caregiver_id INTEGER,
                category TEXT,
                content TEXT,
                embedding_id TEXT,
                ingested INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                rag_context TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chat_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_id INTEGER,
                confusion_score REAL,
                sentiment_score REAL,
                response_length INTEGER,
                vocabulary_diversity REAL,
                alert_keywords TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(message_id) REFERENCES chat_history(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS screening_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                due_date TEXT,
                email_sent INTEGER DEFAULT 0,
                email_sent_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS caregiver_patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caregiver_id INTEGER NOT NULL,
                patient_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(caregiver_id, patient_id),
                FOREIGN KEY(caregiver_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(patient_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_auth_sessions_token ON auth_sessions(token);
            CREATE INDEX IF NOT EXISTS idx_screening_sessions_user_id ON screening_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_screening_results_user_id ON screening_results(user_id);
            CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
            CREATE INDEX IF NOT EXISTS idx_chat_signals_user_id ON chat_signals(user_id);
            CREATE INDEX IF NOT EXISTS idx_caregiver_memories_user_id ON caregiver_memories(user_id);
            CREATE INDEX IF NOT EXISTS idx_caregiver_patients_caregiver ON caregiver_patients(caregiver_id);
            """
        )


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def create_user(username: str, password_hash: str, full_name: str, email: str, role: str = "patient") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, full_name, email, role),
        )
        return int(cur.lastrowid)


def verify_user(username: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return _row_to_dict(row)


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_dict(row)


def create_session_token(user_id: int, hours: int = 24) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO auth_sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at),
        )
    return token, expires_at


def validate_token(token: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT u.* FROM auth_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ? AND datetime(s.expires_at) > datetime('now')
            """,
            (token,),
        ).fetchone()
        return _row_to_dict(row)


def delete_token(token: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))


def get_session_number(user_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(session_number), 0) + 1 AS next_num FROM screening_sessions WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return int(row["next_num"])


def create_screening_session(user_id: int, setting: str) -> dict[str, Any]:
    session_number = get_session_number(user_id)
    reg_map = {
        0: "A",
        1: "B",
        2: "C",
    }
    registration_set = reg_map[session_number % 3]
    attention_variant = "serial_7s" if session_number % 2 == 0 else "world_backwards"
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO screening_sessions
            (user_id, setting, session_number, registration_set, attention_variant)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, setting, session_number, registration_set, attention_variant),
        )
        session_id = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM screening_sessions WHERE id = ?", (session_id,)).fetchone()
        return _row_to_dict(row) or {}


def save_answer(
    session_id: int,
    task_number: int,
    domain: str,
    answer_text: str,
    score_awarded: int,
    max_score: int,
    auto_scored: int = 1,
    caregiver_override: int | None = None,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO answers
            (session_id, task_number, domain, answer_text, score_awarded, max_score, auto_scored, caregiver_override)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, task_number, domain, answer_text, score_awarded, max_score, auto_scored, caregiver_override),
        )
        return int(cur.lastrowid)


def complete_screening_session(session_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE screening_sessions SET status = 'completed', completed_at = datetime('now') WHERE id = ?",
            (session_id,),
        )


def save_result(
    session_id: int,
    user_id: int,
    mmse_total: float,
    domain_scores: dict[str, float],
    ml_prediction: str,
    ml_confidence: float,
    svm_prediction: str,
    rf_prediction: str,
    mlp_prediction: str,
    rule_based: str,
    agreement: int,
    ml_features: list[float],
    registration_set: str,
    attention_variant: str,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT OR REPLACE INTO screening_results
            (session_id, user_id, mmse_total, domain_scores, ml_prediction, ml_confidence,
             svm_prediction, rf_prediction, mlp_prediction, rule_based, agreement,
             ml_features, registration_set, attention_variant)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                mmse_total,
                json.dumps(domain_scores),
                ml_prediction,
                ml_confidence,
                svm_prediction,
                rf_prediction,
                mlp_prediction,
                rule_based,
                agreement,
                json.dumps(ml_features),
                registration_set,
                attention_variant,
            ),
        )
        return int(cur.lastrowid)


def get_user_results(user_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM screening_results WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_results() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM screening_results ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def add_memory(user_id: int, caregiver_id: int, category: str, content: str, embedding_id: str | None = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO caregiver_memories (user_id, caregiver_id, category, content, embedding_id, ingested)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (user_id, caregiver_id, category, content, embedding_id),
        )
        return int(cur.lastrowid)


def get_uningest_memories() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM caregiver_memories WHERE ingested = 0").fetchall()
        return [dict(r) for r in rows]


def mark_ingested(memory_id: int, embedding_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE caregiver_memories SET ingested = 1, embedding_id = ? WHERE id = ?",
            (embedding_id, memory_id),
        )


def get_user_memories(user_id: int) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM caregiver_memories WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def is_caregiver_linked_to_patient(caregiver_id: int, patient_user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM caregiver_memories
            WHERE caregiver_id = ? AND user_id = ?
            LIMIT 1
            """,
            (caregiver_id, patient_user_id),
        ).fetchone()
        return row is not None


def get_linked_patient_ids(caregiver_id: int) -> list[int]:
    """Return patient IDs linked via caregiver_patients table, falling back to caregiver_memories."""
    with get_conn() as conn:
        # Primary: explicit link table
        rows = conn.execute(
            "SELECT patient_id FROM caregiver_patients WHERE caregiver_id = ? ORDER BY created_at ASC",
            (caregiver_id,),
        ).fetchall()
        if rows:
            return [int(r["patient_id"]) for r in rows]
        # Fallback: inferred from memory history
        rows = conn.execute(
            "SELECT DISTINCT user_id FROM caregiver_memories WHERE caregiver_id = ?",
            (caregiver_id,),
        ).fetchall()
        return [int(r["user_id"]) for r in rows if r["user_id"] is not None]


def link_caregiver_to_patient(caregiver_id: int, patient_id: int) -> bool:
    """Create an explicit caregiver-patient link. Returns True if newly created."""
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM caregiver_patients WHERE caregiver_id = ? AND patient_id = ?",
            (caregiver_id, patient_id),
        ).fetchone()
        if existing:
            return False
        conn.execute(
            "INSERT INTO caregiver_patients (caregiver_id, patient_id) VALUES (?, ?)",
            (caregiver_id, patient_id),
        )
        return True


def get_all_patients() -> list[dict[str, Any]]:
    """Return all users with role=patient (for caregiver linking UI)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, full_name, email FROM users WHERE role = 'patient' ORDER BY full_name ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def save_chat(user_id: int, role: str, content: str, rag_context: str | None = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO chat_history (user_id, role, content, rag_context) VALUES (?, ?, ?, ?)",
            (user_id, role, content, rag_context),
        )
        return int(cur.lastrowid)


def get_chat_history(user_id: int, limit: int = 30) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]


def save_signal(
    user_id: int,
    message_id: int,
    confusion_score: float,
    sentiment_score: float,
    response_length: int,
    vocabulary_diversity: float,
    alert_keywords: list[str],
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO chat_signals
            (user_id, message_id, confusion_score, sentiment_score, response_length, vocabulary_diversity, alert_keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                message_id,
                confusion_score,
                sentiment_score,
                response_length,
                vocabulary_diversity,
                json.dumps(alert_keywords),
            ),
        )
        return int(cur.lastrowid)


def get_signals(user_id: int, days: int = 90) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM chat_signals
            WHERE user_id = ? AND datetime(created_at) >= datetime('now', ?)
            ORDER BY created_at DESC
            """,
            (user_id, f"-{days} days"),
        ).fetchall()
        return [dict(r) for r in rows]


def get_last_screening_date(user_id: int) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT completed_at FROM screening_sessions
            WHERE user_id = ? AND status = 'completed'
            ORDER BY datetime(completed_at) DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        return row["completed_at"] if row else None


def create_reminder(user_id: int, due_date: str) -> int:
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM screening_reminders WHERE user_id = ? AND due_date = ?",
            (user_id, due_date),
        ).fetchone()
        if existing:
            return int(existing["id"])
        cur = conn.execute(
            "INSERT INTO screening_reminders (user_id, due_date, email_sent) VALUES (?, ?, 0)",
            (user_id, due_date),
        )
        return int(cur.lastrowid)


def get_pending_reminders() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM screening_reminders WHERE email_sent = 0 ORDER BY created_at ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def mark_reminder_sent(reminder_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE screening_reminders
            SET email_sent = 1, email_sent_at = ?
            WHERE id = ?
            """,
            (datetime.now(timezone.utc).isoformat(), reminder_id),
        )
