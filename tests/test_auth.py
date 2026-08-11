"""Unit tests for password storage and signed application sessions."""

import uuid

import pytest
from pydantic import ValidationError

from app.db.models import User
from app.models.auth import SignUpRequest
from app.security.auth import create_access_token, hash_password, read_signed_payload, verify_password
from app.services import auth_service


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


@pytest.mark.asyncio
async def test_google_sign_in_cannot_bypass_disabled_registration():
    class EmptyDatabase:
        async def scalar(self, _query):
            return None

    with pytest.raises(auth_service.AccountCreationDisabledError):
        await auth_service.find_or_create_google_user(
            EmptyDatabase(),
            subject="google-subject",
            email="new-user@example.com",
            name="New User",
            allow_create=False,
        )


@pytest.mark.asyncio
async def test_existing_account_can_link_google_when_registration_is_disabled():
    existing = User(
        id=uuid.uuid4(),
        username="reviewer",
        email="reviewer@example.com",
        password_hash="hash",
    )

    class ExistingAccountDatabase:
        def __init__(self):
            self.calls = 0

        async def scalar(self, _query):
            self.calls += 1
            return None if self.calls == 1 else existing

        async def commit(self):
            pass

        async def refresh(self, _user):
            pass

    user = await auth_service.find_or_create_google_user(
        ExistingAccountDatabase(),
        subject="google-subject",
        email="reviewer@example.com",
        name="Reviewer",
        allow_create=False,
    )

    assert user is existing
    assert user.google_subject == "google-subject"
