from __future__ import annotations


def generate_otp() -> str:
    import random

    return str(random.randint(100000, 999999))


def generate_session_token() -> str:
    import secrets

    return secrets.token_hex(32)


def is_otp_valid(otp_code: str, otp_expires_at: str, submitted_otp: str) -> bool:
    from datetime import datetime

    if submitted_otp != otp_code:
        return False
    expiry = datetime.fromisoformat(otp_expires_at)
    return datetime.utcnow() < expiry
