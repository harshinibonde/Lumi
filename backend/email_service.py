from __future__ import annotations

import os

import resend

from database import get_user_by_id

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM = os.getenv("RESEND_FROM", "CogniScreen <onboarding@resend.dev>")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:3000")

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def send_screening_reminder(user_id: int) -> bool:
    user = get_user_by_id(user_id)
    if not user:
        return False

    to_email = (user.get("email") or "").strip()
    if not to_email or not RESEND_API_KEY:
        return False

    full_name = user.get("full_name") or user.get("username") or "there"
    button_url = f"{APP_BASE_URL.rstrip('/')}/screening"

    html = f"""
    <div style=\"font-family: Arial, sans-serif; line-height: 1.6; color: #1f2937;\">
      <h2 style=\"margin: 0 0 12px;\">Hello {full_name},</h2>
      <p style=\"margin: 0 0 12px;\">It has been 90 days since your last cognitive screening.</p>
      <p style=\"margin: 0 0 18px;\">A new check-in can help keep your care team updated on your cognitive health.</p>
      <a href=\"{button_url}\"
         style=\"display:inline-block;padding:10px 16px;background:#b45309;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;\">
         Begin Screening
      </a>
      <p style=\"margin: 20px 0 0; font-size: 12px; color: #6b7280;\">
        This is a support tool and does not replace clinical diagnosis or medical advice.
      </p>
    </div>
    """

    resend.Emails.send(
        {
            "from": RESEND_FROM,
            "to": [to_email],
            "subject": "Your 3-month cognitive screening is due",
            "html": html,
        }
    )
    return True


if __name__ == "__main__":
    from database import init_db

    init_db()
    if not RESEND_API_KEY:
        print("No API key set — skipping")
    else:
        print("Email sent:", send_screening_reminder(1))
