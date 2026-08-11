"""Unit tests for password storage and signed application sessions."""

import uuid

import pytest
from pydantic import ValidationError

from app.db.models import User
from app.models.auth import SignUpRequest
from app.security.auth import create_access_token, hash_password, read_signed_payload, verify_password


def test_passwords_are_salted_scrypt_hashes_and_verify_in_constant_time_path():
    first = hash_password("a secure passphrase")
    second = hash_password("a secure passphrase")

    assert first.startswith("scrypt$")
    assert first != second
    assert verify_password("a secure passphrase", first)
    assert not verify_password("wrong password", first)
    assert not verify_password("a secure passphrase", None)


def test_access_token_is_signed_and_tampering_is_rejected():
    user = User(id=uuid.uuid4(), username="engineer", email="engineer@example.com", password_hash="hash")
    token = create_access_token(user)
    assert read_signed_payload(token)["sub"] == str(user.id)

    payload, signature = token.split(".")
    replacement = "A" if payload[-1] != "A" else "B"
    assert read_signed_payload(f"{payload[:-1]}{replacement}.{signature}") is None


def test_signup_requires_a_safe_username_email_and_password():
    request = SignUpRequest(
        username="Engineering.User",
        email="ENGINEER@example.com",
        password="a secure passphrase",
    )
    assert request.username == "engineering.user"
    assert request.email == "engineer@example.com"

    with pytest.raises(ValidationError):
        SignUpRequest(username="x", email="not-an-email", password="short")
