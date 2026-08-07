CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS processing_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(24) NOT NULL DEFAULT 'queued',
    input_uri TEXT NOT NULL,
    output_uri TEXT NOT NULL,
    optimized BOOLEAN NOT NULL DEFAULT TRUE,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    input_rows INTEGER,
    output_rows INTEGER,
    duplicate_rows INTEGER,
    skill_count INTEGER,
    duration_ms INTEGER,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT
);

CREATE INDEX IF NOT EXISTS ix_processing_runs_status_requested
    ON processing_runs (status, requested_at DESC);

CREATE TABLE IF NOT EXISTS job_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(48) NOT NULL,
    source_record_id VARCHAR(256) NOT NULL,
    company_normalized VARCHAR(256) NOT NULL,
    title_normalized VARCHAR(256) NOT NULL,
    location_normalized VARCHAR(256) NOT NULL,
    role_family VARCHAR(96) NOT NULL,
    description TEXT NOT NULL,
    content_hash CHAR(64) NOT NULL,
    composite_join_key CHAR(64) NOT NULL,
    is_remote BOOLEAN NOT NULL DEFAULT FALSE,
    posted_at TIMESTAMPTZ NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_job_posting_source_record UNIQUE (source, source_record_id)
);

CREATE INDEX IF NOT EXISTS ix_job_postings_content_hash
    ON job_postings (content_hash);
CREATE INDEX IF NOT EXISTS ix_job_postings_composite_key_posted
    ON job_postings (composite_join_key, posted_at DESC);
CREATE INDEX IF NOT EXISTS ix_job_postings_filters
    ON job_postings (role_family, location_normalized, posted_at DESC);

CREATE TABLE IF NOT EXISTS skills (
    id BIGSERIAL PRIMARY KEY,
    slug VARCHAR(128) NOT NULL UNIQUE,
    canonical_name VARCHAR(256) NOT NULL,
    category VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS job_posting_skills (
    posting_id UUID NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    skill_id BIGINT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    matched_alias VARCHAR(256) NOT NULL,
    PRIMARY KEY (posting_id, skill_id)
);

CREATE INDEX IF NOT EXISTS ix_job_posting_skills_skill_posting
    ON job_posting_skills (skill_id, posting_id);
