"""Request and response models for application authentication."""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, field_validator


_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,49}$")


class SignUpRequest(BaseModel):
    username: str
    email: str
    password: str
    display_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip().lower()
        if not _USERNAME_RE.fullmatch(value):
            raise ValueError("Username must be 3-50 characters using letters, numbers, ., _, or -.")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) > 320 or not _EMAIL_RE.fullmatch(value):
            raise ValueError("Enter a valid email address.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not 12 <= len(value) <= 1024:
            raise ValueError("Password must be between 12 and 1024 characters.")
        return value

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 255:
            raise ValueError("Display name must be 255 characters or fewer.")
        return value or None


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_RE.fullmatch(value):
            raise ValueError("Enter a valid email address.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value or len(value) > 1024:
            raise ValueError("Enter your password.")
        return value


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: Optional[str] = None
    has_password: bool
    google_connected: bool

