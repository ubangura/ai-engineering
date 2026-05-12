import asyncio
from typing import Any, cast

from models.domain import ErrorResponse, TranscriptSegment
from youtube_transcript_api import (
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

from app.clients import deepgram as dg_client
from app.config import settings
from app.transcript.gate import GateRejection

_MIN_DEEPGRAM_CONFIDENCE = 0.5


class TranscriptResult:
    def __init__(
        self,
        segments: list[TranscriptSegment],
        vtt_text: str,
        source: str,
        mean_confidence: float | None = None,
    ):
        self.segments = segments
        self.vtt_text = vtt_text
        self.source = source
        self.mean_confidence = mean_confidence


async def fetch_transcript(video_id: str, video_url: str) -> TranscriptResult:
    """
    Try YouTube auto-captions first; fall back to Deepgram.
    Raises `GateRejection` for audio-too-poor or empty content.
    """
    result = await _try_youtube(video_id)
    if result and result.segments:
        return result

    result = await _try_deepgram(video_url)
    if not result.segments:
        raise GateRejection(
            ErrorResponse(
                code="audio_too_poor",
                detail="No spoken content could be transcribed from this video.",
            )
        )
    return result


async def _try_youtube(video_id: str) -> TranscriptResult | None:
    loop = asyncio.get_running_loop()
    try:
        raw = await loop.run_in_executor(None, _fetch_youtube_transcript, video_id)
        if not raw:
            return None

        segments = [
            TranscriptSegment(
                start=float(entry["start"]),
                end=float(entry["start"] + entry["duration"]),
                text=str(entry["text"]),
            )
            for entry in cast(list[dict], raw)
        ]
        vtt = _segments_to_vtt(segments)
        return TranscriptResult(segments=segments, vtt_text=vtt, source="youtube")
    except (NoTranscriptFound, TranscriptsDisabled, IpBlocked, RequestBlocked):
        return None


def _make_youtube_api() -> YouTubeTranscriptApi:
    if not settings.youtube_cookies_path:
        return YouTubeTranscriptApi()
    import http.cookiejar

    import requests

    session = requests.Session()
    jar = http.cookiejar.MozillaCookieJar(settings.youtube_cookies_path)
    jar.load(ignore_discard=True, ignore_expires=True)
    session.cookies = jar  # type: ignore[assignment]
    return YouTubeTranscriptApi(http_client=session)


def _fetch_youtube_transcript(video_id: str) -> list[dict]:
    api = _make_youtube_api()
    transcript_list = api.list(video_id)
    try:
        transcript = transcript_list.find_transcript(["en"])
    except Exception:
        try:
            transcript = next(iter(transcript_list)).translate("en")
        except Exception as exc:
            raise NoTranscriptFound(video_id, ["en"], transcript_list) from exc

    raw_data = transcript.fetch()
    return [
        {
            "start": entry.start,
            "duration": entry.duration,
            "text": entry.text,
        }
        for entry in raw_data
    ]


async def _try_deepgram(video_url: str) -> TranscriptResult:
    audio_url = await _youtube_to_audio_url(video_url)
    response = await dg_client.transcribe(audio_url)
    confidence = dg_client.mean_confidence(response)

    # If confidence is None (no words), it's effectively 0.0
    val = confidence if confidence is not None else 0.0
    if val < _MIN_DEEPGRAM_CONFIDENCE:
        raise GateRejection(
            ErrorResponse(
                code="audio_too_poor",
                detail="Audio quality was too low to transcribe reliably.",
            )
        )

    segments = dg_client.to_segments(response)
    vtt = _segments_to_vtt(segments)
    return TranscriptResult(
        segments=segments,
        vtt_text=vtt,
        source="deepgram",
        mean_confidence=confidence,
    )


async def _youtube_to_audio_url(video_url: str) -> str:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _extract_audio_url_sync, video_url)
    return cast(str, result)


def _extract_audio_url_sync(video_url: str) -> str:
    import yt_dlp
    from yt_dlp.utils import DownloadError

    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "format": "bestaudio/best",
        "skip_download": True,
        "noplaylist": True,
        "js_runtimes": {"node": {"path": settings.yt_dlp_node_path}},
        "remote_components": ["ejs:github"],
        **({"cookiefile": settings.youtube_cookies_path} if settings.youtube_cookies_path else {}),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
            info = ydl.extract_info(video_url, download=False)
            audio_url = (info or {}).get("url")
            if not audio_url:
                raise GateRejection(
                    ErrorResponse(
                        code="internal_error",
                        detail="Couldn't process this video's audio. Please try again or use a different video.",
                    )
                )
            return cast(str, audio_url)
    except DownloadError:
        raise GateRejection(
            ErrorResponse(
                code="internal_error",
                detail="Couldn't reach YouTube to extract audio. Please try again in a moment.",
            )
        )


def _segments_to_vtt(segments: list[TranscriptSegment]) -> str:
    lines = ["WEBVTT", ""]
    for segment in segments:
        lines.append(
            f"{_seconds_to_vtt_time(segment.start)} --> {_seconds_to_vtt_time(segment.end)}"
        )
        lines.append(segment.text)
        lines.append("")
    return "\n".join(lines)


def _seconds_to_vtt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = min(seconds % 60, 59.999)
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:06.3f}"
