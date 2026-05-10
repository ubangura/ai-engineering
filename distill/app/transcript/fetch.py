import asyncio

from models.domain import ErrorResponse, TranscriptSegment
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

from app.clients import deepgram as dg_client
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
    Raises `GateRejection` for audio-too-poor.
    """
    result = await _try_youtube(video_id)
    if result:
        return result

    return await _try_deepgram(video_url)


async def _try_youtube(video_id: str) -> TranscriptResult | None:
    loop = asyncio.get_running_loop()
    try:
        raw = await loop.run_in_executor(None, _fetch_youtube_transcript, video_id)
        segments = [
            TranscriptSegment(
                start=entry["start"],
                end=entry["start"] + entry["duration"],
                text=entry["text"],
            )
            for entry in raw
        ]
        vtt = _segments_to_vtt(segments)
        return TranscriptResult(segments=segments, vtt_text=vtt, source="youtube")
    except (NoTranscriptFound, TranscriptsDisabled):
        return None


def _fetch_youtube_transcript(video_id: str) -> list[dict]:
    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id)
    return [
        {"start": entry.start, "duration": entry.duration, "text": entry.text}
        for entry in transcript
    ]


async def _try_deepgram(video_url: str) -> TranscriptResult:
    audio_url = _youtube_to_audio_url(video_url)
    response = await dg_client.transcribe(audio_url)
    confidence = dg_client.mean_confidence(response)
    if confidence and confidence < _MIN_DEEPGRAM_CONFIDENCE:
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


def _youtube_to_audio_url(video_url: str) -> str:
    import yt_dlp

    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "skip_download": True,
        "noplaylist": True,
    }
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
        return audio_url


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
    remaining_seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:06.3f}"
