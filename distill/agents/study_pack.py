import functools
import json
import os

from app.clients.anthropic import get_anthropic_client
from models.domain import Outline, StudyPack

from agents.messaging import complete

_MODEL = "claude-sonnet-4-6"
_MAX_ATTEMPTS = 3


@functools.lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "system", "study_pack.md"
    )
    with open(path) as f:
        return f.read()


@functools.lru_cache(maxsize=None)
def _load_category_prompt(category: str) -> str:
    path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "category", f"{category}.md"
    )
    with open(path) as f:
        return f.read()


def _clamp_temperature(raw: float) -> float:
    return min(max(raw, 0.0), 0.7)


async def run_study_pack(
    transcript: str, outline: Outline, video_id: str, _job_id: str = ""
) -> StudyPack:
    client = get_anthropic_client()
    system_text = (
        _load_system_prompt()
        + "\n\n"
        + _load_category_prompt(outline.inferred_category)
    )
    temperature = _clamp_temperature(outline.recommended_temperature)
    instruction = (
        f"Outline JSON:\n{outline.model_dump_json()}\n\nProduce a complete StudyPack."
    )

    for attempt in range(_MAX_ATTEMPTS):
        raw = await complete(
            client,
            _MODEL,
            16000,
            system_text,
            transcript,
            instruction,
            agent="study_pack",
            video_id=video_id,
            temperature=temperature,
        )
        try:
            return StudyPack.model_validate(json.loads(raw))
        except Exception as exc:
            if attempt == _MAX_ATTEMPTS - 1:
                raise RuntimeError(
                    f"Study Pack agent failed after {_MAX_ATTEMPTS} attempts"
                ) from exc

    raise RuntimeError("Unreachable")
