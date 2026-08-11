"""Small ASGI middleware used to harden browser-facing deployments."""

from http.cookies import SimpleCookie
from typing import Iterable
from urllib.parse import urlsplit

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse


_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _normalise_origin(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return ""
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


class OriginProtectionMiddleware:
    """Require a trusted browser Origin for cookie-authenticated mutations."""

    def __init__(self, app, *, trusted_origins: Iterable[str], cookie_name: str):
        self.app = app
        self.trusted_origins = {
            origin
            for value in trusted_origins
            if (origin := _normalise_origin(value))
        }
        self.cookie_name = cookie_name

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"].upper() in _UNSAFE_METHODS:
            headers = Headers(scope=scope)
            cookies = SimpleCookie()
            cookies.load(headers.get("cookie", ""))
            if self.cookie_name in cookies:
                origin = _normalise_origin(headers.get("origin", ""))
                if origin not in self.trusted_origins:
                    response = JSONResponse(
                        {"detail": "Request origin is not allowed."},
                        status_code=403,
                    )
                    await response(scope, receive, send)
                    return
        await self.app(scope, receive, send)


class SecurityHeadersMiddleware:
    def __init__(self, app, *, production: bool):
        self.app = app
        self.production = production

    async def __call__(self, scope, receive, send):
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("X-Frame-Options", "DENY")
                headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
                headers.setdefault(
                    "Permissions-Policy",
                    "camera=(), microphone=(), geolocation=()",
                )
                if self.production:
                    headers.setdefault(
                        "Content-Security-Policy",
                        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                        "img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; "
                        "worker-src 'self' blob:; object-src 'none'; base-uri 'self'; "
                        "form-action 'self'; frame-ancestors 'none'",
                    )
                    headers.setdefault(
                        "Strict-Transport-Security",
                        "max-age=31536000; includeSubDomains",
                    )
            await send(message)

        await self.app(scope, receive, send_with_headers)
