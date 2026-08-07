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
def test_pipeline_deduplicates_and_extracts_skills(
    spark: SparkSession, tmp_path: Path
) -> None:
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
