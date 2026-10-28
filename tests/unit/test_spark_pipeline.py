from pathlib import Path

import pytest

pyspark = pytest.importorskip("pyspark")

from pyspark.sql import SparkSession  # noqa: E402

from skill_analytics.spark.job import _read_input  # noqa: E402
from skill_analytics.spark.pipeline import (  # noqa: E402
    PipelineConfig,
    canonicalize,
    classify_duplicates,
    extract_skill_matches,
)


@pytest.fixture(scope="module")
def spark() -> SparkSession:
    session = SparkSession.builder.master("local[2]").appName("skill-analytics-tests").getOrCreate()
    yield session
    session.stop()


@pytest.mark.spark
def test_pipeline_deduplicates_and_extracts_skills(spark: SparkSession, tmp_path: Path) -> None:
    rows = [
        {
            "source": "test",
            "id": "1",
            "company": "Acme",
            "role": "Data Engineer",
            "location": "NYC",
            "description": "Build Python pipelines with PySpark and AWS.",
            "posting_date": "2026-01-01T00:00:00Z",
        },
        {
            "source": "test",
            "id": "2",
            "company": "Acme",
            "role": "Data Engineer",
            "location": "NYC",
            "description": "Build Python pipelines with PySpark and AWS.",
            "posting_date": "2026-01-02T00:00:00Z",
        },
    ]
    taxonomy = tmp_path / "skills.csv"
    taxonomy.write_text(
        "canonical_skill,alias,category\n"
        "python,python,languages\n"
        "apache spark,pyspark,data\n"
        "aws,aws,cloud\n",
        encoding="utf-8",
    )
    frame = canonicalize(spark.createDataFrame(rows))
    canonical, duplicates = classify_duplicates(frame, PipelineConfig(partitions=2))
    matches = extract_skill_matches(spark, canonical, str(taxonomy), 1)
    assert canonical.count() == 1
    assert duplicates.count() == 1
    assert {row.canonical_skill for row in matches.collect()} == {
        "python",
        "apache spark",
        "aws",
    }


@pytest.mark.spark
def test_csv_reader_handles_pandas_quoting(spark: SparkSession, tmp_path: Path) -> None:
    csv_path = tmp_path / "quoted.csv"
    csv_path.write_text(
        'id,description\n1,"hello ""spark"", team\nnext"\n2,simple\n',
        encoding="utf-8",
    )
    rows = _read_input(spark, str(csv_path)).orderBy("id").collect()
    assert len(rows) == 2
    assert rows[0].description == 'hello "spark", team\nnext'


@pytest.mark.spark
def test_canonicalize_replaces_ancient_posting_dates(spark: SparkSession) -> None:
    frame = canonicalize(
        spark.createDataFrame(
            [
                {
                    "source": "test",
                    "id": "ancient-date",
                    "company": "A" * 300,
                    "role": "Engineer",
                    "location": "NYC",
                    "description": "Python",
                    "posting_date": "0001-01-01T00:00:00Z",
                    "observed_at": "2026-02-03T00:00:00Z",
                }
            ]
        )
    )
    row = frame.select("posted_at", "company_normalized").first()
    assert row.posted_at.year == 2026
    assert len(row.company_normalized) == 256


@pytest.mark.spark
def test_canonicalize_replaces_ancient_observation_dates(spark: SparkSession) -> None:
    frame = canonicalize(
        spark.createDataFrame(
            [
                {
                    "source": "test",
                    "id": "ancient-observation",
                    "company": "Acme",
                    "role": "Engineer",
                    "location": "NYC",
                    "description": "Python",
                    "posting_date": "",
                    "observed_at": "0001-01-01T00:00:00Z",
                }
            ]
        )
    )
    row = frame.select("posted_at", "observed_at").first()
    assert row.posted_at.year >= 2026
    assert row.observed_at.year >= 2026


@pytest.mark.spark
def test_bounded_duplicate_comparison_matches_unbounded_reference(spark: SparkSession) -> None:
    from datetime import UTC, datetime, timedelta

    from pyspark.sql import functions as F

    cases = [(100, n, days) for n in (0, 1, 7, 8, 9, 30) for days in (1, 90, 91)]
    cases += [(size, changes, 10) for size, changes in ((13, 1), (13, 2), (250, 20), (250, 21))]
    rows = []
    expected_candidates = []
    for i, (size, changes, days) in enumerate(cases):
        first = "a" * size
        second = "a" * (size - changes) + "b" * changes
        for n, text in enumerate((first, second)):
            rows.append(
                {
                    "source": "boundary",
                    "id": f"{i}-{n}",
                    "company": f"Company {i}",
                    "role": "Engineer",
                    "location": "US",
                    "description": text,
                    "posting_date": (
                        datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=days * n)
                    ).isoformat(),
                }
            )
        expected_candidates.append((str(i), first, second, days))
    reference = spark.createDataFrame(expected_candidates, ["case", "first", "second", "days"])
    reference = reference.withColumn(
        "similarity",
        F.lit(1.0)
        - F.levenshtein("first", "second") / F.greatest(F.length("first"), F.length("second")),
    )
    expected = {
        r["case"]: float(r["similarity"])
        for r in reference.filter(
            (F.col("first") == F.col("second"))
            | ((F.col("similarity") >= 0.92) & F.col("days").between(0, 90))
        ).collect()
    }
    frame = canonicalize(spark.createDataFrame(rows))
    canonical, duplicates = classify_duplicates(frame, PipelineConfig(partitions=2))
    resolved = duplicates.join(
        frame.select("posting_key", "source_record_id"), "posting_key"
    ).collect()
    observed = {r.source_record_id.split("-")[0]: r.similarity_score for r in resolved}
    assert observed == expected
    assert canonical.count() + len(resolved) == len(rows)
