import json
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from skill_analytics.cache import Cache
from skill_analytics.database import Database
from skill_analytics.models import JobPosting, JobPostingSkill, Skill


def _json_rows(directory: Path) -> Iterator[dict[str, object]]:
    for part in sorted(directory.glob("part-*.json")):
        with part.open(encoding="utf-8") as handle:
            for line in handle:
                value = json.loads(line)
                if isinstance(value, dict):
                    yield value


def _chunks(
    rows: Iterable[dict[str, object]], size: int = 500
) -> Iterator[list[dict[str, object]]]:
    chunk: list[dict[str, object]] = []
    for row in rows:
        chunk.append(row)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _parse_timestamp(value: object) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _posting_uuid(posting_key: object) -> UUID:
    return uuid5(NAMESPACE_URL, f"skill-analytics:{posting_key}")


async def publish_local_output(
    database: Database,
    cache: Cache,
    output_uri: str,
) -> dict[str, int]:
    root = Path(output_uri) / "publish"
    posting_rows = list(_json_rows(root / "job_postings"))
    skill_match_rows = list(_json_rows(root / "job_skill_matches"))

    async with database.sessions() as session:
        for chunk in _chunks(posting_rows):
            values = [
                {
                    "id": _posting_uuid(row["posting_key"]),
                    "source": str(row["source"])[:48],
                    "source_record_id": str(row["source_record_id"])[:256],
                    "company_normalized": str(row["company_normalized"])[:256],
                    "title_normalized": str(row["title_normalized"])[:256],
                    "location_normalized": str(row["location_normalized"])[:256],
                    "role_family": str(row["role_family"])[:96],
                    "description": str(row["description"]),
                    "content_hash": str(row["content_hash"]),
                    "composite_join_key": str(row["composite_join_key"]),
                    "is_remote": bool(row.get("is_remote", False)),
                    "posted_at": _parse_timestamp(row["posted_at"]),
                    "observed_at": _parse_timestamp(row["observed_at"]),
                }
                for row in chunk
            ]
            statement = insert(JobPosting).values(values)
            await session.execute(
                statement.on_conflict_do_update(
                    constraint="uq_job_posting_source_record",
                    set_={
                        "company_normalized": statement.excluded.company_normalized,
                        "title_normalized": statement.excluded.title_normalized,
                        "location_normalized": statement.excluded.location_normalized,
                        "role_family": statement.excluded.role_family,
                        "description": statement.excluded.description,
                        "content_hash": statement.excluded.content_hash,
                        "composite_join_key": statement.excluded.composite_join_key,
                        "is_remote": statement.excluded.is_remote,
                        "posted_at": statement.excluded.posted_at,
                        "observed_at": statement.excluded.observed_at,
                    },
                )
            )

        unique_skills = {
            str(row["canonical_skill"])[:128]: str(
                row.get("category", "uncategorized")
            )[:128]
            for row in skill_match_rows
        }
        if unique_skills:
            skill_values = [
                {
                    "slug": slug,
                    "canonical_name": slug,
                    "category": category,
                }
                for slug, category in sorted(unique_skills.items())
            ]
            skill_statement = insert(Skill).values(skill_values)
            await session.execute(
                skill_statement.on_conflict_do_update(
                    index_elements=[Skill.slug],
                    set_={
                        "canonical_name": skill_statement.excluded.canonical_name,
                        "category": skill_statement.excluded.category,
                    },
                )
            )

        skill_ids = dict((await session.execute(select(Skill.slug, Skill.id))).all())
        bridge_values = [
            {
                "posting_id": _posting_uuid(row["posting_key"]),
                "skill_id": skill_ids[str(row["canonical_skill"])[:128]],
                "matched_alias": str(row["matched_alias"])[:256],
            }
            for row in skill_match_rows
            if str(row["canonical_skill"])[:128] in skill_ids
        ]
        for chunk in _chunks(bridge_values):
            bridge_statement = insert(JobPostingSkill).values(chunk)
            await session.execute(
                bridge_statement.on_conflict_do_update(
                    index_elements=[JobPostingSkill.posting_id, JobPostingSkill.skill_id],
                    set_={"matched_alias": bridge_statement.excluded.matched_alias},
                )
            )
        await session.commit()

    invalidated = await cache.invalidate_metrics()
    return {
        "published_postings": len(posting_rows),
        "published_skill_matches": len(skill_match_rows),
        "cache_keys_invalidated": invalidated,
    }
