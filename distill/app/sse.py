import asyncio
import json
from collections.abc import AsyncGenerator


async def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def sse_keepalive() -> str:
    return ": ping\n\n"


async def keepalive_stream(
    source: AsyncGenerator[str, None],
    interval_seconds: int = 15,
) -> AsyncGenerator[str, None]:
    """
    Wraps an SSE generator and injects a keepalive comment every `interval_seconds`
    to prevent Railway's proxy from closing idle connections.
    """

    async def _ticker():
        while True:
            await asyncio.sleep(interval_seconds)
            yield await sse_keepalive()

    source_done = False
    ticker = _ticker()

    async def _merged():
        nonlocal source_done
        source_task = asyncio.ensure_future(_consume(source))
        ticker_task = asyncio.ensure_future(_consume(ticker))

        pending = {source_task, ticker_task}
        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                chunk = task.result()
                if task is source_task:
                    if chunk is None:
                        source_done = True
                        ticker_task.cancel()
                        return
                    yield chunk
                    source_task = asyncio.ensure_future(_consume(source))
                    pending.add(source_task)
                else:
                    if not source_done:
                        yield chunk
                    ticker_task = asyncio.ensure_future(_consume(ticker))
                    if not source_done:
                        pending.add(ticker_task)

    async for chunk in _merged():
        yield chunk


async def _consume(gen: AsyncGenerator) -> str | None:
    try:
        return await gen.__anext__()
    except StopAsyncIteration:
        return None
