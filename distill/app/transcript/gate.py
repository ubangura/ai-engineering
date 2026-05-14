import asyncio
from typing import Any
from urllib.parse import parse_qs, urlparse

import yt_dlp
from models.domain import ErrorResponse, VideoMetadata
from yt_dlp.utils import DownloadError

from app.config import settings


def _extract_video_id(url: str) -> str | None:
    parsed = urlparse(url.strip())
    hostname = parsed.hostname
    hostname = hostname.lower() if hostname else None

    if hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2]
        elif parsed.path.startswith("/embed/"):
            video_id = parsed.path.split("/")[2]
        else:
            video_id = parse_qs(parsed.query).get("v", [None])[0]
    elif hostname == "youtu.be":
        video_id = parsed.path.lstrip("/")
    else:
        return None

    return video_id if video_id and len(video_id) == 11 else None


class GateRejection(Exception):
    def __init__(self, error: ErrorResponse):
        self.error = error
        super().__init__(error.code)


async def run_gate(url: str) -> VideoMetadata:
    """
    Fetch YouTube metadata.
    Raises `GateRejection` for any unsupported input.
    Returns `VideoMetadata` on success.
    """
    url = url.strip()

    video_id = _extract_video_id(url)
    if video_id is None:
        raise GateRejection(
            ErrorResponse(
                code="not_found",
                detail="Could not find a YouTube video matching that URL.",
            )
        )

    info = await _fetch_info(url)
    return _validate(video_id, info)


async def _fetch_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "js_runtimes": {"node": {"path": settings.yt_dlp_node_path}},
        "remote_components": ["ejs:github"],
        **(
            {"cookiefile": settings.youtube_cookies_path}
            if settings.youtube_cookies_path
            else {}
        ),
    }

    for attempt in range(3):
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, _extract, url, ydl_opts)
        except DownloadError as exc:
            msg = str(exc).lower()
            if "private" in msg or "unavailable" in msg:
                raise GateRejection(
                    ErrorResponse(
                        code="private",
                        detail="This video isn't publicly available.",
                    )
                ) from exc
            if "sign in" in msg or "age" in msg:
                raise GateRejection(
                    ErrorResponse(
                        code="age_restricted",
                        detail="This video requires sign-in to view.",
                    )
                ) from exc

            await asyncio.sleep(2**attempt)

    raise GateRejection(
        ErrorResponse(
            code="internal_error",
            detail="Couldn't reach YouTube. Please try again in a moment.",
        )
    )


def _extract(url: str, opts: dict[str, Any]) -> Any:
    with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
        return ydl.extract_info(url, download=False)


def _validate(video_id: str, info: dict) -> VideoMetadata:
    is_live = bool(info.get("is_live"))
    if is_live:
        raise GateRejection(
            ErrorResponse(
                code="livestream",
                detail="Livestreams aren't supported. Try an uploaded lecture.",
            )
        )

    availability = info.get("availability", "")
    if availability in ("private", "premium_only", "subscriber_only", "needs_auth"):
        raise GateRejection(
            ErrorResponse(
                code="private",
                detail="This video isn't publicly available.",
            )
        )

    age_limit = int(info.get("age_limit", 0))
    if age_limit > 0:
        raise GateRejection(
            ErrorResponse(
                code="age_restricted",
                detail="This video is age-restricted, requiring sign-in to view.",
            )
        )

    duration = int(info.get("duration", 0))
    if duration <= 0:
        raise GateRejection(
            ErrorResponse(
                code="internal_error",
                detail="Couldn't determine video duration.",
            )
        )

    return VideoMetadata(
        video_id=video_id,
        title=info.get("title", ""),
        duration_seconds=duration,
        uploader=info.get("uploader", ""),
        is_live=is_live,
        was_live=bool(info.get("was_live")),
        availability="public" if availability in ("public", "") else "unlisted",
        age_limit=age_limit,
        categories=info.get("categories", []),
    )
