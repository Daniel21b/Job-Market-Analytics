from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str


class ProcessingRunCreate(BaseModel):
    input_uri: str = Field(min_length=1, max_length=2_048)
    output_uri: str = Field(min_length=1, max_length=2_048)
    optimized: bool = True


class ProcessingRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    input_uri: str
    output_uri: str
    optimized: bool
    requested_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    input_rows: int | None = None
    output_rows: int | None = None
    duplicate_rows: int | None = None
    skill_count: int | None = None
    duration_ms: int | None = None
    metrics: dict[str, object] = Field(default_factory=dict)
    error: str | None = None


class SkillDemandItem(BaseModel):
    skill: str
    canonical_name: str
    role_family: str
    location: str
    posting_count: int


class SkillDemandResponse(BaseModel):
    filters: dict[str, str | None]
    items: list[SkillDemandItem]
    result_count: int
    cache_status: str
    query_duration_ms: float


class MetricsFilters(BaseModel):
    skill: str | None = None
    role_family: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
