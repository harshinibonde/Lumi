import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))


def send_cognitive_reminder(to_email: str, user_name: str, opening_preview: str) -> None:
    if not smtp_configured():
        return
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("SMTP_FROM", "")
    subject = os.getenv(
        "REMINDER_EMAIL_SUBJECT", "Your daily cognitive check-in is ready"
    )

    body = (
        f"Hi {user_name},\n\n"
        "Your cognitive companion has a new check-in message for you.\n\n"
        f"Preview:\n{opening_preview[:500]}\n\n"
        "Open your Cognitive AI app to continue the conversation.\n\n"
        "— Automated message (do not reply)\n"
    )

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls(context=context)
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_email], msg.as_string())
        logger.info("Reminder email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send reminder email to %s", to_email)
