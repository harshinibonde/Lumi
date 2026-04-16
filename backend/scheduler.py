from __future__ import annotations

from datetime import datetime, timedelta, timezone

from database import get_conn, get_last_screening_date
from email_service import send_screening_reminder


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def get_screening_status(user_id: int) -> dict:
    last_str = get_last_screening_date(user_id)
    last_dt = _parse_datetime(last_str)

    if last_dt is None:
        return {
            "screening_due": True,
            "days_overdue": None,
            "last_screening": None,
            "next_due": None,
            "days_until_due": None,
        }

    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    days_since = (now.date() - last_dt.date()).days
    next_due_dt = last_dt + timedelta(days=90)

    if days_since >= 90:
        return {
            "screening_due": True,
            "days_overdue": int(days_since - 90),
            "last_screening": last_dt.date().isoformat(),
            "next_due": next_due_dt.date().isoformat(),
            "days_until_due": 0,
        }

    return {
        "screening_due": False,
        "days_overdue": 0,
        "days_until_due": int(90 - days_since),
        "last_screening": last_dt.date().isoformat(),
        "next_due": next_due_dt.date().isoformat(),
    }


def check_and_send_reminder(user_id: int) -> bool:
    status = get_screening_status(user_id)
    if not status["screening_due"]:
        return False

    with get_conn() as conn:
        recent = conn.execute(
            """
            SELECT id FROM screening_reminders
            WHERE user_id = ?
              AND email_sent = 1
              AND datetime(created_at) >= datetime('now', '-90 days')
            ORDER BY datetime(created_at) DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if recent:
            return False

    sent = send_screening_reminder(user_id)
    if not sent:
        return False

    due_date = status.get("next_due") or datetime.now(timezone.utc).date().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO screening_reminders (user_id, due_date, email_sent, email_sent_at)
            VALUES (?, ?, 1, ?)
            """,
            (user_id, due_date, datetime.now(timezone.utc).isoformat()),
        )
    return True


if __name__ == "__main__":
    from database import init_db

    init_db()
    test_user_id = 1
    print("Screening status:", get_screening_status(test_user_id))
    print("Reminder sent:", check_and_send_reminder(test_user_id))
