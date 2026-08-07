# Local validation record

Validated on 2026-08-07 using Python 3.11, PySpark 3.5.9, Java 11, PostgreSQL 16,
Redis 7, and Docker on an ARM64 development machine.

## Quality gates

- Ruff passed for `src`, `tests`, and `benchmarks`.
- Eight non-Spark unit tests passed.
- Four Spark contract tests passed, including pandas-compatible multiline CSV parsing,
  pre-1900 timestamp handling, database field bounds, repost removal, and skill extraction.
- The PostgreSQL/Redis service integration test passed.
- The FastAPI and PySpark worker images both built successfully.

## End-to-end processing result

The asynchronous API queued the checked-in `jobs_cleaned.csv` fixture, the worker executed the
optimized Spark path, and the publisher committed the canonical postings and skill bridges to a
clean PostgreSQL database before invalidating Redis metrics keys.

| Metric | Measured result |
|---|---:|
| Input rows | 4,137 |
| Canonical output rows | 4,135 |
| Duplicate decisions | 2 |
| Duplicate rate | 0.0483% |
| Skill-match rows | 2,164 |
| Distinct matched canonical skills | 65 |
| Optimized local duration | 17.627 seconds |
| Partition skew ratio before | 1.644 |
| Partition skew ratio after | 1.060 |

The input count independently reconciles with pandas: 3,608 Adzuna rows and 529 Hacker News rows.

## Populated API cache result

The benchmark sent 100 warm requests with `skill=python`, `role_family=uncategorized`, and
`location=seattle wa` against the populated PostgreSQL tables.

| Metric | Measured result |
|---|---:|
| Redis cache hits | 100 / 100 |
| p50 | 0.898 ms |
| p95 | 1.989 ms |
| Maximum | 4.013 ms |
| Sub-50 ms p95 target | Met locally |

This is development-scale validation. It does not substantiate 120,000 postings, 18% duplicate
removal, 500+ matched skills, or a 40-to-12-minute batch reduction. Those claims remain gated on a
versioned production-scale dataset and repeated same-input benchmark runs.
