# Real-posting benchmark — October 25, 2026

This is an October 2026 follow-up to the original January–March 2025 project. It does not retroactively establish measurements from 2025. Dates in raw evidence use UTC (the completed run may be October 26 UTC).

## Data provenance

Source: [OpenJobData / scholarweave Jobs-Dataset-v2](https://huggingface.co/datasets/scholarweave/Jobs-Dataset-v2), immutable revision `7675a78a63ea3d42d47515a350ac7650da972bd0`. Snapshot timestamp: 2026-10-25 16:29:33 UTC. Frozen input: 120,000 unique source IDs; 27,864 source-dated 2025 and 92,136 source-dated 2026.

Selection follows numeric shard order and file row order, stopping at 120,000 qualifying records: United States, nonempty title/company/source ID, description at least 200 characters, and source posting date from 2025-01-01 through the snapshot timestamp. This is a convenience sample, not a representative labor-market survey or a complete historical archive. Provider dates have not been independently verified.

Input SHA-256: `641c7d6e11ff8c7bc217e6f1036c8dd6907a00e908053e12f9b78013133a5d11`. The [sample manifest](../evidence/2026-10-25/sample-manifest.json) records source shard checksums, filters, and field mapping. Raw descriptions are retained locally and are not redistributed in this repository. The dataset card labels the dataset Apache-2.0; underlying job descriptions may retain source rights.

## Pipeline results

| Measurement | Observed |
|---|---:|
| Input records | 120,000 |
| Canonical postings | 107,330 |
| Heuristic duplicate candidates removed | 12,670 |
| Posting-to-skill matches | 40,001 |
| Distinct matched canonical skills | 73 |
| Spark duration (ms) | 467,244 |

Duplicate candidate rate: **10.558%**. These are algorithmic decisions, not manually verified duplicate precision. Country-only location can conflate openings in different cities. The upstream snapshot may already remove some duplicates. The taxonomy contains 74 canonical skills; 500+ matched skills and 18% removal are not supported by this run.

The actual API → Redis queue → worker → PySpark → PostgreSQL publisher path was used. Spark duration includes initialization and output writing, but excludes PostgreSQL publication. The complete run timestamps and publisher metrics are preserved in [run-completed.json](../evidence/2026-10-25/run-completed.json). One successful run establishes functionality, not a repeatability or optimization speedup claim.

## HTTP measurements

| Query | Redis mode | Requests | p50 ms | p95 ms | p99 ms |
|---|---|---:|---:|---:|---:|
| all skills | cold_cache | 100 | 31.456 | 33.851 | 34.8 |
| all skills | warm_cache | 1000 | 0.634 | 0.861 | 1.723 |
| {'skill': 'python'} | cold_cache | 100 | 6.816 | 9.368 | 10.469 |
| {'skill': 'python'} | warm_cache | 1000 | 0.579 | 0.858 | 1.451 |
| {'skill': 'sql', 'location': 'united states'} | cold_cache | 100 | 6.099 | 8.471 | 12.55 |
| {'skill': 'sql', 'location': 'united states'} | warm_cache | 1000 | 0.573 | 0.765 | 1.357 |

Sequential HTTP requests, concurrency 1, persistent httpx connection; nearest-rank percentiles. Cold cache deletes only the exact query key before each request; PostgreSQL/OS caches are not reset. Warm cache primed once. Connection setup and deletion excluded from timings. No empty-result queries.

All requests used loopback HTTP on one development machine, concurrency 1. A cache miss is not a cold PostgreSQL buffer cache. These are neither production latency nor concurrent-load guarantees. [Raw timings and hit/miss counts](../evidence/2026-10-25/api-latency.json).

## Environment and reproduction

Application base commit: `d300415fc9d09e321b39cf7a9078c6abf548c194`. ARM64 macOS 27.0.1, 10 CPU cores, 24 GiB RAM; Python 3.11.11, Java Corretto 11, Spark local[4], 8 partitions, 4 GiB driver heap; local PostgreSQL 15 and Redis 7.2.7. Exact Python versions: [environment](../evidence/2026-10-25/python-environment.txt).

Install the project with `pip install -e ".[spark,dev]" pyarrow pandas`. Set `JAVA_HOME` to Java 11 and `PYSPARK_PYTHON` to the same Python interpreter used by the worker. Set `SPARK_MASTER_URL=local[4]`, `SPARK_PARTITIONS=8`, and `PYSPARK_SUBMIT_ARGS="--driver-memory 4g pyspark-shell"`. Use isolated, empty PostgreSQL and Redis instances configured with `DATABASE_URL` and `REDIS_URL`; start the API and worker as described in the README.

```sh
python benchmarks/freeze_openjobdata.py --evidence evidence/2026-10-25 --data-dir /tmp/job-data --target 120000
# POST /v1/runs with input_uri=/tmp/job-data/postings-120000.parquet and an empty output_uri.
# Wait for succeeded before measuring; save GET /v1/runs/{id}.
python benchmarks/measure_frozen_api.py --base-url http://127.0.0.1:8037 --redis-url redis://127.0.0.1:6398/0 --output /tmp/api-latency.json
```

Keep the checked-in source manifests unchanged when reproducing. Rebuilding the Parquet file with different library versions may change its byte hash even when records are equivalent. One initial attempt failed because Python worker and driver versions differed; a second was interrupted before producing output. Neither is counted as a successful run.

## Validation

Independent reconciliation verified 120,000 = 107,330 + 12,670, unique canonical keys, 73 distinct matched skills, and PostgreSQL counts of 107,330 postings / 73 skills / 40,001 relationships. Duplicate reasons were 7,810 exact repost candidates and 4,860 near-repost candidates. [Audit evidence](../evidence/2026-10-25/output-audit.json).

Local verification: 12 unit/Spark tests passed and 1 PostgreSQL/Redis service integration test passed. Benchmark scripts passed Ruff. The service test used a separate Redis database after latency measurement. Run `benchmarks/audit_frozen_output.py --evidence evidence/2026-10-25 --output-dir /tmp/job-output --database-url "$AUDIT_DATABASE_URL"` to reconcile your completed run with its database.
