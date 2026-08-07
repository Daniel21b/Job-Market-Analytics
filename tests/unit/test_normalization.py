from skill_analytics.spark.normalization import composite_join_key, normalize_text


def test_normalize_text_is_stable() -> None:
    assert normalize_text("  Senior—Python / AWS Engineer ") == "senior python aws engineer"
    assert normalize_text(None) == "unknown"


def test_composite_join_key_is_deterministic() -> None:
    first = composite_join_key("Acme, Inc.", "Data Engineer", "New York, NY")
    second = composite_join_key("ACME INC", "data engineer", "new york ny")
    assert first == second
    assert len(first) == 64
