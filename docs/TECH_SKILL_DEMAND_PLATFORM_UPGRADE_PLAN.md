# Tech Skill Demand Platform — Upgrade Plan

## Objective

Replace the notebook/CSV implementation in `Job-Market-Analytics` with an auditable ELT platform built around Airbyte, BigQuery, PySpark, dbt, Airflow, and Docker. Preserve useful parsing and taxonomy logic, but do not publish the proposed resume metrics until dated run artifacts prove each one.

## Non-negotiable truth gate

The current verified baseline is 4,137 cleaned rows: 3,608 Adzuna and 529 Hacker News. Its material dates are May 2024, October 2024, and October 2025. It does not substantiate 120K postings, eight contiguous months, 18% repost removal, 500 normalized skills, a 40-to-12-minute Spark improvement, 40 dbt tests, Airflow alerting, or a 4 GB-to-1.5 GB BigQuery scan reduction.

Each resume number remains withheld until the repository contains a reproducible query or benchmark plus dated raw output. If measured results differ, update the resume to the measured values.

## Recommended architecture

```text
Licensed job source(s)
  -> custom Airbyte incremental source(s)
  -> BigQuery raw_job_postings (immutable append, Airbyte metadata retained)
  -> PySpark normalization pipeline
       -> canonical_job_postings
       -> rejected_job_postings
       -> duplicate_decisions
       -> job_skill_matches
       -> pipeline_metrics
  -> dbt staging / dimensions / facts / marts
  -> Streamlit dashboard and benchmark/evidence reports

Airflow controls:
Airbyte sync -> raw reconciliation -> Spark transform -> dbt source freshness
-> dbt build/test -> publish run manifest -> notify success/failure
```

Airbyte should use an actual source cursor and source primary key in incremental append mode. At-least-once delivery is expected, so downstream deduplication must be explicit and idempotent. BigQuery is the system of record; local Docker services are for development and integration testing, not a substitute for cloud-run evidence.

## Target repository layout

```text
Job-Market-Analytics/
├── README.md
├── Makefile
├── .env.example
├── docker-compose.yml
├── pyproject.toml
├── configs/
│   ├── data_contracts/
│   │   ├── raw_job_posting.schema.json
│   │   └── canonical_job_posting.schema.json
│   └── sources.yml
├── airbyte/
│   ├── source_job_postings/
│   │   ├── Dockerfile
│   │   ├── metadata.yaml
│   │   ├── manifest.yaml or source.py
│   │   └── tests/
│   └── connections/
│       └── README.md
├── spark/
│   ├── Dockerfile
│   ├── jobs/normalize_postings.py
│   ├── src/job_market/
│   │   ├── contracts.py
│   │   ├── normalize.py
│   │   ├── deduplicate.py
│   │   ├── extract_skills.py
│   │   └── metrics.py
│   └── tests/
├── dbt/
│   └── job_market/
│       ├── dbt_project.yml
│       ├── packages.yml
│       ├── models/
│       │   ├── sources.yml
│       │   ├── staging/
│       │   ├── intermediate/
│       │   └── marts/
│       ├── seeds/
│       │   ├── company_aliases.csv
│       │   ├── role_taxonomy.csv
│       │   └── skill_taxonomy.csv
│       ├── tests/
│       └── macros/
├── airflow/
│   ├── Dockerfile
│   ├── dags/tech_skill_demand_daily.py
│   ├── include/
│   └── tests/
├── dashboard/
│   ├── Dockerfile
│   ├── app.py
│   └── queries/
├── infra/
│   ├── bigquery/
│   └── iam/
├── benchmarks/
│   ├── spark/
│   ├── bigquery/
│   └── run_benchmarks.py
├── evidence/
│   ├── manifests/
│   ├── dbt/
│   ├── spark/
│   └── bigquery/
├── legacy/
│   ├── notebooks/
│   └── README.md
├── tests/
│   ├── fixtures/
│   └── integration/
└── .github/workflows/ci.yml
```

## Data contracts and warehouse model

### Raw contract

Retain `source`, `source_record_id`, `source_posted_at`, `source_updated_at`, `observed_at`, `airbyte_extracted_at`, `airbyte_run_id`, `source_payload`, and a payload checksum. Never overwrite the raw payload. Keep source timestamps separate from observation timestamps and record their granularity.

### Spark outputs

