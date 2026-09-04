"""
Authentication helpers: password hashing, JWT creation and verification.

Environment variables:
    JWT_SECRET_KEY  — required in production; a random 32+ character string.
                      Defaults to a placeholder in dev that prints a warning.
    JWT_ALGORITHM   — optional, defaults to HS256.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("kimat.auth")

_JWT_SECRET_KEY_DEFAULT = "CHANGE_THIS_SECRET_IN_PRODUCTION"
SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", _JWT_SECRET_KEY_DEFAULT)
ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

if SECRET_KEY == _JWT_SECRET_KEY_DEFAULT:
    logger.warning(
        "JWT_SECRET_KEY is not set — using an insecure default. "
        "Set JWT_SECRET_KEY in backend/.env before deploying to production."
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Return a bcrypt hash of password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Encode a JWT containing *data* with an expiry claim."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Decode and return the JWT payload, or None if invalid/expired."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
