"""Freeze a bounded, reproducible real-posting sample; never synthesize rows."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen

import pyarrow as pa
import pyarrow.parquet as pq


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--target", type=int, default=120000)
    args = parser.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    meta = json.loads((args.evidence / "source-revision.json").read_text())
    manifest = json.loads((args.evidence / "source-manifest.json").read_text())
    as_of = datetime.fromisoformat(manifest["active"]["as_of"])
    counts, years = Counter(), Counter()
    selected, used, ids = [], [], set()
    for _, entry in sorted(
        manifest["active"]["minimal"]["shards"].items(), key=lambda x: int(x[0])
    ):
        path = args.data_dir / Path(entry["path"]).name
        url = f"https://huggingface.co/datasets/{meta['dataset']}/resolve/{meta['revision']}/{entry['path']}"
        if not path.exists():
            with urlopen(url, timeout=120) as src, path.open("wb") as dst:
                while block := src.read(1024 * 1024):
                    dst.write(block)
        if path.stat().st_size != entry["bytes"] or sha(path) != entry["sha256"]:
            raise ValueError(f"Integrity mismatch: {path.name}")
        used.append(entry)
        for row in pq.read_table(path).to_pylist():
            counts["examined"] += 1
            if row.get("country") != "United States":
                counts["not_us"] += 1
                continue
            description = (row.get("description_plain") or "").strip()
            if len(description) < 200:
                counts["short_or_missing_description"] += 1
                continue
            posted = row.get("posted_at")
            if not posted or not datetime(2025, 1, 1, tzinfo=UTC) <= posted <= as_of:
                counts["outside_date_range_or_missing"] += 1
                continue
            if not row.get("title") or row.get("company_id") is None or not row.get("posting_id"):
                counts["missing_identity"] += 1
                continue
            if row["posting_id"] in ids:
                counts["repeated_source_id"] += 1
                continue
            ids.add(row["posting_id"])
            years[str(posted.year)] += 1
            selected.append(
                {
                    "source": "openjobdata",
                    "source_record_id": hashlib.sha256(row["posting_id"].encode()).hexdigest(),
                    "original_posting_id": row["posting_id"],
                    "source_url": row.get("apply_url"),
                    "company": f"openjobdata company {row['company_id']}",
                    "title": row["title"],
                    "location": "United States",
                    "description": description,
                    "source_posted_at": posted.isoformat(),
                    "observed_at": row["first_seen_at"].isoformat(),
                    "is_remote": bool(row.get("is_remote")),
                }
            )
            if len(selected) == args.target:
                break
        print(
            json.dumps(
                {"shards": len(used), "selected": len(selected), "examined": counts["examined"]}
            ),
            flush=True,
        )
        if len(selected) == args.target:
            break
    if len(selected) < args.target:
        raise ValueError(f"Only {len(selected)} eligible rows; target not reached")
    dest = args.data_dir / f"postings-{args.target}.parquet"
    pq.write_table(pa.Table.from_pylist(selected), dest, compression="zstd")
    report = {
        **meta,
        "frozen_at": datetime.now(UTC).isoformat(),
        "source_as_of": as_of.isoformat(),
        "selection": (
            "Numeric shard order, original row order, stop at target; convenience sample, not"
            " representative."
        ),
        "filters": (
            "United States; nonempty title/company/source ID; description >=200 characters; "
            "source posted date 2025-01-01 through snapshot timestamp; unique source posting "
            "IDs."
        ),
        "mapping": (
            "Stable source company IDs used as company identity; SHA256 of posting ID as "
            "source_record_id; location is country only because minimal source lacks "
            "consistent city/region. Original posting ID and source URL retained in frozen "
            "input."
        ),
        "limitations": (
            "Source posted_at values are unverified. Upstream active snapshot may already be "
            "deduplicated. Country-only location may conflate distinct local openings; "
            "duplicate decisions are heuristic candidates, not audited true reposts. No "
            "future dates or synthetic records included."
        ),
        "selected_rows": len(selected),
        "selected_posted_years": dict(years),
        "filter_counts": dict(counts),
        "shards": used,
        "sample_sha256": sha(dest),
        "sample_bytes": dest.stat().st_size,
    }
    (args.evidence / "sample-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
