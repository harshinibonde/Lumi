"""
Seed script: creates 5 test users with varying cognitive profiles,
assessment histories, chat sessions, difficulty progressions,
and caregiver memories.

Run from project root:
    python scripts/seed_test_users.py
"""

import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.db import DB_NAME, initialize_database

# ── Test-user definitions ────────────────────────────────────────

USERS = [
    {
        "name": "Margaret Thompson",
        "age": 72,
        "gender": "F",
        "education_years": 16,
        "handedness": "Right",
        "native_language": "English",
        "lives_alone": 0,
        "patient_email": "margaret.t@example.com",
        "caregiver_name": "David Thompson",
        "caregiver_email": "david.t@example.com",
        "email": "margaret.t@example.com",
        "difficulty_level": 3,
        "is_verified": 1,
        "caregiver_notes": (
            "Margaret is a retired school teacher who loves gardening and reading. "
            "She lives with her husband David. Occasionally forgets where she left her "
            "reading glasses but otherwise sharp. Enjoys crosswords and word games."
        ),
        # Cognitive profile: NORMAL – high accuracy, fast responses
        "assessment_score": 28,
        "classification": "Normal",
        "avg_accuracy": 0.90,
        "avg_latency": 1.8,
        "sessions_count": 18,
        "turns_per_session": 6,
        "difficulty_progression": [1, 2, 2, 3, 3],
    },
    {
        "name": "Arthur Reynolds",
        "age": 78,
        "gender": "M",
        "education_years": 12,
        "handedness": "Right",
        "native_language": "English",
        "lives_alone": 0,
        "patient_email": "arthur.r@example.com",
        "caregiver_name": "Susan Reynolds",
        "caregiver_email": "susan.r@example.com",
        "email": "arthur.r@example.com",
        "difficulty_level": 2,
        "is_verified": 1,
        "caregiver_notes": (
            "Arthur served in the Navy for 25 years. He loves telling stories about "
            "his time at sea. Recently started repeating stories within the same "
            "conversation. Wife Susan noticed he struggles with dates and sometimes "
            "forgets recent phone calls. Still drives and manages daily tasks."
        ),
        # Cognitive profile: MILD IMPAIRMENT – moderate accuracy, slightly slower
        "assessment_score": 22,
        "classification": "Mild Cognitive Impairment",
        "avg_accuracy": 0.72,
        "avg_latency": 3.2,
        "sessions_count": 14,
        "turns_per_session": 5,
        "difficulty_progression": [1, 1, 2, 2, 2],
    },
    {
        "name": "Evelyn Chen",
        "age": 81,
        "gender": "F",
        "education_years": 14,
        "handedness": "Right",
        "native_language": "Mandarin",
        "lives_alone": 1,
        "patient_email": "evelyn.c@example.com",
        "caregiver_name": "Wei Chen",
        "caregiver_email": "wei.c@example.com",
        "email": "evelyn.c@example.com",
        "difficulty_level": 2,
        "is_verified": 1,
        "caregiver_notes": (
            "Evelyn is a former piano teacher who immigrated from Taiwan 40 years ago. "
            "She lives alone since her husband passed. Son Wei visits weekly. "
            "She sometimes leaves the stove on and has trouble recalling what she ate "
            "for breakfast. Her long-term memory is still strong — she plays Chopin "
            "from memory. Prefers conversations about music and her grandchildren."
        ),
        # Cognitive profile: MODERATE IMPAIRMENT – lower accuracy, variable
        "assessment_score": 17,
        "classification": "Moderate Cognitive Impairment",
        "avg_accuracy": 0.55,
        "avg_latency": 4.5,
        "sessions_count": 12,
        "turns_per_session": 4,
        "difficulty_progression": [1, 1, 1, 2, 2],
    },
    {
        "name": "Robert O'Brien",
        "age": 85,
        "gender": "M",
        "education_years": 10,
        "handedness": "Left",
        "native_language": "English",
        "lives_alone": 0,
        "patient_email": "robert.ob@example.com",
        "caregiver_name": "Mary O'Brien",
        "caregiver_email": "mary.ob@example.com",
        "email": "robert.ob@example.com",
        "difficulty_level": 1,
        "is_verified": 1,
        "caregiver_notes": (
            "Robert is a retired carpenter. He lives with his daughter Mary. "
            "He often confuses family members' names and has difficulty following "
            "multi-step instructions. He gets agitated in the evenings (sundowning). "
            "Responds best to simple, warm prompts. Loves talking about building "
            "his daughter's first treehouse."
        ),
        # Cognitive profile: SEVERE IMPAIRMENT – low accuracy, slow, needs hints
        "assessment_score": 10,
        "classification": "Severe Cognitive Impairment",
        "avg_accuracy": 0.35,
        "avg_latency": 6.5,
        "sessions_count": 8,
        "turns_per_session": 3,
        "difficulty_progression": [1, 1, 1, 1, 1],
    },
    {
        "name": "Dorothy Patel",
        "age": 69,
        "gender": "F",
        "education_years": 18,
        "handedness": "Right",
        "native_language": "English",
        "lives_alone": 0,
        "patient_email": "dorothy.p@example.com",
        "caregiver_name": "Raj Patel",
        "caregiver_email": "raj.p@example.com",
        "email": "dorothy.p@example.com",
        "difficulty_level": 4,
        "is_verified": 1,
        "caregiver_notes": (
            "Dorothy is a retired professor of literature. She is the primary "
            "caregiver for her husband Raj who has Parkinson's. Very intellectually "
            "active — reads two books a week, writes poetry. No cognitive concerns; "
            "using Lumi for preventative screening and to stay mentally engaged."
        ),
        # Cognitive profile: HIGH NORMAL – excellent accuracy, fast
        "assessment_score": 30,
        "classification": "Normal",
        "avg_accuracy": 0.95,
        "avg_latency": 1.3,
        "sessions_count": 22,
        "turns_per_session": 8,
        "difficulty_progression": [2, 3, 3, 4, 4],
    },
]

