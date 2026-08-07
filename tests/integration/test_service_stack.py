import os

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from skill_analytics.config import get_settings
from skill_analytics.main import create_app

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_health_and_async_run_queue() -> None:
    os.environ["AUTO_CREATE_SCHEMA"] = "true"
    get_settings.cache_clear()
    app = create_app()
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            health = await client.get("/health")
            assert health.status_code == 200
            assert health.json() == {"status": "ok", "database": "ok", "redis": "ok"}

            created = await client.post(
                "/v1/runs",
                json={
                    "input_uri": "/data/input/jobs.json",
                    "output_uri": "/data/output/test-run",
                    "optimized": True,
                },
            )
            assert created.status_code == 202
            body = created.json()
            assert body["status"] == "queued"
            fetched = await client.get(f"/v1/runs/{body['id']}")
            assert fetched.status_code == 200
            assert fetched.json()["id"] == body["id"]
