import functools
import json
import os

from app.clients.anthropic import get_anthropic_client
from app.transcript.gate import GateRejection
from models.domain import ErrorResponse, Outline

from agents.messaging import complete

_MODEL = "claude-sonnet-4-6"
_MAX_ATTEMPTS = 3
_NON_LECTURE_THRESHOLD = 0.4


@functools.lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "system", "outline.md"
    )
    with open(path) as f:
        return f.read()


async def run_outline(transcript: str, video_id: str, _job_id: str = "") -> Outline:
    client = get_anthropic_client()
    instruction = "Produce a complete Outline for this transcript."

    for attempt in range(_MAX_ATTEMPTS):
        raw = await complete(
            client,
            _MODEL,
            1000,
            _load_system_prompt(),
            transcript,
            instruction,
            agent="outline",
            video_id=video_id,
        )
        try:
            outline = Outline.model_validate(json.loads(raw))
        except Exception as exc:
            if attempt == _MAX_ATTEMPTS - 1:
                raise RuntimeError(
                    f"Outline agent failed to produce valid JSON after {_MAX_ATTEMPTS} attempts"
                ) from exc
            continue

        if outline.is_lecture_confidence < _NON_LECTURE_THRESHOLD:
            raise GateRejection(
                ErrorResponse(
                    code="not_a_lecture",
                    detail="This doesn't appear to be lecture content. Try a recorded class, tutorial, or academic talk.",
                )
            )
        return outline

    raise RuntimeError("Unreachable")
