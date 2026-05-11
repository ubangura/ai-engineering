import logging
import time

from app.clients.anthropic import get_anthropic_client

logger = logging.getLogger(__name__)

_client = get_anthropic_client()


async def complete(
    model: str,
    max_tokens: int,
    system_prompt: str,
    transcript: str,
    instruction: str,
    agent: str,
    video_id: str,
    temperature: float | None = None,
) -> str:
    start = time.monotonic()

    params: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "system": [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": transcript,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {"type": "text", "text": instruction},
                ],
            }
        ],
    }
    if temperature is not None:
        params["temperature"] = temperature

    response = await _client.messages.create(**params)

    logger.info(
        "anthropic_call",
        extra={
            "agent": agent,
            "video_id": video_id,
            "model": model,
            "latency_ms": round((time.monotonic() - start) * 1000),
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    )

    text_block = next(
        (block for block in response.content if block.type == "text"), None
    )
    if text_block is None:
        raise RuntimeError(f"{agent} agent returned no text block")

    return _strip_fence(text_block.text.strip())


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
