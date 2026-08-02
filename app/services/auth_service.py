"""Database operations for local and Google-backed accounts."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.security.auth import hash_password, verify_password


class DuplicateAccountError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def find_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    return await db.scalar(select(User).where(User.email == email.lower()))


async def create_password_user(
    db: AsyncSession, *, username: str, email: str, password: str, display_name: Optional[str]
) -> User:
    existing = await db.scalar(select(User.id).where(or_(User.email == email, User.username == username)))
    if existing is not None:
        raise DuplicateAccountError("An account already uses that email address or username.")
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        display_name=display_name or username,
        last_login_at=_utcnow(),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DuplicateAccountError("An account already uses that email address or username.") from exc
    await db.refresh(user)
    return user


async def authenticate_password(db: AsyncSession, *, email: str, password: str) -> Optional[User]:
    user = await find_user_by_email(db, email)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    user.last_login_at = _utcnow()
    await db.commit()
    await db.refresh(user)
    return user


def _username_base(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-._")
    return (value or "user")[:42]


async def _available_username(db: AsyncSession, preferred: str) -> str:
    base = _username_base(preferred)
    for suffix in range(0, 1000):
        candidate = base if suffix == 0 else f"{base[:45]}-{suffix}"
        if await db.scalar(select(User.id).where(User.username == candidate)) is None:
            return candidate
    raise RuntimeError("Could not allocate a username for this account.")


async def find_or_create_google_user(
    db: AsyncSession, *, subject: str, email: str, name: Optional[str]
) -> User:
    user = await db.scalar(select(User).where(User.google_subject == subject))
    if user is None:
        # A verified Google email can be linked to an existing local account.
        user = await find_user_by_email(db, email)
        if user is not None:
            if user.google_subject and user.google_subject != subject:
                raise DuplicateAccountError("This email is already linked to another Google account.")
            user.google_subject = subject
            user.display_name = user.display_name or name
        else:
            user = User(
                username=await _available_username(db, email.split("@", 1)[0]),
                email=email,
                google_subject=subject,
                display_name=name or email.split("@", 1)[0],
            )
            db.add(user)
    user.last_login_at = _utcnow()
    await db.commit()
    await db.refresh(user)
    return user
