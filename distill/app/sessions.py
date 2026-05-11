import secrets
from collections.abc import Callable
from datetime import timedelta

from itsdangerous import BadSignature, TimestampSigner
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

_COOKIE_NAME = "lectern_sid"
_COOKIE_MAX_AGE = timedelta(days=30)
_signer = TimestampSigner(settings.session_cookie_secret.get_secret_value())


def get_session_id(request: Request) -> str:
    """Return the session ID stashed by SessionMiddleware, falling back to the cookie."""
    if hasattr(request.state, "session_id"):
        return request.state.session_id
    raw = request.cookies.get(_COOKIE_NAME)
    if raw:
        try:
            return _signer.unsign(raw, max_age=int(_COOKIE_MAX_AGE.total_seconds())).decode()
        except BadSignature:
            pass
    return _mint_session_id()


def _mint_session_id() -> str:
    return secrets.token_urlsafe(32)


class SessionMiddleware(BaseHTTPMiddleware):
    """Resolve or mint a session ID, stash it on request.state, and set the cookie."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        existing = request.cookies.get(_COOKIE_NAME)
        session_id: str | None = None

        if existing:
            try:
                session_id = _signer.unsign(
                    existing, max_age=int(_COOKIE_MAX_AGE.total_seconds())
                ).decode()
            except BadSignature:
                session_id = None

        mint_cookie = session_id is None
        if mint_cookie:
            session_id = _mint_session_id()

        request.state.session_id = session_id
        response = await call_next(request)

        if mint_cookie:
            response.set_cookie(
                key=_COOKIE_NAME,
                value=_signer.sign(session_id).decode(),
                max_age=_COOKIE_MAX_AGE,
                httponly=True,
                secure=not settings.is_dev,
                samesite="lax",
            )
        return response
