import functools
import json
import os

from app.transcript.gate import GateRejection
from models.domain import ErrorResponse, VideoAnalysis

from agents.messaging import complete

_MODEL = "claude-sonnet-4-6"
_MAX_ATTEMPTS = 3
_NON_LECTURE_THRESHOLD = 0.4
_AGENT_NAME = "outline"


@functools.lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "system", "outline.md"
    )
    with open(path) as f:
        return f.read()


async def run_outline(
    timestamped_transcript: str, video_id: str, _job_id: str = ""
) -> VideoAnalysis:
    instruction = "Produce a complete Outline for this transcript."
    last_exc: Exception | None = None

    for _ in range(_MAX_ATTEMPTS):
        raw = await complete(
            model=_MODEL,
            max_tokens=9000,
            system_prompt=_load_system_prompt(),
            transcript=timestamped_transcript,
            instruction=instruction,
            agent=_AGENT_NAME,
            video_id=video_id,
        )
        try:
            data = json.loads(raw)
            nodes_data = data.pop("outline", None) or data.pop("nodes", None)
            data["outline"] = {"video_id": video_id, "nodes": nodes_data}
            analysis = VideoAnalysis.model_validate(data)
        except Exception as exc:
            last_exc = exc
            continue

        if analysis.is_lecture_confidence < _NON_LECTURE_THRESHOLD:
            raise GateRejection(
                ErrorResponse(
                    code="not_a_lecture",
                    detail="This doesn't appear to be lecture content. Try a recorded class, tutorial, or academic talk.",
                )
            )
        return analysis

    raise GateRejection(
        ErrorResponse(
            code="internal_error",
            detail="Could not analyse this transcript. Try again later.",
        )
    ) from last_exc
