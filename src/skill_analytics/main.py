from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from redis.asyncio import Redis

from skill_analytics import __version__
from skill_analytics.api.routes import health, metrics, runs
from skill_analytics.cache import Cache
from skill_analytics.config import get_settings
from skill_analytics.database import Database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    database = Database(settings)
    redis = Redis.from_url(settings.redis_url, decode_responses=False)

    app.state.settings = settings
    app.state.database = database
    app.state.redis = redis
    app.state.cache = Cache(redis, settings.cache_ttl_seconds)

    if settings.auto_create_schema:
        from skill_analytics import models  # noqa: F401

        await database.create_schema()

    yield

    await redis.aclose()
    await database.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Distributed Skill Analytics API",
        version=__version__,
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(runs.router)
    return app


app = create_app()


def run() -> None:
    uvicorn.run("skill_analytics.main:app", host="0.0.0.0", port=8000, reload=False)
