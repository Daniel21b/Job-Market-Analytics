import time
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from skill_analytics.cache import Cache, build_cache_key
from skill_analytics.config import Settings
from skill_analytics.models import ProcessingRun
from skill_analytics.repository import (
    create_processing_run,
    get_processing_run,
    query_skill_demand,
)
from skill_analytics.schemas import (
    MetricsFilters,
    ProcessingRunCreate,
    SkillDemandResponse,
)


class MetricsService:
    def __init__(self, session: AsyncSession, cache: Cache) -> None:
        self.session = session
        self.cache = cache

    async def skill_demand(self, filters: MetricsFilters) -> SkillDemandResponse:
        values = filters.model_dump(mode="json")
        cache_key = build_cache_key("metrics:skill-demand", values)
        started = time.perf_counter()

        cached = await self.cache.get_json(cache_key)
        if cached is not None:
            response = SkillDemandResponse.model_validate(cached)
            return response.model_copy(
                update={
                    "cache_status": "hit",
                    "query_duration_ms": round((time.perf_counter() - started) * 1_000, 3),
                }
            )

        items = await query_skill_demand(self.session, filters)
        duration_ms = round((time.perf_counter() - started) * 1_000, 3)
        response = SkillDemandResponse(
            filters={key: None if value is None else str(value) for key, value in values.items()},
            items=items,
            result_count=len(items),
            cache_status="miss",
            query_duration_ms=duration_ms,
        )
        await self.cache.set_json(cache_key, response.model_dump(mode="json"))
        return response


class RunService:
    def __init__(
        self,
        session: AsyncSession,
        redis: Redis,
        settings: Settings,
    ) -> None:
        self.session = session
        self.redis = redis
        self.settings = settings

    async def create(self, request: ProcessingRunCreate) -> ProcessingRun:
        run = await create_processing_run(
            self.session,
            input_uri=request.input_uri,
            output_uri=request.output_uri,
            optimized=request.optimized,
        )
        message = {
            "run_id": str(run.id),
            "input_uri": run.input_uri,
            "output_uri": run.output_uri,
            "optimized": run.optimized,
            "partitions": self.settings.spark_partitions,
        }
        import json

        await self.redis.lpush(self.settings.queue_name, json.dumps(message))
        return run

    async def get(self, run_id: UUID) -> ProcessingRun | None:
        return await get_processing_run(self.session, run_id)