# ── Chat conversation samples per profile ────────────────────────

CHAT_EXCHANGES = {
    "Normal": [
        ("Good morning! I had the loveliest walk in the garden today.", "That sounds wonderful! What flowers are blooming in your garden right now?"),
        ("The daffodils and tulips are out. David planted new roses last autumn.", "How delightful! Do you remember what variety of roses David chose?"),
        ("I believe they were English roses — the David Austin kind, ironically!", "Ha! That's a lovely coincidence. Do you have a favourite colour among them?"),
        ("I finished my crossword in record time today — 12 minutes!", "Impressive! What was the trickiest clue you solved?"),
        ("Something about a seven-letter word for 'resilience'. It was 'stamina'.", "Great vocabulary! Would you like to try a word challenge with me?"),
        ("We visited the grandchildren this weekend. Little Sophie is learning piano.", "How wonderful! Does Sophie remind you of anyone in the family?"),
    ],
    "Mild Cognitive Impairment": [
        ("I was telling Susan about my time on the USS Constellation.", "That's a wonderful memory, Arthur. What year were you stationed there?"),
        ("It was... I think around 1972. Or was it '74? The Pacific deployment.", "The details might be fuzzy but the experience clearly meant a lot. What do you remember most vividly?"),
        ("The sunsets at sea. Nothing like them anywhere else.", "That's beautiful. Did you ever photograph those sunsets?"),
        ("Did I tell you about my time on the Constellation?", "You mentioned it a little earlier! You were talking about the beautiful sunsets at sea."),
        ("Oh right, right. The sunsets. Susan says I repeat myself sometimes.", "It's very natural. Those powerful memories want to be shared! What else from your Navy days stands out?"),
    ],
    "Moderate Cognitive Impairment": [
        ("I played some music today. Chopin.", "Lovely! Which Chopin piece did you play, Evelyn?"),
        ("The... the night one. The famous one.", "The Nocturne? That's one of the most beautiful pieces ever written."),
        ("Yes! My fingers still remember even when my head forgets.", "Music memory is remarkable that way. How long have you been playing piano?"),
        ("Wei came to visit. Or was that yesterday?", "Either way, it's nice to have Wei's company. What did you two talk about?"),
    ],
    "Severe Cognitive Impairment": [
        ("I built something once. A house... a small house.", "Was it the treehouse you built for Mary? She's told me about it."),
        ("Mary? She's... my daughter, yes.", "That's right. She loves you very much. What tools did you use to build things?"),
        ("Hammer. I know hammer. And the... the cutting thing.", "A saw! You must have been very skilled with your hands."),
    ],
}

TASK_FOCUSES = ["memory_recall", "language_fluency", "attention", "orientation", "general engagement"]


