# Real-posting benchmark — October 26, 2026

This is an October 2026 follow-up to the original January–March 2025 project. It does not retroactively establish measurements from 2025. Dates in raw evidence use UTC. The original 120,000-record benchmark is retained separately. This expanded sample includes those original records plus 80,000 additional unique source IDs; it is 200,000 total, not 320,000. No extra provider was needed because the pinned dataset had enough eligible records.

## Data provenance

Source: [OpenJobData / scholarweave Jobs-Dataset-v2](https://huggingface.co/datasets/scholarweave/Jobs-Dataset-v2), immutable revision `7675a78a63ea3d42d47515a350ac7650da972bd0`. Snapshot timestamp: 2026-10-25 16:29:33 UTC. Frozen input: 200,000 unique source IDs; 46,839 source-dated 2025 and 153,161 source-dated 2026.

Selection follows numeric shard order and file row order, stopping at 200,000 qualifying records: United States, nonempty title/company/source ID, description at least 200 characters, and source posting date from 2025-01-01 through the snapshot timestamp. This is a convenience sample, not a representative labor-market survey or a complete historical archive. Provider dates have not been independently verified.

Input SHA-256: `9dbee9fd46a77fd2576415b96061b1480a098bebf7e9b4b7e419974a6a983d1a`. The [sample manifest](../evidence/2026-10-26/sample-manifest.json) records source shard checksums, filters, and field mapping. Raw descriptions are retained locally and are not redistributed in this repository. The dataset card labels the dataset Apache-2.0; underlying job descriptions may retain source rights.

## Pipeline results

| Measurement | Observed |
|---|---:|
| Input records | 200,000 |
| Canonical postings | 174,361 |
| Heuristic duplicate candidates removed | 25,639 |
| Posting-to-skill matches | 66,339 |
| Distinct matched canonical skills | 73 |
| Spark duration (ms) | 1,130,362 |

Duplicate candidate rate: **12.819%**. These are algorithmic decisions, not manually verified duplicate precision. Country-only location can conflate openings in different cities. The upstream snapshot may already remove some duplicates. The taxonomy contains 74 canonical skills; 500+ matched skills and 18% removal are not supported by this run.

The actual API → Redis queue → worker → PySpark → PostgreSQL publisher path was used. Spark duration includes initialization and output writing, but excludes PostgreSQL publication. The complete run timestamps and publisher metrics are preserved in [run-completed.json](../evidence/2026-10-26/run-completed.json). One successful run establishes functionality, not a repeatability or optimization speedup claim.

## HTTP measurements

| Query | Redis mode | Requests | p50 ms | p95 ms | p99 ms |
|---|---|---:|---:|---:|---:|
| all skills | cold_cache | 100 | 48.324 | 52.09 | 53.433 |
| all skills | warm_cache | 1000 | 0.736 | 0.855 | 1.076 |
| {'skill': 'python'} | cold_cache | 100 | 9.884 | 11.309 | 13.804 |
| {'skill': 'python'} | warm_cache | 1000 | 0.669 | 0.833 | 1.654 |
| {'skill': 'sql', 'location': 'united states'} | cold_cache | 100 | 6.782 | 10.714 | 11.251 |
| {'skill': 'sql', 'location': 'united states'} | warm_cache | 1000 | 0.67 | 0.803 | 1.433 |

Sequential HTTP requests, concurrency 1, persistent httpx connection; nearest-rank percentiles. Cold cache deletes only the exact query key before each request; PostgreSQL/OS caches are not reset. Warm cache primed once. Connection setup and deletion excluded from timings. No empty-result queries.

All requests used loopback HTTP on one development machine, concurrency 1. A cache miss is not a cold PostgreSQL buffer cache. These are neither production latency nor concurrent-load guarantees. [Raw timings and hit/miss counts](../evidence/2026-10-26/api-latency.json).

## Environment and reproduction

Application base commit: `150533425c7afc4e3bd69d79aaa793517963bc77`. ARM64 macOS 27.0.1, 10 CPU cores, 24 GiB RAM; Python 3.11.11, Java Corretto 11, Spark local[4], 8 partitions, 4 GiB driver heap; local PostgreSQL 15 and Redis 7.2.7. Exact Python versions: [environment](../evidence/2026-10-26/python-environment.txt).

Install the project with `pip install -e ".[spark,dev]" pyarrow pandas`. Set `JAVA_HOME` to Java 11 and `PYSPARK_PYTHON` to the same Python interpreter used by the worker. Set `SPARK_MASTER_URL=local[4]`, `SPARK_PARTITIONS=8`, and `PYSPARK_SUBMIT_ARGS="--driver-memory 4g pyspark-shell"`. Use isolated, empty PostgreSQL and Redis instances configured with `DATABASE_URL` and `REDIS_URL`; start the API and worker as described in the README.

```sh
python benchmarks/freeze_openjobdata.py --evidence evidence/2026-10-26 --data-dir /tmp/job-data --target 200000
# POST /v1/runs with input_uri=/tmp/job-data/postings-200000.parquet and an empty output_uri.
# Wait for succeeded before measuring; save GET /v1/runs/{id}.
python benchmarks/measure_frozen_api.py --base-url http://127.0.0.1:8040 --redis-url redis://127.0.0.1:6398/2 --output /tmp/api-latency.json
```

Keep the checked-in source manifests unchanged when reproducing. Rebuilding the Parquet file with different library versions may change its byte hash even when records are equivalent. The expanded run uses a fresh PostgreSQL database and separate Redis namespace, so prior benchmark rows cannot inflate publication counts.

## Validation

Independent reconciliation verified 200,000 = 174,361 + 25,639, unique canonical keys, 73 distinct matched skills, and PostgreSQL counts of 174,361 postings / 73 skills / 66,339 relationships. Duplicate reasons were 15,603 exact repost candidates and 10,036 near-repost candidates. [Audit evidence](../evidence/2026-10-26/output-audit.json).

The prior application version passed 12 unit/Spark tests and 1 PostgreSQL/Redis service test. Application pipeline code is unchanged. This expanded run independently reconciled the actual outputs and database, and measured another 3,300 successful HTTP requests. Benchmark scripts passed Ruff. Run `benchmarks/audit_frozen_output.py --evidence evidence/2026-10-26 --output-dir /tmp/job-output --database-url "$AUDIT_DATABASE_URL"` to reconcile your completed run with its database.

Unfiltered cache-miss p95 was 52.090 ms. Consequently, the evidence supports the specifically qualified cached-query result, not a blanket claim that every query stays under 50 ms.
