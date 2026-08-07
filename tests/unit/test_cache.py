import fakeredis.aioredis
import pytest

from skill_analytics.cache import Cache, build_cache_key


def test_cache_key_is_order_independent() -> None:
    first = build_cache_key("metrics", {"location": "nyc", "role": "data"})
    second = build_cache_key("metrics", {"role": "data", "location": "nyc"})
    assert first == second


@pytest.mark.asyncio
async def test_cache_round_trip_and_invalidation() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    cache = Cache(redis, ttl_seconds=60)
    key = build_cache_key("metrics:skill-demand", {"skill": "python"})
    await cache.set_json(key, {"items": ["python"]})
    assert await cache.get_json(key) == {"items": ["python"]}
    assert await cache.invalidate_metrics() == 1
    assert await cache.get_json(key) is None
    await redis.aclose()
