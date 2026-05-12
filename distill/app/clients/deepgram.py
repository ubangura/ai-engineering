import httpx
from app.config import settings
from models.domain import TranscriptSegment

_DEEPGRAM_BASE = "https://api.deepgram.com"


async def transcribe(audio_url: str, language: str | None = None) -> dict:
    params = {
        "model": "nova-3",
        "smart_format": "true",
        "utterances": "true",
        "punctuate": "true",
        "diarize": "false",
    }
    if language:
        params["language"] = language
    else:
        params["detect_language"] = "true"

    headers = {"Authorization": f"Token {settings.deepgram_api_key.get_secret_value()}"}
    async with httpx.AsyncClient(base_url=_DEEPGRAM_BASE, headers=headers) as client:
        response = await client.post(
            "/v1/listen",
            params=params,
            json={"url": audio_url},
            timeout=900.0,
        )
        response.raise_for_status()
        return response.json()


def mean_confidence(response: dict) -> float | None:
    try:
        words = response["results"]["channels"][0]["alternatives"][0]["words"]
        if not words:
            return None
        return sum(word["confidence"] for word in words) / len(words)
    except (KeyError, IndexError):
        return None


def to_segments(response: dict) -> list[TranscriptSegment]:
    try:
        utterances = response["results"]["utterances"]
    except (KeyError, TypeError):
        return []
    return [
        TranscriptSegment(
            start=utterance["start"],
            end=utterance["end"],
            text=utterance["transcript"],
        )
        for utterance in utterances
    ]
