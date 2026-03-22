import sqlite3

DB_NAME = "cognitive_system.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def _migrate_task_logs_text_columns(cursor):
    cursor.execute("PRAGMA table_info(task_logs)")
    cols = {row[1] for row in cursor.fetchall()}
    if "user_message" not in cols:
        cursor.execute("ALTER TABLE task_logs ADD COLUMN user_message TEXT")
    if "assistant_message" not in cols:
        cursor.execute("ALTER TABLE task_logs ADD COLUMN assistant_message TEXT")


def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            caregiver_notes TEXT,
            difficulty_level INTEGER DEFAULT 1
        )
    """)

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Task logs table
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

    conn.commit()
    conn.close()


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
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO task_logs (
            session_id, task_type, accuracy, latency, hints_used,
            user_message, assistant_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            task_type,
            accuracy,
            latency,
            hints_used,
            user_message,
            assistant_message,
        ),
    )
    conn.commit()
    conn.close()


def get_user(user_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, age, caregiver_notes, difficulty_level
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
    }


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