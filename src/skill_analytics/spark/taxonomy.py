import csv
from dataclasses import dataclass
from pathlib import Path

from skill_analytics.spark.normalization import normalize_text


@dataclass(frozen=True)
class SkillAlias:
    canonical_skill: str
    alias: str
    category: str


def load_taxonomy(path: str | Path, *, minimum_canonical_skills: int = 1) -> list[SkillAlias]:
    rows: list[SkillAlias] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"canonical_skill", "alias", "category"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"taxonomy must contain columns: {sorted(required)}")
        for row in reader:
            canonical = normalize_text(row["canonical_skill"])
            alias = normalize_text(row["alias"])
            category = normalize_text(row["category"])
            if "unknown" in {canonical, alias, category}:
                continue
            rows.append(SkillAlias(canonical, alias, category))

    canonical_count = len({row.canonical_skill for row in rows})
    if canonical_count < minimum_canonical_skills:
        raise ValueError(
            f"taxonomy has {canonical_count} canonical skills; "
            f"minimum is {minimum_canonical_skills}"
        )
    return rows
