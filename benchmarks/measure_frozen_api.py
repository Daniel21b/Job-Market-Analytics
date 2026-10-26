"""Measure warm-cache and forced-cache-miss HTTP requests on isolated local services."""

import argparse
import asyncio
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
from redis.asyncio import Redis

from skill_analytics.cache import build_cache_key
from skill_analytics.schemas import MetricsFilters


def summary(rows):
    timings = sorted(row["elapsed_ms"] for row in rows)
    return {
        "requests": len(rows),
        **{
            f"p{p}_ms": round(timings[math.ceil(len(timings) * p / 100) - 1], 3)
            for p in (50, 95, 99)
        },
        "max_ms": round(max(timings), 3),
        "cache_hits": sum(row["cache"] == "hit" for row in rows),
        "cache_misses": sum(row["cache"] == "miss" for row in rows),
        "minimum_result_count": min(row["result_count"] for row in rows),
        "timings_ms": [round(row["elapsed_ms"], 3) for row in rows],
    }


async def execute(args):
    redis = Redis.from_url(args.redis_url)
    results = []
    async with httpx.AsyncClient(timeout=60) as client:
        for params in ({}, {"skill": "python"}, {"skill": "sql", "location": "united states"}):
            filters = MetricsFilters(**params)
            key = build_cache_key("metrics:skill-demand", filters.model_dump(mode="json"))
            for mode, count in (("cold_cache", 100), ("warm_cache", 1000)):
                warmup = await client.get(args.base_url + "/v1/metrics/skill-demand", params=params)
                warmup.raise_for_status()
                if not warmup.json()["result_count"]:
                    raise ValueError("Empty query would create a misleading latency benchmark")
                rows = []
                for _ in range(count):
                    if mode == "cold_cache":
                        await redis.delete(key)
                    start = time.perf_counter()
                    response = await client.get(
                        args.base_url + "/v1/metrics/skill-demand", params=params
                    )
                    elapsed = (time.perf_counter() - start) * 1000
                    response.raise_for_status()
                    rows.append(
                        {
                            "elapsed_ms": elapsed,
                            "cache": response.headers.get("X-Cache"),
                            "result_count": response.json()["result_count"],
                        }
                    )
                results.append({"params": params, "mode": mode, **summary(rows)})
                print(
                    json.dumps({k: v for k, v in results[-1].items() if k != "timings_ms"}),
                    flush=True,
                )
    await redis.aclose()
    report = {
        "measured_at": datetime.now(UTC).isoformat(),
        "base_url": args.base_url,
        "method": (
            "Sequential HTTP requests, concurrency 1, persistent httpx connection; nearest-"
            "rank percentiles. Cold cache deletes only the exact query key before each "
            "request; PostgreSQL/OS caches are not reset. Warm cache primed once. Connection "
            "setup and deletion excluded from timings. No empty-result queries."
        ),
        "results": results,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--redis-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    asyncio.run(execute(parser.parse_args()))


if __name__ == "__main__":
    main()
