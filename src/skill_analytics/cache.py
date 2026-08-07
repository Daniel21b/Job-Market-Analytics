import hashlib
import json
from collections.abc import Mapping

from redis.asyncio import Redis


def build_cache_key(namespace: str, values: Mapping[str, object]) -> str:
    canonical = json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"skill-analytics:{namespace}:{digest}"


class Cache:
    def __init__(self, redis: Redis, ttl_seconds: int) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    async def get_json(self, key: str) -> dict[str, object] | None:
        value = await self.redis.get(key)
        if value is None:
            return None
        decoded = value.decode("utf-8") if isinstance(value, bytes) else value
        result = json.loads(decoded)
        if not isinstance(result, dict):
            return None
        return result

    async def set_json(self, key: str, value: Mapping[str, object]) -> None:
        await self.redis.set(key, json.dumps(value, default=str), ex=self.ttl_seconds)

    async def invalidate_metrics(self) -> int:
        deleted = 0
        async for key in self.redis.scan_iter(match="skill-analytics:metrics:*"):
            deleted += await self.redis.delete(key)
        return deleted
