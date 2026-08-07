from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from skill_analytics.api.dependencies import get_cache, get_session
from skill_analytics.cache import Cache
from skill_analytics.schemas import MetricsFilters, SkillDemandResponse
from skill_analytics.services import MetricsService

router = APIRouter(prefix="/v1/metrics", tags=["metrics"])


@router.get("/skill-demand", response_model=SkillDemandResponse)
async def skill_demand(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    cache: Annotated[Cache, Depends(get_cache)],
    skill: str | None = Query(default=None, min_length=1, max_length=128),
    role_family: str | None = Query(default=None, min_length=1, max_length=96),
    location: str | None = Query(default=None, min_length=1, max_length=256),
    start_date: date | None = None,
    end_date: date | None = None,
) -> SkillDemandResponse:
    filters = MetricsFilters(
        skill=skill,
        role_family=role_family,
        location=location,
        start_date=start_date,
        end_date=end_date,
    )
    result = await MetricsService(session, cache).skill_demand(filters)
    response.headers["X-Cache"] = result.cache_status
    response.headers["Server-Timing"] = f"app;dur={result.query_duration_ms:.3f}"
    return result
