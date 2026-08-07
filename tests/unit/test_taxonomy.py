from pathlib import Path

import pytest

from skill_analytics.spark.taxonomy import load_taxonomy


def test_load_taxonomy_normalizes_aliases(tmp_path: Path) -> None:
    taxonomy = tmp_path / "skills.csv"
    taxonomy.write_text(
        "canonical_skill,alias,category\nApache Spark,PySpark,Data Engineering\n",
        encoding="utf-8",
    )
    rows = load_taxonomy(taxonomy)
    assert rows[0].canonical_skill == "apache spark"
    assert rows[0].alias == "pyspark"
    assert rows[0].category == "data engineering"


def test_load_taxonomy_enforces_evidence_threshold(tmp_path: Path) -> None:
    taxonomy = tmp_path / "skills.csv"
    taxonomy.write_text(
        "canonical_skill,alias,category\npython,python,languages\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="minimum is 500"):
        load_taxonomy(taxonomy, minimum_canonical_skills=500)
