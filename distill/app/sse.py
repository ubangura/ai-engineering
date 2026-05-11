import asyncio
import json
from collections.abc import AsyncGenerator


def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def sse_keepalive() -> str:
    return ": ping\n\n"


async def keepalive_stream(
    source: AsyncGenerator[str, None],
    interval_seconds: int = 15,
) -> AsyncGenerator[str, None]:
    """Wrap an SSE generator and inject a keepalive every `interval_seconds`."""
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def _produce() -> None:
        async for chunk in source:
            await queue.put(chunk)
        await queue.put(None)

    async def _tick() -> None:
        while True:
            await asyncio.sleep(interval_seconds)
            await queue.put(sse_keepalive())

    producer = asyncio.ensure_future(_produce())
    ticker = asyncio.ensure_future(_tick())
    try:
        while True:
            item = await queue.get()
            if item is None:
                return
            yield item
    finally:
        ticker.cancel()
        producer.cancel()
