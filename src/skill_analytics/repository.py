from datetime import UTC, datetime, time
from uuid import UUID

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from skill_analytics.models import JobPosting, JobPostingSkill, ProcessingRun, Skill
from skill_analytics.schemas import MetricsFilters, SkillDemandItem


async def create_processing_run(
    session: AsyncSession,
    *,
    input_uri: str,
    output_uri: str,
    optimized: bool,
) -> ProcessingRun:
    run = ProcessingRun(input_uri=input_uri, output_uri=output_uri, optimized=optimized)
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def get_processing_run(session: AsyncSession, run_id: UUID) -> ProcessingRun | None:
    return await session.get(ProcessingRun, run_id)


def _skill_demand_statement(filters: MetricsFilters) -> Select[tuple[object, ...]]:
    statement = (
        select(
            Skill.slug,
            Skill.canonical_name,
            JobPosting.role_family,
            JobPosting.location_normalized,
            func.count(JobPosting.id.distinct()).label("posting_count"),
        )
        .join(JobPostingSkill, JobPostingSkill.skill_id == Skill.id)
        .join(JobPosting, JobPosting.id == JobPostingSkill.posting_id)
    )

    clauses = []
    if filters.skill:
        clauses.append(Skill.slug == filters.skill.lower())
    if filters.role_family:
        clauses.append(JobPosting.role_family == filters.role_family)
    if filters.location:
        clauses.append(JobPosting.location_normalized == filters.location.lower())
    if filters.start_date:
        clauses.append(
            JobPosting.posted_at
            >= datetime.combine(filters.start_date, time.min, tzinfo=UTC)
        )
    if filters.end_date:
        clauses.append(
            JobPosting.posted_at
            <= datetime.combine(filters.end_date, time.max, tzinfo=UTC)
        )
    if clauses:
        statement = statement.where(and_(*clauses))

    return (
        statement.group_by(
            Skill.slug,
            Skill.canonical_name,
            JobPosting.role_family,
            JobPosting.location_normalized,
        )
        .order_by(func.count(JobPosting.id.distinct()).desc(), Skill.slug)
        .limit(500)
    )


async def query_skill_demand(
    session: AsyncSession, filters: MetricsFilters
) -> list[SkillDemandItem]:
    rows = (await session.execute(_skill_demand_statement(filters))).all()
    return [
        SkillDemandItem(
            skill=str(row.slug),
            canonical_name=str(row.canonical_name),
            role_family=str(row.role_family),
            location=str(row.location_normalized),
            posting_count=int(row.posting_count),
        )
        for row in rows
    ]
