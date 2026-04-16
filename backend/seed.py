from __future__ import annotations

from auth_router import pwd_context
from database import add_memory, create_user, init_db, verify_user
from rag import ingest_pending_memories


def ensure_user(username: str, password: str, full_name: str, email: str, role: str) -> int:
    existing = verify_user(username)
    if existing:
        print(f"User exists: {username} (id={existing['id']})")
        return int(existing["id"])

    password_hash = pwd_context.hash(password)
    user_id = create_user(
        username=username,
        password_hash=password_hash,
        full_name=full_name,
        email=email,
        role=role,
    )
    print(f"Created user: {username} (id={user_id})")
    return user_id


def main() -> None:
    init_db()
    print("Database initialized")

    patient_id = ensure_user(
        username="patient1",
        password="test123",
        full_name="Patient One",
        email="patient@test.com",
        role="patient",
    )

    caregiver_id = ensure_user(
        username="caregiver1",
        password="test123",
        full_name="Caregiver One",
        email="caregiver@test.com",
        role="caregiver",
    )

    memory_payloads = [
        ("Family", "Patient enjoys weekly calls with daughter on Sundays."),
        ("Routine", "Patient usually has tea at 4 PM and takes an evening walk."),
        ("Preference", "Patient prefers calm music and short, simple instructions."),
    ]

    for category, content in memory_payloads:
        memory_id = add_memory(
            user_id=patient_id,
            caregiver_id=caregiver_id,
            category=category,
            content=content,
        )
        print(f"Added memory ({category}) id={memory_id}")

    ingested_count = ingest_pending_memories()
    print(f"Ingested pending memories into ChromaDB: {ingested_count}")
    print("Seed completed")


if __name__ == "__main__":
    main()
