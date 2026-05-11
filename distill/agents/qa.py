import functools
import logging
import os
import re
import time
from collections.abc import AsyncGenerator

import anthropic
from app.clients.anthropic import get_anthropic_client
from app.sse import sse_event
from models.domain import Citation, QAResponse
from tools.web_search import WEB_SEARCH_TOOL

_MODEL = "claude-haiku-4-5-20251001"

logger = logging.getLogger(__name__)

_INLINE_TIMESTAMP_RE = re.compile(r"\[(\d{1,2}):(\d{2})\]")
_VTT_TIMESTAMP_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})\.\d{3} --> (\d{2}):(\d{2}):(\d{2})\.\d{3}"
)


@functools.lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", "system", "qa.md")
    with open(path) as f:
        return f.read()


async def run_qa(
    transcript: str,
    history: list[dict],
    question: str,
    video_id: str,
    session_id: str,
    response_language: str | None = None,
) -> AsyncGenerator[str, None]:
    client = get_anthropic_client()
    language_note = (
        f"\n\nRespond in language: {response_language}" if response_language else ""
    )
    messages = _build_messages(transcript, history, question, language_note)

    answer_parts: list[str] = []
    used_web_search = False
    start = time.monotonic()

    async with client.messages.stream(
        model=_MODEL,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": _load_system_prompt(),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=messages,
        tools=[WEB_SEARCH_TOOL],  # type: ignore[arg-type]
    ) as stream:
        async for event in stream:
            if hasattr(event, "type"):
                if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                    chunk = event.delta.text
                    answer_parts.append(chunk)
                    yield sse_event("delta", {"text": chunk})
                elif event.type == "content_block_start":
                    if (
                        hasattr(event.content_block, "type")
                        and event.content_block.type == "tool_use"
                        and event.content_block.name == "web_search"
                    ):
                        used_web_search = True
                        yield sse_event(
                            "tool-use", {"tool": "web_search", "query": ""}
                        )

        final_message = await stream.get_final_message()

    logger.info(
        "anthropic_call",
        extra={
            "agent": "qa",
            "video_id": video_id,
            "session_id": session_id,
            "model": _MODEL,
            "latency_ms": round((time.monotonic() - start) * 1000),
            "input_tokens": final_message.usage.input_tokens,
            "output_tokens": final_message.usage.output_tokens,
        },
    )

    answer_text = "".join(answer_parts)
    citations = _extract_citations_from_text(answer_text, transcript)

    for citation in citations:
        yield sse_event("citation", citation.model_dump())

    yield sse_event(
        "done",
        QAResponse(
            answer=answer_text,
            citations=citations,
            used_web_search=used_web_search,
            web_sources=[],
        ).model_dump(),
    )


def _build_messages(
    transcript: str,
    history: list[dict],
    question: str,
    language_note: str,
) -> list[anthropic.types.MessageParam]:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": transcript, "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": "The above is the lecture transcript. Answer questions using it."},
            ],
        },
        {
            "role": "assistant",
            "content": "Understood. I will answer questions using this lecture transcript, citing timestamps.",
        },
    ]

    for turn in history:
        messages.append({"role": turn["role"], "content": turn["content"]})

    messages.append({"role": "user", "content": question + language_note})
    return messages


def _extract_citations_from_text(text: str, transcript: str) -> list[Citation]:
    seen: set[int] = set()
    citations = []
    for match in _INLINE_TIMESTAMP_RE.finditer(text):
        start_seconds = int(match.group(1)) * 60 + int(match.group(2))
        if start_seconds in seen:
            continue
        seen.add(start_seconds)
        citations.append(Citation(
            section_id="",
            start_ts=float(start_seconds),
            end_ts=float(start_seconds + 10),
            quote=_find_quote_near(transcript, float(start_seconds)),
        ))
    return citations


def _find_quote_near(transcript: str, target_ts: float) -> str:
    best_text = ""
    best_diff = float("inf")
    lines = transcript.splitlines()
    for i, line in enumerate(lines):
        m = _VTT_TIMESTAMP_RE.match(line)
        if not m:
            continue
        ts = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
        diff = abs(ts - target_ts)
        if diff < best_diff and i + 1 < len(lines):
            best_diff = diff
            best_text = " ".join(lines[i + 1].split()[:25])
    return best_text