def _ts(days_ago: int, hour: int = 10) -> str:
    """Return an ISO timestamp N days ago at the given hour."""
    dt = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 3))
    dt = dt.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def seed():
    initialize_database()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    created_ids = []

    for u in USERS:
        # ── 1. Create user ────────────────────────────────────────
        cur.execute(
            """
            INSERT INTO users (
                name, age, caregiver_notes, difficulty_level,
                email, patient_email, caregiver_name, caregiver_email,
                gender, education_years, handedness, native_language,
                lives_alone, is_verified
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                u["name"], u["age"], u["caregiver_notes"], u["difficulty_level"],
                u["email"], u["patient_email"], u["caregiver_name"], u["caregiver_email"],
                u["gender"], u["education_years"], u["handedness"], u["native_language"],
                u["lives_alone"], u["is_verified"],
            ),
        )
        uid = cur.lastrowid
        created_ids.append(uid)
        print(f"  ✓ User #{uid}: {u['name']} ({u['classification']}, difficulty {u['difficulty_level']})")

        # ── 2. Create assessment ──────────────────────────────────
        svm_cls = u["classification"]
        rf_cls = u["classification"]
        mlp_cls = u["classification"]
        conf = round(0.65 + random.uniform(0, 0.30), 4)

        cur.execute(
            """
            INSERT INTO assessments (
                user_id, score, classification,
                score_classification, final_classification,
                svm_classification, random_forest_classification, mlp_classification,
                decision_action, model_confidence, pipeline_version, timestamp
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                uid, u["assessment_score"], u["classification"],
                u["classification"], u["classification"],
                svm_cls, rf_cls, mlp_cls,
                "continue_monitoring" if u["assessment_score"] >= 24 else "schedule_followup",
                conf,
                "v2-ensemble",
                _ts(random.randint(5, 30)),
            ),
        )

        # ── 3. Create sessions + chat turns ───────────────────────
        exchanges = CHAT_EXCHANGES.get(u["classification"], CHAT_EXCHANGES["Normal"])
        base_acc = u["avg_accuracy"]
        base_lat = u["avg_latency"]

        for s_idx in range(u["sessions_count"]):
            days_ago = u["sessions_count"] - s_idx  # older sessions first
            session_ts = _ts(days_ago, hour=random.choice([9, 10, 14, 15, 19]))

            cur.execute(
                "INSERT INTO sessions (user_id, session_type, timestamp) VALUES (?,?,?)",
                (uid, random.choice(["chat", "proactive_manual", "scheduled_proactive"]), session_ts),
            )
            sid = cur.lastrowid

            n_turns = u["turns_per_session"] + random.randint(-1, 2)
            n_turns = max(2, min(n_turns, len(exchanges)))

            for t_idx in range(n_turns):
                ex = exchanges[t_idx % len(exchanges)]
                acc = round(max(0.1, min(1.0, base_acc + random.uniform(-0.15, 0.10))), 3)
                lat = round(max(0.5, base_lat + random.uniform(-0.8, 1.5)), 2)
                focus = random.choice(TASK_FOCUSES)

                cur.execute(
                    """
                    INSERT INTO task_logs (
                        session_id, task_type, accuracy, latency, hints_used,
                        user_message, assistant_message, task_focus
                    ) VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (
                        sid,
                        "chat_turn" if t_idx > 0 else "proactive_open",
                        acc, lat,
                        random.randint(0, 2) if base_acc < 0.6 else 0,
                        ex[0], ex[1], focus,
                    ),
                )

        # ── 4. Difficulty progression ─────────────────────────────
        prog = u["difficulty_progression"]
        for i in range(1, len(prog)):
            if prog[i] != prog[i - 1]:
                cur.execute(
                    "INSERT INTO difficulty_history (user_id, old_level, new_level, created_at) VALUES (?,?,?,?)",
                    (uid, prog[i - 1], prog[i], _ts(u["sessions_count"] - i * 3)),
                )

    conn.commit()
    conn.close()

    print(f"\n✅ Seeded {len(created_ids)} test users (IDs: {created_ids})")
    print("   Run the backend with: uvicorn app.main:app --reload")
    print("   Then browse to the dashboard to see their analytics.")
    return created_ids


if __name__ == "__main__":
    print("🌱 Seeding test users into", DB_NAME, "...\n")
    seed()
