import argparse
import asyncio
import json
from collections import Counter
from pathlib import Path

import asyncpg
import pyarrow.parquet as pq

parser = argparse.ArgumentParser()
parser.add_argument("--evidence", type=Path, required=True)
parser.add_argument("--output-dir", type=Path, required=True)
parser.add_argument("--database-url", required=True)
args = parser.parse_args()
r = args.evidence
o = args.output_dir
m = json.loads((r / "run-completed.json").read_text())["metrics"]
expected = json.loads((r / "sample-manifest.json").read_text())["selected_rows"]
c = pq.read_table(o / "canonical_job_postings", columns=["posting_key"])
d = pq.read_table(o / "duplicate_decisions", columns=["duplicate_reason"])
s = pq.read_table(o / "job_skill_matches", columns=["canonical_skill"])
assert c.num_rows + d.num_rows == m["input_rows"] == expected
assert c.num_rows == m["output_rows"] and d.num_rows == m["duplicate_rows"]
assert s.num_rows == m["skill_match_rows"]
assert len(set(s["canonical_skill"].to_pylist())) == m["canonical_skill_count"]
assert len(set(c["posting_key"].to_pylist())) == c.num_rows


async def check():
    db = await asyncpg.connect(args.database_url)
    counts = {
        t: await db.fetchval("SELECT count(*) FROM " + t)
        for t in ["job_postings", "skills", "job_posting_skills"]
    }
    await db.close()
    assert counts["job_postings"] == c.num_rows
    assert counts["skills"] == m["canonical_skill_count"]
    assert counts["job_posting_skills"] == s.num_rows
    return counts


result = {
    "reconciliation_passed": True,
    "input_rows": expected,
    "canonical_rows": c.num_rows,
    "duplicate_rows": d.num_rows,
    "duplicate_reasons": dict(Counter(d["duplicate_reason"].to_pylist())),
    "database_counts": asyncio.run(check()),
}
(r / "output-audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
