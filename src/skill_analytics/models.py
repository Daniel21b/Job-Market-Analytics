from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from skill_analytics.database import Base


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default=RunStatus.QUEUED)
    input_uri: Mapped[str] = mapped_column(Text, nullable=False)
    output_uri: Mapped[str] = mapped_column(Text, nullable=False)
    optimized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_rows: Mapped[int | None] = mapped_column(Integer)
    output_rows: Mapped[int | None] = mapped_column(Integer)
    duplicate_rows: Mapped[int | None] = mapped_column(Integer)
    skill_count: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    metrics: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_processing_runs_status_requested", "status", "requested_at"),)


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source: Mapped[str] = mapped_column(String(48), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(256), nullable=False)
    company_normalized: Mapped[str] = mapped_column(String(256), nullable=False)
    title_normalized: Mapped[str] = mapped_column(String(256), nullable=False)
    location_normalized: Mapped[str] = mapped_column(String(256), nullable=False)
    role_family: Mapped[str] = mapped_column(String(96), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    composite_join_key: Mapped[str] = mapped_column(String(64), nullable=False)
    is_remote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    skills: Mapped[list["JobPostingSkill"]] = relationship(
        back_populates="posting", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("source", "source_record_id", name="uq_job_posting_source_record"),
        Index("ix_job_postings_content_hash", "content_hash"),
        Index("ix_job_postings_composite_key_posted", "composite_join_key", "posted_at"),
        Index(
            "ix_job_postings_filters",
            "role_family",
            "location_normalized",
            "posted_at",
        ),
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    canonical_name: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)

    postings: Mapped[list["JobPostingSkill"]] = relationship(back_populates="skill")


class JobPostingSkill(Base):
    __tablename__ = "job_posting_skills"

    posting_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    matched_alias: Mapped[str] = mapped_column(String(256), nullable=False)

    posting: Mapped[JobPosting] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="postings")

    __table_args__ = (
        Index("ix_job_posting_skills_skill_posting", "skill_id", "posting_id"),
    )
