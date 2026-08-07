import argparse
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path

from skill_analytics.spark.job import execute


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-uri", required=True)
    parser.add_argument("--taxonomy-path", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--partitions", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--master", default="local[*]")
    args = parser.parse_args()

    results: dict[str, list[dict[str, object]]] = {"baseline": [], "optimized": []}
    for label, optimized in (("baseline", False), ("optimized", True)):
        for attempt in range(args.repeats):
            metrics = execute(
                input_uri=args.input_uri,
                output_uri=f"{args.output_root}/{label}/run-{attempt + 1}",
                taxonomy_path=args.taxonomy_path,
                partitions=args.partitions,
                optimized=optimized,
                minimum_canonical_skills=1,
                master=args.master,
            )
            results[label].append(metrics)

    baseline_ms = [int(item["duration_ms"]) for item in results["baseline"]]
    optimized_ms = [int(item["duration_ms"]) for item in results["optimized"]]
    baseline_median = statistics.median(baseline_ms)
    optimized_median = statistics.median(optimized_ms)
    report = {
        "measured_at": datetime.now(UTC).isoformat(),
        "input_uri": args.input_uri,
        "master": args.master,
        "partitions": args.partitions,
        "repeats": args.repeats,
        "baseline_duration_ms": baseline_ms,
        "optimized_duration_ms": optimized_ms,
        "baseline_median_ms": baseline_median,
        "optimized_median_ms": optimized_median,
        "reduction_percent": round(
            (baseline_median - optimized_median) / baseline_median * 100, 3
        )
        if baseline_median
        else 0.0,
        "runs": results,
    }
    destination = Path(args.output_root) / "spark_benchmark.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
