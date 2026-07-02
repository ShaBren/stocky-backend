"""
Authentication utilities for session-based auth and password hashing.
"""

import secrets
import string

from fastapi import Request, Response

from ..core.config import settings

# Password hashing context
# Use direct bcrypt to avoid passlib compatibility issues with Python 3.13
import bcrypt as _bcrypt


class BcryptContext:
    """Direct bcrypt wrapper to avoid passlib compatibility issues"""

    @staticmethod
    def hash(password: str) -> str:
        """Hash a password using bcrypt"""
        # Encode password and ensure it's not longer than 72 bytes
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        # Generate salt and hash
        salt = _bcrypt.gensalt(rounds=12)
        hashed_bytes = _bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode("utf-8")

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        try:
            # Encode password and ensure it's not longer than 72 bytes
            password_bytes = password.encode("utf-8")
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]

            # Verify password
            hashed_bytes = hashed.encode("utf-8")
            return _bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False


pwd_context = BcryptContext()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


# Alias for compatibility
get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ── Session cookie helpers ──────────────────────────────────────────

def set_session_cookie(response: Response, token: str, persistent: bool = False) -> None:
    """Set the session cookie on the response."""
    max_age = (
        settings.PERSISTENT_SESSION_EXPIRE_DAYS * 86400
        if persistent
        else settings.SESSION_EXPIRE_HOURS * 3600
    )
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
    )


def get_session_token_from_cookie(request: Request) -> str | None:
    """Extract the session token from the request cookie."""
    return request.cookies.get(settings.COOKIE_NAME)


def clear_session_cookie(response: Response) -> None:
    """Clear the session cookie."""
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
    )
