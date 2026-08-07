from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from skill_analytics.api.dependencies import get_redis, get_session
from skill_analytics.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> HealthResponse:
    database_status = "ok"
    redis_status = "ok"
    overall = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"
        overall = "degraded"
    try:
        await redis.ping()
    except Exception:
        redis_status = "unavailable"
        overall = "degraded"
    return HealthResponse(status=overall, database=database_status, redis=redis_status)
