from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from skill_analytics.api.dependencies import (
    get_redis,
    get_session,
    get_settings_from_app,
)
from skill_analytics.config import Settings
from skill_analytics.schemas import ProcessingRunCreate, ProcessingRunResponse
from skill_analytics.services import RunService

router = APIRouter(prefix="/v1/runs", tags=["processing-runs"])


@router.post("", response_model=ProcessingRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_run(
    request: ProcessingRunCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings_from_app)],
) -> ProcessingRunResponse:
    run = await RunService(session, redis, settings).create(request)
    return ProcessingRunResponse.model_validate(run)


@router.get("/{run_id}", response_model=ProcessingRunResponse)
async def get_run(
    run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings_from_app)],
) -> ProcessingRunResponse:
    run = await RunService(session, redis, settings).get(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    return ProcessingRunResponse.model_validate(run)
