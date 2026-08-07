import argparse
import asyncio
import json
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx


async def execute(url: str, request_count: int) -> dict[str, object]:
    timings: list[float] = []
    cache_headers: list[str] = []
    async with httpx.AsyncClient(timeout=10) as client:
        await client.get(url)
        for _ in range(request_count):
            started = time.perf_counter()
            response = await client.get(url)
            response.raise_for_status()
            timings.append((time.perf_counter() - started) * 1_000)
            cache_headers.append(response.headers.get("X-Cache", "missing"))
    ordered = sorted(timings)
    p95_index = min(len(ordered) - 1, int(len(ordered) * 0.95))
    return {
        "measured_at": datetime.now(UTC).isoformat(),
        "url": url,
        "request_count": request_count,
        "p50_ms": round(statistics.median(ordered), 3),
        "p95_ms": round(ordered[p95_index], 3),
        "max_ms": round(max(ordered), 3),
        "cache_hit_count": cache_headers.count("hit"),
        "target_sub_50ms_met": ordered[p95_index] < 50,
        "timings_ms": [round(value, 3) for value in timings],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000/v1/metrics/skill-demand")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--output", default="evidence/api_benchmark.json")
    args = parser.parse_args()
    result = asyncio.run(execute(args.url, args.requests))
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