- `canonical_job_postings`: one canonical posting version with normalized company, role, location, description, employment type, salary fields, rule version, and provenance.
- `duplicate_decisions`: candidate ID, canonical ID, rule/reason, similarity score, decision timestamp, and pipeline run ID.
- `rejected_job_postings`: rejected row, rule, explanation, and run ID.
- `job_skill_matches`: posting ID, canonical skill ID, matched alias, match location, confidence/rule, taxonomy version, and run ID.
- `pipeline_metrics`: input/output/reject/duplicate counts, source/date coverage, skew statistics, partition counts, and timings.

Avoid opaque Python UDFs for simple normalization. Use native Spark expressions, broadcast the small skill taxonomy where appropriate, and reserve repartitioning/salting for measured skew. Preserve the original row and every transformation decision.

### dbt models

- Staging: `stg_airbyte_job_postings`, `stg_canonical_job_postings`, `stg_job_skill_matches`.
- Dimensions: `dim_company`, `dim_role`, `dim_location`, `dim_skill`, `dim_source`.
- Facts/bridges: `fct_job_posting`, `fct_job_posting_snapshot`, `bridge_job_posting_skill`.
- Marts: `mart_skill_demand_monthly`, `mart_role_demand_monthly`, `mart_company_skill_demand`, `mart_location_skill_demand`, `mart_pipeline_health`.

Partition posting/snapshot facts by `posting_date` (or the documented source-appropriate period date), cluster first by the most common selective filters after workload measurement, and enable required partition filters on large marts. The resume wording may say role/location clustering only if benchmark queries prove that ordering is useful.

## Orchestration contract

The daily Airflow DAG should be idempotent and parameterized by logical date/backfill interval:

1. Trigger the Airbyte connection and poll the job to completion.
2. Record Airbyte job ID, cursor/state, extracted count, rejected count, and destination reconciliation.
3. Fail if raw data is missing, stale, or outside contract.
4. Submit the PySpark transform with the run ID and bounded input interval.
5. Validate Spark output reconciliation and duplicate/skill metrics.
6. Run `dbt source freshness`.
7. Run `dbt build` for affected models and tests.
8. Generate one immutable pipeline run manifest linking Airbyte, Spark, dbt, and BigQuery job identifiers.
9. Notify the configured channel on retry exhaustion or freshness failure.

Set bounded retries with exponential backoff. Demonstrate the alert path using a controlled stale-source or failed-sync test; screenshots alone are not sufficient evidence.

## Migration phases and acceptance gates

### Phase 0 — Access, security, and source feasibility

- Add the Desktop repository as a writable workspace root.
- Revoke and rotate the committed Adzuna credential; remove it from current history before publishing further work.
- Select a job-posting source whose terms, quotas, cursor semantics, and historical coverage permit 120K records and eight months.
- Create a GCP project with billing, BigQuery datasets in one region, service identities, and a budget alert.
- Choose the failure-alert destination.

Gate: new credentials work from secret storage, no secret scanning failures, and a documented source contract proves historical/incremental feasibility.

### Phase 1 — Repository reset and local developer platform

- Move the existing notebooks/data/report into `legacy/` without treating them as production inputs.
- Add pinned Python and container dependencies, Make targets, Docker Compose, pre-commit hooks, and CI.
- Bring up Airflow, Spark, dbt runner, and dashboard locally with health checks.

Gate: one command starts the local stack; lint, type checks, unit tests, and container health checks pass in CI.

### Phase 2 — Airbyte ingestion and raw BigQuery layer

- Implement and test custom source streams with source-defined primary keys and cursors.
- Configure BigQuery destination and append-only raw tables.
- Add backfill boundaries, state checkpoint tests, replay/idempotency tests, and raw reconciliation.

Gate: two consecutive incremental syncs show correct state advancement, deliberate replay produces explainable duplicates, and a dated raw manifest links counts to Airbyte and BigQuery jobs.

### Phase 3 — PySpark canonicalization, deduplication, and skills

- Port reusable parser/company/role logic into tested functions.
- Define repost identity separately from same-ID re-delivery and recurring roles.
- Build exact, normalized-key, and similarity candidate stages with a persisted decision table.
- Build a versioned skill taxonomy with at least 500 canonical skills/aliases only if the source and validation support them.
- Produce clean, reject, duplicate, match, and metric outputs.

Gate: golden fixtures pass; raw = canonical + rejected + duplicate dispositions under the documented counting policy; sampled duplicate and skill matches meet a recorded review threshold.

### Phase 4 — dbt warehouse and 40+ meaningful tests

