"""Export public aggregates only from independently audited pipeline outputs."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence
    run = json.loads((evidence / "run-completed.json").read_text())
    audit = json.loads((evidence / "output-audit.json").read_text())
    sample = json.loads((evidence / "sample-manifest.json").read_text())
    latency = json.loads((evidence / "api-latency.json").read_text())
    assert run["status"] == "succeeded" and audit["reconciliation_passed"]
    m = run["metrics"]
    posts = pq.read_table(
        args.output_dir / "canonical_job_postings", columns=["posting_key", "posted_at"]
    ).to_pandas()
    matches = pq.read_table(
        args.output_dir / "job_skill_matches",
        columns=["posting_key", "canonical_skill", "category"],
    ).to_pandas()
    posts["month"] = pd.to_datetime(posts["posted_at"], utc=True).dt.strftime("%Y-%m")
    assert posts["posting_key"].is_unique and len(posts) == m["output_rows"]
    assert len(matches) == m["skill_match_rows"]
    merged = matches.merge(posts, on="posting_key", validate="many_to_one")
    posts["withSkills"] = posts["posting_key"].isin(set(matches["posting_key"]))
    monthly = [
        {"month": month, "postings": len(group), "withSkills": int(group["withSkills"].sum())}
        for month, group in posts.groupby("month", sort=True)
    ]
    skills = []
    for (name, category), group in merged.groupby(["canonical_skill", "category"], sort=True):
        skills.append(
            {
                "name": name,
                "category": category,
                "postings": int(group["posting_key"].nunique()),
                "monthly": [
                    {"month": month, "postings": int(rows["posting_key"].nunique())}
                    for month, rows in group.groupby("month", sort=True)
                ],
            }
        )
    assert sum(row["postings"] for row in monthly) == m["output_rows"]
    assert sum(row["postings"] for row in skills) == m["skill_match_rows"]
    warm = next(
        q
        for q in latency["results"]
        if q["params"] == {"skill": "python"} and q["mode"] == "warm_cache"
    )
    date = evidence.name
    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "benchmarkDate": date,
        "runId": run["id"],
        "sampleSha256": sample["sample_sha256"],
        "source": {
            "name": "OpenJobData",
            "url": "https://huggingface.co/datasets/scholarweave/Jobs-Dataset-v2",
            "revision": sample["revision"],
            "asOf": sample["source_as_of"],
            "country": "United States",
            "sampling": sample["selection"],
            "statusCoverage": (
                "Includes active and closed archived postings"
                if sample.get("includes_closed_archive")
                else "Active snapshot records"
            ),
        },
        "metrics": {
            "inputRows": m["input_rows"],
            "canonicalRows": m["output_rows"],
            "duplicateRows": m["duplicate_rows"],
            "skillMatchRows": m["skill_match_rows"],
            "matchedSkills": m["canonical_skill_count"],
            "postingsWithSkills": int(posts["withSkills"].sum()),
            "sparkDurationMs": m["duration_ms"],
        },
        "latency": {
            "pythonWarmP95Ms": warm["p95_ms"],
            "requests": warm["requests"],
            "concurrency": 1,
            "environment": "local",
        },
        "monthly": monthly,
        "skills": skills,
        "evidenceUrl": f"https://github.com/Daniel21b/Job-Market-Analytics/blob/main/docs/BENCHMARK_{date}.md",
        "limitations": [
            "Verified aggregate snapshot, not a live job feed.",
            "Convenience sample; monthly source dates do not measure market-wide hiring growth.",
            "Country-only location; no city, salary or role-family breakdown is inferred.",
            "Skills overlap across postings; skill counts cannot be summed to count distinct jobs.",
            "Alias matching can be ambiguous (for example, go); skill precision is not audited.",
            "Duplicate candidates are heuristic decisions, not audited true duplicates.",
            "Latency is local, sequential and cached; it is not a production SLA.",
        ],
    }
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        json.dumps(
            {
                "destination": str(args.destination),
                "postings": len(posts),
                "skills": len(skills),
                "bytes": args.destination.stat().st_size,
            }
        )
    )


if __name__ == "__main__":
    main()
