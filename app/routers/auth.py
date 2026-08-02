"""Account registration, password sign-in, and Google OAuth routes."""

from __future__ import annotations

import secrets
import time
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.models.auth import LoginRequest, SignUpRequest, UserResponse
from app.security.auth import (
    clear_auth_cookie,
    create_signed_payload,
    get_current_user,
    read_signed_payload,
    set_auth_cookie,
)
from app.services import auth_service


router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_STATE_COOKIE = "assessment_google_oauth"


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        has_password=bool(user.password_hash),
        google_connected=bool(user.google_subject),
    )


def _google_is_configured() -> bool:
    settings = get_settings()
    return bool(settings.google_client_id and settings.google_client_secret and settings.google_redirect_uri)


def _oauth_error_redirect(reason: str = "google_sign_in_failed") -> RedirectResponse:
    response = RedirectResponse(f"{get_settings().frontend_url}/login?error={reason}", status_code=303)
    response.delete_cookie(_GOOGLE_STATE_COOKIE, path="/")
    return response


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignUpRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await auth_service.create_password_user(
            db,
            username=payload.username,
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except auth_service.DuplicateAccountError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    response = JSONResponse(_user_response(user).model_dump(), status_code=status.HTTP_201_CREATED)
    set_auth_cookie(response, user)
    return response


@router.post("/login", response_model=UserResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_password(db, email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    response = JSONResponse(_user_response(user).model_dump())
    set_auth_cookie(response, user)
    return response


@router.post("/logout")
async def logout():
    response = JSONResponse({"ok": True})
    clear_auth_cookie(response)
    return response


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return _user_response(current_user)


@router.get("/google/start")
async def google_start():
    if not _google_is_configured():
        return _oauth_error_redirect("google_sign_in_unavailable")
    settings = get_settings()
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    state_cookie = create_signed_payload({
        "typ": "google-oauth-state",
        "state": state,
        "nonce": nonce,
        "exp": int(time.time()) + 600,
    })
    query = urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "prompt": "select_account",
    })
    response = RedirectResponse(f"{_GOOGLE_AUTH_URL}?{query}", status_code=303)
    response.set_cookie(
        _GOOGLE_STATE_COOKIE,
        state_cookie,
        max_age=600,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )
    return response


def _verify_google_id_token(token: str, audience: str) -> dict[str, Any]:
    # Imported lazily so password-only deployments can start before Google
    # OAuth dependencies/configuration are enabled.
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2 import id_token as google_id_token

    return google_id_token.verify_oauth2_token(token, GoogleRequest(), audience)


@router.get("/google/callback")
async def google_callback(request: Request, code: str | None = None, state: str | None = None, db: AsyncSession = Depends(get_db)):
    if not _google_is_configured() or not code or not state:
        return _oauth_error_redirect()
    state_payload = read_signed_payload(request.cookies.get(_GOOGLE_STATE_COOKIE, ""))
    if (
        not state_payload
        or state_payload.get("typ") != "google-oauth-state"
        or not secrets.compare_digest(str(state_payload.get("state", "")), state)
    ):
        return _oauth_error_redirect()

    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            token_response = await client.post(_GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            })
        token_response.raise_for_status()
        identity = await run_in_threadpool(
            _verify_google_id_token, token_response.json()["id_token"], settings.google_client_id
        )
        if identity.get("nonce") != state_payload.get("nonce") or not identity.get("email_verified"):
            return _oauth_error_redirect()
        user = await auth_service.find_or_create_google_user(
            db,
            subject=str(identity["sub"]),
            email=str(identity["email"]).lower(),
            name=str(identity.get("name") or "").strip() or None,
        )
    except (httpx.HTTPError, KeyError, ValueError, auth_service.DuplicateAccountError):
        return _oauth_error_redirect()

    response = RedirectResponse(settings.frontend_url, status_code=303)
    set_auth_cookie(response, user)
    response.delete_cookie(_GOOGLE_STATE_COOKIE, path="/")
    return response
