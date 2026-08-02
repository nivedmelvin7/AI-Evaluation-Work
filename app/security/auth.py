"""Password hashing, signed sessions, and the current-user dependency."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db


_PASSWORD_ALGORITHM = "scrypt"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DK_LEN = 64


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    """Return a versioned salted scrypt hash; never retain the password itself."""
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=_DK_LEN
    )
    return "$".join((
        _PASSWORD_ALGORITHM,
        str(_SCRYPT_N),
        str(_SCRYPT_R),
        str(_SCRYPT_P),
        _b64encode(salt),
        _b64encode(derived),
    ))


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$")
        if algorithm != _PASSWORD_ALGORITHM:
            return False
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_b64decode(salt),
            n=int(n), r=int(r), p=int(p), dklen=len(_b64decode(expected)),
        )
        return hmac.compare_digest(candidate, _b64decode(expected))
    except (TypeError, ValueError, AttributeError):
        return False


def _sign(value: bytes) -> str:
    return _b64encode(hmac.new(get_settings().secret_key.encode("utf-8"), value, hashlib.sha256).digest())


def create_signed_payload(payload: Dict[str, Any]) -> str:
    encoded = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    return f"{encoded}.{_sign(encoded.encode('ascii'))}"


def read_signed_payload(token: str) -> Dict[str, Any] | None:
    try:
        encoded, signature = token.split(".", 1)
        expected = _sign(encoded.encode("ascii"))
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(_b64decode(encoded))
        if not isinstance(payload, dict) or int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def create_access_token(user: User) -> str:
    settings = get_settings()
    now = int(time.time())
    return create_signed_payload({
        "typ": "assessment-session",
        "sub": str(user.id),
        "iat": now,
        "exp": now + settings.auth_token_expire_minutes * 60,
    })


def set_auth_cookie(response: Response, user: User) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=create_access_token(user),
        max_age=settings.auth_token_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get(get_settings().auth_cookie_name)
    payload = read_signed_payload(token) if token else None
    if not payload or payload.get("typ") != "assessment-session":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in is required.")
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session is invalid. Please sign in again.")
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session is no longer active. Please sign in again.")
    return user
