from __future__ import annotations

import os
import logging
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from dotenv import load_dotenv
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, field_validator

from database import (
    create_session_token,
    create_user,
    delete_token,
    get_conn,
    get_user_by_id,
    validate_token,
    verify_user,
)
from scheduler import check_and_send_reminder, get_screening_status

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Password handling — bcrypt directly (no passlib)
# ---------------------------------------------------------------------------
def _hash_password(password: str) -> str:
    """Hash a password with bcrypt. Truncates to 72 bytes (bcrypt hard limit)."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash. Constant-time comparison."""
    pw_bytes = password.encode("utf-8")[:72]
    hash_bytes = password_hash.encode("utf-8")
    try:
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except (ValueError, TypeError):
        return False


def _validate_password(password: str) -> str:
    """Validate password constraints before hashing."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"Password must not exceed {MAX_PASSWORD_LENGTH} characters",
        )
    return password


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: EmailStr
    role: str = "patient"

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 64:
            raise ValueError("Username must not exceed 64 characters")
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("patient", "caregiver"):
            raise ValueError("Role must be 'patient' or 'caregiver'")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username is required")
        return v

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("Password is required")
        return v


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
def create_access_token(user_id: int, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------
def get_current_user(authorization: str = Header(default="")) -> dict:
    """Resolve and validate current user from bearer token."""
    if not authorization.startswith("Bearer "):
        logger.warning("Authentication failed: missing bearer token")
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.replace("Bearer ", "", 1).strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        logger.warning("Authentication failed: invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")

    session_user = validate_token(token)
    if not session_user:
        logger.warning("Authentication failed: expired or revoked session")
        raise HTTPException(status_code=401, detail="Expired or revoked session")

    user = get_user_by_id(user_id)
    if not user:
        logger.warning("Authentication failed: user id %s not found", user_id)
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_role(role: str):
    def _inner(user: dict = Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return _inner


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/register")
def register(payload: RegisterRequest):
    """Create a new user account."""
    existing = verify_user(payload.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    _validate_password(payload.password)
    password_hash = _hash_password(payload.password)
    user_id = create_user(
        username=payload.username,
        password_hash=password_hash,
        full_name=payload.full_name,
        email=str(payload.email),
        role=payload.role,
    )
    return {"user_id": user_id, "message": "Registered"}


@router.post("/login")
def login(payload: LoginRequest):
    """Authenticate user and return JWT token with profile."""
    user = verify_user(payload.username)

    # Timing-attack prevention: hash a dummy if user not found
    if not user:
        _hash_password("dummy-timing-attack-prevention")
        logger.warning("Login failed: username=%s not found", payload.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not _verify_password(payload.password, user["password_hash"]):
        logger.warning("Login failed: bad password for username=%s", payload.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = int(user["id"])
    access_token = create_access_token(user_id, user["username"], user.get("role", "patient"))

    # Store JWT in auth_sessions for server-side revocation
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO auth_sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (access_token, user_id, expires_at),
        )

    screening_status = get_screening_status(user_id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "username": user["username"],
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "role": user.get("role", "patient"),
        },
        "screening_status": screening_status,
    }


@router.post("/logout")
def logout(authorization: str = Header(default="")):
    """Invalidate current session token if present."""
    if not authorization.startswith("Bearer "):
        return {"message": "Logged out"}
    token = authorization.replace("Bearer ", "", 1).strip()
    if token:
        delete_token(token)
    return {"message": "Logged out"}


@router.get("/me")
def me(background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    """Return authenticated profile and screening reminder status."""
    user_id = int(user["id"])
    status = get_screening_status(user_id)
    background_tasks.add_task(check_and_send_reminder, user_id)

    return {
        "id": user_id,
        "username": user["username"],
        "full_name": user.get("full_name"),
        "email": user.get("email"),
        "role": user.get("role", "patient"),
        "screening_due": status.get("screening_due", False),
        "days_overdue": status.get("days_overdue"),
        "days_until_due": status.get("days_until_due"),
        "next_due": status.get("next_due"),
        "last_screening": status.get("last_screening"),
    }
