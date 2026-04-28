import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.config import settings


def generate_magic_link_token() -> tuple[str, str]:
    """Generate a magic-link token.

    Returns (plain_token, sha256_hash). Persist only the hash;
    the plain token is sent in the email exactly once.
    """
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session_jwt(user_id: UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.jwt_expire_days)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_session_jwt(token: str) -> UUID | None:
    """Decode and validate a session JWT. Returns the user_id, or None on failure."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        return None
