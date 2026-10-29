import argparse
import json
import time
from pathlib import Path

from pyspark.sql import SparkSession

from skill_analytics.spark.pipeline import (
    PipelineConfig,
    canonicalize,
    classify_duplicates,
    extract_skill_matches,
    partition_profile,
)


def _read_input(spark: SparkSession, input_uri: str):  # type: ignore[no-untyped-def]
    suffix = Path(input_uri).suffix.lower()
    if suffix == ".csv":
        return (
            spark.read.option("header", True)
            .option("multiLine", True)
            .option("escape", '"')
            .csv(input_uri)
        )
    if suffix in {".json", ".jsonl", ".ndjson"}:
        return spark.read.json(input_uri)
    return spark.read.parquet(input_uri)


def execute(
    *,
    input_uri: str,
    output_uri: str,
    taxonomy_path: str,
    partitions: int,
    optimized: bool,
    minimum_canonical_skills: int,
    master: str,
) -> dict[str, object]:
    started = time.perf_counter()
    spark = (
        SparkSession.builder.appName("distributed-skill-analytics")
        .master(master)
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.skewJoin.enabled", "true")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    try:
        raw = _read_input(spark, input_uri).cache()
        input_rows = raw.count()
        config = PipelineConfig(partitions=partitions, optimized=optimized)
        normalized = canonicalize(raw).cache()
        before_profile = partition_profile(normalized)
        canonical, duplicates = classify_duplicates(normalized, config)
        canonical = canonical.cache()
        duplicates = duplicates.cache()
        skills = extract_skill_matches(
            spark,
            canonical,
            taxonomy_path,
            minimum_canonical_skills,
        ).cache()

        output_rows = canonical.count()
        duplicate_rows = duplicates.count()
        if output_rows + duplicate_rows != input_rows:
            raise ValueError("Canonical and duplicate counts do not reconcile with input")
        skill_matches = skills.count()
        canonical_skill_count = skills.select("canonical_skill").distinct().count()
        after_profile = partition_profile(canonical)

        canonical.write.mode("overwrite").parquet(f"{output_uri}/canonical_job_postings")
        duplicates.write.mode("overwrite").parquet(f"{output_uri}/duplicate_decisions")
        skills.write.mode("overwrite").parquet(f"{output_uri}/job_skill_matches")
        canonical.select(
            "posting_key",
            "source",
            "source_record_id",
            "company_normalized",
            "title_normalized",
            "location_normalized",
            "role_family",
            "description",
            "content_hash",
            "composite_join_key",
            "is_remote",
            "posted_at",
            "observed_at",
        ).write.mode("overwrite").json(f"{output_uri}/publish/job_postings")
        skills.write.mode("overwrite").json(f"{output_uri}/publish/job_skill_matches")

        metrics: dict[str, object] = {
            "input_rows": input_rows,
            "output_rows": output_rows,
            "duplicate_rows": duplicate_rows,
            "duplicate_rate": round(duplicate_rows / input_rows, 6) if input_rows else 0.0,
            "skill_match_rows": skill_matches,
            "canonical_skill_count": canonical_skill_count,
            "optimized": optimized,
            "configured_partitions": partitions,
            "partition_profile_before": before_profile,
            "partition_profile_after": after_profile,
            "duration_ms": round((time.perf_counter() - started) * 1_000),
        }
        if output_uri.startswith("/") or output_uri.startswith("."):
            metrics_path = Path(output_uri) / "pipeline_metrics.json"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return metrics
    finally:
        spark.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize and enrich job postings with PySpark")
    parser.add_argument("--input-uri", required=True)
    parser.add_argument("--output-uri", required=True)
    parser.add_argument("--taxonomy-path", required=True)
    parser.add_argument("--master", default="local[*]")
    parser.add_argument("--partitions", type=int, default=8)
    parser.add_argument("--minimum-canonical-skills", type=int, default=1)
    parser.add_argument("--optimized", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = execute(
        input_uri=args.input_uri,
        output_uri=args.output_uri,
        taxonomy_path=args.taxonomy_path,
        partitions=args.partitions,
        optimized=args.optimized,
        minimum_canonical_skills=args.minimum_canonical_skills,
        master=args.master,
    )
    print(json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    main()
