from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext
from passlib.exc import MissingBackendError

from app.core.config import settings

ALGORITHM = "HS256"
pwd_context = CryptContext(
    # Use pbkdf2_sha256 as default to avoid native bcrypt backend issues in some runtimes.
    # Keep bcrypt in the list to preserve compatibility with existing hashes.
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except MissingBackendError:
        # If a legacy bcrypt hash is present but bcrypt backend is unavailable,
        # avoid crashing the request path.
        return False


def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except MissingBackendError:
        return pwd_context.handler("pbkdf2_sha256").hash(password)


def create_token(subject: str | Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(subject: str | Any) -> str:
    return create_token(subject, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(subject: str | Any) -> str:
    return create_token(subject, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
