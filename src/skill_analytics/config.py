from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://skill_analytics:skill_analytics@localhost:5432/skill_analytics"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = Field(default=300, ge=1, le=86_400)
    queue_name: str = "skill-analytics:runs"
    auto_create_schema: bool = False

    spark_master_url: str = "local[*]"
    spark_input_uri: str = "/data/input"
    spark_output_uri: str = "/data/output"
    spark_partitions: int = Field(default=8, ge=1, le=10_000)
    skill_taxonomy_path: str = "config/skill_taxonomy.csv"
    minimum_canonical_skills: int = Field(default=1, ge=1)
    execution_backend: str = "local"

    aws_region: str = "us-east-1"
    aws_s3_input_bucket: str | None = None
    aws_s3_output_bucket: str | None = None
    aws_emr_serverless_application_id: str | None = None
    aws_emr_serverless_execution_role_arn: str | None = None
    aws_emr_serverless_entrypoint_uri: str | None = None
    aws_emr_serverless_log_uri: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
