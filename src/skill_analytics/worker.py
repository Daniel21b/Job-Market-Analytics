import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import update

from skill_analytics.aws.emr_serverless import EmrServerlessRunner
from skill_analytics.cache import Cache
from skill_analytics.config import get_settings
from skill_analytics.database import Database
from skill_analytics.models import ProcessingRun, RunStatus
from skill_analytics.publisher import publish_local_output


def _error_message(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"[:8_000]


async def _mark_run(
    database: Database,
    run_id: UUID,
    *,
    status: RunStatus,
    values: dict[str, object] | None = None,
) -> None:
    payload: dict[str, object] = {"status": status.value}
    payload.update(values or {})
    async with database.sessions() as session:
        await session.execute(
            update(ProcessingRun).where(ProcessingRun.id == run_id).values(**payload)
        )
        await session.commit()


async def _execute_message(
    database: Database, redis: Redis, message: dict[str, object]
) -> None:
    settings = get_settings()
    run_id = UUID(str(message["run_id"]))
    await _mark_run(
        database,
        run_id,
        status=RunStatus.RUNNING,
        values={"started_at": datetime.now(UTC)},
    )
    if settings.execution_backend == "emr-serverless":
        try:
            metrics = await EmrServerlessRunner(settings).submit_and_wait(message)
        except Exception as exc:
            await _mark_run(
                database,
                run_id,
                status=RunStatus.FAILED,
                values={"completed_at": datetime.now(UTC), "error": _error_message(exc)},
            )
            return
        await _mark_run(
            database,
            run_id,
            status=RunStatus.SUCCEEDED,
            values={
                "completed_at": datetime.now(UTC),
                "metrics": metrics,
                "error": None,
            },
        )
        return

    command = [
        sys.executable,
        "-m",
        "skill_analytics.spark.job",
        "--input-uri",
        str(message["input_uri"]),
        "--output-uri",
        str(message["output_uri"]),
        "--taxonomy-path",
        settings.skill_taxonomy_path,
        "--master",
        settings.spark_master_url,
        "--partitions",
        str(message.get("partitions", settings.spark_partitions)),
        "--minimum-canonical-skills",
        str(settings.minimum_canonical_skills),
        "--optimized" if bool(message.get("optimized", True)) else "--no-optimized",
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        await _mark_run(
            database,
            run_id,
            status=RunStatus.FAILED,
            values={
                "completed_at": datetime.now(UTC),
                "error": stderr.decode("utf-8", errors="replace")[-8_000:],
            },
        )
        return

    metrics_path = Path(str(message["output_uri"])) / "pipeline_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    publish_metrics = await publish_local_output(
        database,
        Cache(redis, settings.cache_ttl_seconds),
        str(message["output_uri"]),
    )
    metrics.update(publish_metrics)
    await _mark_run(
        database,
        run_id,
        status=RunStatus.SUCCEEDED,
        values={
            "completed_at": datetime.now(UTC),
            "input_rows": metrics["input_rows"],
            "output_rows": metrics["output_rows"],
            "duplicate_rows": metrics["duplicate_rows"],
            "skill_count": metrics["canonical_skill_count"],
            "duration_ms": metrics["duration_ms"],
            "metrics": metrics,
            "error": None,
        },
    )
    print(stdout.decode("utf-8", errors="replace"))


async def worker() -> None:
    settings = get_settings()
    database = Database(settings)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        while True:
            item = await redis.brpop(settings.queue_name, timeout=5)
            if item is None:
                continue
            _, raw_message = item
            try:
                await _execute_message(database, redis, json.loads(raw_message))
            except Exception as exc:
                message = json.loads(raw_message)
                await _mark_run(
                    database,
                    UUID(str(message["run_id"])),
                    status=RunStatus.FAILED,
                    values={
                        "completed_at": datetime.now(UTC),
                        "error": _error_message(exc),
                    },
                )
    finally:
        await redis.aclose()
        await database.dispose()


def run() -> None:
    asyncio.run(worker())


if __name__ == "__main__":
    run()
