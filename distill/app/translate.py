import functools
import json
import logging
import os
import time

from models.domain import Flashcard, Summary
from models.responses.translate import TranslationResponse

from app.clients.anthropic import get_anthropic_client

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 16000

logger = logging.getLogger(__name__)
_client = get_anthropic_client()


@functools.lru_cache(maxsize=1)
def _load_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", "translate.md")
    with open(path) as f:
        return f.read()


def _strip_fence(text: str) -> str:
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    end = len(lines)
    for i in range(len(lines) - 1, 0, -1):
        if lines[i].strip() == "```":
            end = i
            break
    return "\n".join(lines[1:end])


async def translate_pack(
    summaries: list[Summary],
    flashcards: list[Flashcard],
    target_language: str,
    video_id: str,
) -> TranslationResponse:
    payload = json.dumps(
        {
            "summaries": [summary.model_dump() for summary in summaries],
            "flashcards": [file.model_dump() for file in flashcards],
        }
    )
    instruction = f"Target language: {target_language}\n\n{payload}"

    start = time.monotonic()
    response = await _client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": _load_prompt(),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": instruction}],
    )

    logger.info(
        "anthropic_call",
        extra={
            "transform": "translate",
            "video_id": video_id,
            "target_language": target_language,
            "model": _MODEL,
            "latency_ms": round((time.monotonic() - start) * 1000),
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_creation_input_tokens": response.usage.cache_creation_input_tokens,
            "cache_read_input_tokens": response.usage.cache_read_input_tokens,
        },
    )

    text = next(
        (block.text for block in response.content if block.type == "text"), None
    )
    if text is None:
        raise RuntimeError("translate transform returned no text block")

    data = json.loads(_strip_fence(text.strip()))
    return TranslationResponse(
        video_id=video_id,
        target_language=target_language,
        summaries=[Summary(**summary) for summary in data["summaries"]],
        flashcards=[Flashcard(**flashcard) for flashcard in data["flashcards"]],
    )