- Implement staging, dimensional, fact, bridge, and demand marts.
- Add generic and singular tests for keys, relationships, accepted values, temporal validity, reconciliation, duplicate leakage, skill coverage, and source/date completeness.
- Generate docs and preserve `manifest.json`, `run_results.json`, and test inventory per evidence run.

Gate: at least 40 distinct meaningful tests pass against a dated cloud dataset; test count is generated from artifacts, not manually stated.

### Phase 5 — Airflow orchestration and alert proof

- Implement the daily DAG, backfill DAG/parameters, retries, freshness checks, run manifest, and notification callback.
- Add DAG parse/unit tests and an integration test with a deliberately failed/stale upstream run.

Gate: successful run, retry recovery, terminal failure alert, and stale-source alert are all represented by dated task/run IDs and logs.

### Phase 6 — Dashboard and publishable analytics

- Replace randomized fallback data with hard failure and visible last-successful-run metadata.
- Query only dbt marts with required date/source filters.
- Add data coverage, freshness, taxonomy version, and methodology panels.

Gate: dashboard totals reconcile to marts, empty/stale data cannot look healthy, and deployed version links to a pipeline run manifest.

### Phase 7 — Performance and cost benchmarking

- Pin an immutable 120K+ input snapshot if legitimately available.
- Benchmark baseline and optimized Spark jobs on identical data, code-independent cluster settings, cold/warm policy, and at least five runs; store event logs and percentile/median results.
- Diagnose skew from key distributions and Spark plans before choosing repartitioning, broadcast, or salting.
- Run paired BigQuery benchmark queries with cache disabled/dry-run estimates and store query text, job IDs, bytes processed/billed, table metadata, and dates.

Gate: only publish `40 -> 12 minutes` and `4 GB -> 1.5 GB` if the measured, repeatable results match those figures. Otherwise publish the measured numbers.

### Phase 8 — Evidence release and portfolio/resume update

- Generate `evidence/manifests/<run_id>.json` with dataset version, source coverage, row counts, duplicate ratio, distinct canonical skills, dbt test results, Spark timings, and BigQuery scan results.
- Update README architecture, runbook, lineage, limitations, and cost controls.
- Update the portfolio evidence ledger and resume only after every claimed number links to an artifact.

Gate: a fresh reviewer can reproduce or independently query every published claim without relying on notebook output or prose.

## Claim-to-proof definitions

| Claim | Required computation/evidence |
|---|---|
| 120K+ postings | Count from canonical fact/snapshot under a documented grain, plus raw/canonical reconciliation and source/date coverage. |
| Eight months | Eight contiguous covered periods meeting minimum completeness/freshness thresholds, not merely eight partition names. |
| 18% reposts | `repost_duplicates / eligible_raw_postings`, with same-ID delivery duplicates excluded and reason rows persisted. |
| 500+ skills | Count of active canonical skill IDs that have versioned aliases and validated matches; do not count aliases as skills. |
| 40 to 12 minutes | Same input, cluster, cache policy, and output contract; repeated baseline/optimized Spark event-log timings. |
| 40+ dbt tests | Programmatic count of successful generic and singular test nodes in dated dbt artifacts. |
| Retries/alerts | Airflow run/task IDs and logs from controlled retry and stale/failure exercises, plus delivered notification evidence. |
| 4 GB to 1.5 GB | Identical semantic query before/after table design, cache policy controlled, with BigQuery job IDs and bytes processed. |

## External prerequisites/blockers

Implementation cannot truthfully complete the resume scope without:

1. Write access to `/Users/danielberhane/Desktop/projects/Job-Market-Analytics`.
2. A newly rotated job-source credential; the committed credential must not be reused.
3. A lawful source/backfill capable of 120K+ records and eight contiguous months.
4. A GCP project, billing/budget approval, BigQuery dataset region, and service-account strategy.
5. A chosen alert destination such as email or Slack/webhook.
6. Agreement that measured results replace proposed resume numbers when they differ.

## End-to-end verification

- Secret scan and dependency/container vulnerability checks.
- Connector spec/check/discover/read/state tests plus replay tests.
- PySpark unit, property, golden-fixture, reconciliation, and deterministic-output tests.
- dbt parse/compile/build/source-freshness plus artifact-based test inventory.
- Airflow DAG import, task dependency, retry, idempotency, backfill, and failure-alert tests.
- BigQuery schema, partition, clustering, required-filter, and query-cost assertions.
- Docker Compose health and local smoke test.
- Cloud canary and full daily run producing one immutable evidence manifest.
- Dashboard reconciliation and stale/missing-data behavior check.
