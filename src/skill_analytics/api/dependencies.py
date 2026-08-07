from collections.abc import AsyncIterator
from typing import cast

from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from skill_analytics.cache import Cache
from skill_analytics.config import Settings
from skill_analytics.database import Database


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    database = cast(Database, request.app.state.database)
    async with database.sessions() as session:
        yield session


def get_redis(request: Request) -> Redis:
    return cast(Redis, request.app.state.redis)


def get_settings_from_app(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_cache(request: Request) -> Cache:
    return cast(Cache, request.app.state.cache)
