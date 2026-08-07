from skill_analytics.main import create_app


def test_openapi_exposes_health_metrics_and_runs() -> None:
    schema = create_app().openapi()
    paths = schema["paths"]
    assert "/health" in paths
    assert "/v1/metrics/skill-demand" in paths
    assert "/v1/runs" in paths
    assert "/v1/runs/{run_id}" in paths
