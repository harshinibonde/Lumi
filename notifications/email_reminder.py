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


def send_caregiver_alert(
    to_email: str,
    user_name: str,
    classification: str,
    score: int,
    decision_action: str,
) -> None:
    if not smtp_configured():
        return
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("SMTP_FROM", "")
    subject = os.getenv(
        "CAREGIVER_ALERT_SUBJECT", "LumiAI cognitive screening alert"
    )

    body = (
        f"Hello,\n\n"
        f"A cognitive screening alert was generated for {user_name}.\n\n"
        f"Classification: {classification}\n"
        f"Score: {score}/30\n"
        f"Decision action: {decision_action}\n\n"
        "Please follow your clinical/support workflow for appropriate next steps.\n\n"
        "- Automated LumiAI alert (do not reply)\n"
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
        logger.info("Caregiver alert email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send caregiver alert email to %s", to_email)


def send_otp_email(to_email: str, otp_code: str, name: str):
    subject = "Your Cognitive Companion login code"
    body = (
        f"Hi {name},\n\n"
        f"Your one-time login code is: {otp_code}\n\n"
        "This code expires in 10 minutes.\n"
        "Do not share this code with anyone.\n\n"
        "- Cognitive Companion\n"
    )

    if not smtp_configured():
        logger.warning("SMTP not configured; falling back to console OTP output.")
        print(f"[DEV MODE] OTP for {name} ({to_email}): {otp_code}")
        return

    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("SMTP_FROM", "")

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
        logger.info("OTP email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send OTP email to %s; using console fallback.", to_email)
        print(f"[DEV MODE] OTP for {name} ({to_email}): {otp_code}")
