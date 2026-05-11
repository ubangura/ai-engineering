import asyncio
import os
import sys

import httpx

BASE_URL = os.environ["BASE_URL"]

# (expected_code, url)
CASES = [
    (
        "livestream",
        "https://www.youtube.com/watch?v=jfKfPfyJRdk",
    ),  # lofi hip hop radio — active stream
    ("private", "https://www.youtube.com/watch?v=aQkQaQbODJE"),  # known private video
    # ("age_restricted", "https://www.youtube.com/watch?v=bbFDsGRBJVM"),  # age-restricted
    (
        "music_category",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ),  # Rick Astley — Music category
    ("private", "https://www.youtube.com/watch?v=xxxxxxxxxxx"),  # deleted/nonexistent
]


async def check_rejection(
    client: httpx.AsyncClient, expected_code: str, url: str
) -> None:
    response = await client.post("/api/video", json={"url": url})
    assert response.status_code in (422, 404, 400), (
        f"expected 4xx, got {response.status_code}: {response.text}"
    )
    code = response.json()["detail"]["code"]
    assert code == expected_code, f"expected {expected_code!r}, got {code!r}"


async def main() -> None:
    failed = 0
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
        for expected_code, url in CASES:
            print(f"checking rejection [{expected_code}] {url}")
            try:
                await check_rejection(client, expected_code, url)
                print("  PASS")
            except Exception as exc:
                print(f"  FAIL: {exc}")
                failed += 1

    sys.exit(failed)


asyncio.run(main())
