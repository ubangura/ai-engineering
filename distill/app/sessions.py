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
    """Return the verified session_id from the cookie, or a newly minted one."""
    raw = request.cookies.get(_COOKIE_NAME)
    if raw:
        try:
            return _signer.unsign(
                raw, max_age=int(_COOKIE_MAX_AGE.total_seconds())
            ).decode()
        except BadSignature:
            pass
    return _mint_session_id()


def _mint_session_id() -> str:
    return secrets.token_urlsafe(32)


class SessionMiddleware(BaseHTTPMiddleware):
    """Set a signed session cookie on every response if one isn't already present."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        existing = request.cookies.get(_COOKIE_NAME)
        if existing:
            try:
                _signer.unsign(existing, max_age=int(_COOKIE_MAX_AGE.total_seconds()))
                response = await call_next(request)
                return response
            except BadSignature:
                pass

        session_id = _mint_session_id()
        signed = _signer.sign(session_id).decode()
        response = await call_next(request)
        response.set_cookie(
            key=_COOKIE_NAME,
            value=signed,
            max_age=_COOKIE_MAX_AGE,
            httponly=True,
            secure=not settings.is_dev,
            samesite="lax",
        )
        return response
