import asyncio
import json
import os
import sys

import httpx

BASE_URL = os.environ["BASE_URL"]

URLS = [
    "https://www.youtube.com/watch?v=hiiEeMN7vbQ",  # Developing a Growth Mindset — ~10min, captions
    # "https://www.youtube.com/watch?v=bZzyPscbtI8",  # AI Agents in Python — ~47min, captions
    # "https://www.youtube.com/watch?v=g5uGLV01slc",  # C-SPAN history lecture — ~78min, captions
    # TODO: lecture not in English language
    # TODO: lecture without auto-captions (Deepgram fallback)
    # TODO: lecture with low-audio but recoverable
]


async def check_url(client: httpx.AsyncClient, url: str) -> None:
    response = await client.post("/api/video", json={"url": url})

    if response.status_code == 200:
        data = response.json()
        assert "video_id" in data, "missing video_id"
        assert "study_pack" in data, "missing study_pack"
        pack = data["study_pack"]
        assert len(pack["summaries"]) == 3, (
            f"expected 3 summaries, got {len(pack['summaries'])}"
        )
        assert len(pack["flashcards"]) >= 8, (
            f"expected ≥8 flashcards, got {len(pack['flashcards'])}"
        )
        print(f"  CACHE HIT — {len(pack['flashcards'])} flashcards")
        return

    assert response.status_code == 202, (
        f"unexpected status {response.status_code}: {response.text}"
    )
    job_id = response.json()["job_id"]
    print(f"  queued job {job_id}, consuming SSE...")

    async with client.stream("GET", f"/sse/video/{job_id}") as stream:
        event_name = ""
        async for line in stream.aiter_lines():
            if line.startswith("event: "):
                event_name = line[7:].strip()
            elif line.startswith("data: "):
                data = json.loads(line[6:])
                if event_name == "error":
                    raise AssertionError(f"pipeline error: {data}")
                if event_name == "study-pack-done":
                    pack = data["study_pack"]
                    assert len(pack["summaries"]) == 3, (
                        f"expected 3 summaries, got {len(pack['summaries'])}"
                    )
                    assert len(pack["flashcards"]) >= 8, (
                        f"expected ≥8 flashcards, got {len(pack['flashcards'])}"
                    )
                    print(f"  study-pack-done — {len(pack['flashcards'])} flashcards")
                if event_name == "done":
                    break


async def main() -> None:
    failed = 0
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=300) as client:
        for url in URLS:
            print(f"checking {url}")
            try:
                await check_url(client, url)
                print("  PASS")
            except Exception as exc:
                print(f"  FAIL: {exc}")
                failed += 1

    sys.exit(failed)


asyncio.run(main())
