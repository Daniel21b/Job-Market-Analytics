from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession


@dataclass(frozen=True)
class PipelineConfig:
    partitions: int = 8
    optimized: bool = True
    duplicate_similarity_threshold: float = 0.92
    duplicate_window_days: int = 90
    minimum_canonical_skills: int = 1


def _first_existing(df: DataFrame, names: list[str], default: str | None = None) -> Any:
    from pyspark.sql import functions as F

    columns = [F.col(name).cast("string") for name in names if name in df.columns]
    if default is not None:
        columns.append(F.lit(default))
    if not columns:
        return F.lit(None).cast("string")
    return F.coalesce(*columns)


def _normalized(column: Any) -> Any:
    from pyspark.sql import functions as F

    lowered = F.lower(F.trim(F.coalesce(column, F.lit("unknown"))))
    compact = F.regexp_replace(lowered, r"[^a-z0-9+#]+", " ")
    return F.trim(F.regexp_replace(compact, r"\s+", " "))


def canonicalize(raw: DataFrame) -> DataFrame:
    from pyspark.sql import Window
    from pyspark.sql import functions as F

    source = _first_existing(raw, ["source"], "unknown")
    source_id = _first_existing(raw, ["source_record_id", "job_id", "comment_id", "id"])
    company = _first_existing(raw, ["company", "company_name"], "unknown")
    title = _first_existing(raw, ["role", "title", "job_title"], "unknown")
    location = _first_existing(raw, ["location", "location_name"], "unknown")
    description = _first_existing(raw, ["description", "body", "text"], "")
    role_family = _first_existing(raw, ["role_family", "role_category"], "uncategorized")
    is_remote = _first_existing(raw, ["is_remote"], "false")
    posted_text = _first_existing(
        raw, ["source_posted_at", "posting_date", "created_date", "created_at"]
    )
    month_text = _first_existing(raw, ["month"])
    observed_text = _first_existing(raw, ["observed_at", "scraped_date"])

    frame = raw.select(
        source.alias("source"),
        source_id.alias("source_record_id"),
        company.alias("company_raw"),
        title.alias("title_raw"),
        location.alias("location_raw"),
        description.alias("description"),
        role_family.alias("role_family_raw"),
        is_remote.alias("is_remote_raw"),
        posted_text.alias("posted_text"),
        month_text.alias("month_text"),
        observed_text.alias("observed_text"),
    )
    frame = (
        frame.withColumn(
            "company_normalized", F.substring(_normalized(F.col("company_raw")), 1, 256)
        )
        .withColumn(
            "title_normalized", F.substring(_normalized(F.col("title_raw")), 1, 256)
        )
        .withColumn(
            "location_normalized", F.substring(_normalized(F.col("location_raw")), 1, 256)
        )
        .withColumn(
            "role_family", F.substring(_normalized(F.col("role_family_raw")), 1, 96)
        )
        .withColumn("is_remote", F.lower(F.col("is_remote_raw")).isin("true", "1", "yes"))
        .withColumn("description_normalized", _normalized(F.col("description")))
        .withColumn(
            "posted_at",
            F.coalesce(
                F.to_timestamp("posted_text"),
                F.to_timestamp(F.concat(F.col("month_text"), F.lit("-01"))),
            ),
        )
        .withColumn(
            "observed_at",
            F.coalesce(F.to_timestamp("observed_text"), F.current_timestamp()),
        )
        .withColumn(
            "observed_at",
            F.when(
                F.col("observed_at") >= F.to_timestamp(F.lit("1990-01-01")),
                F.col("observed_at"),
            ).otherwise(F.current_timestamp()),
        )
        .withColumn(
            "posted_at",
            F.when(
                F.col("posted_at") >= F.to_timestamp(F.lit("1990-01-01")),
                F.col("posted_at"),
            ),
        )
        .withColumn("posted_at", F.coalesce(F.col("posted_at"), F.col("observed_at")))
        .withColumn(
            "source_record_id",
            F.coalesce(
                F.col("source_record_id"),
                F.sha2(
                    F.concat_ws(
                        "|",
                        "source",
                        "company_normalized",
                        "title_normalized",
                        "location_normalized",
                        "description_normalized",
                    ),
                    256,
                ),
            ),
        )
        .withColumn(
            "posting_key", F.sha2(F.concat_ws("|", "source", "source_record_id"), 256)
        )
        .withColumn(
            "content_hash",
            F.sha2(
                F.concat_ws(
                    "|",
                    "company_normalized",
                    "title_normalized",
                    "location_normalized",
                    "description_normalized",
                ),
                256,
            ),
        )
        .withColumn(
            "composite_join_key",
            F.sha2(
                F.concat_ws(
                    "|", "company_normalized", "title_normalized", "location_normalized"
                ),
                256,
            ),
        )
    )

    latest_delivery = Window.partitionBy("source", "source_record_id").orderBy(
        F.col("observed_at").desc()
    )
    return frame.withColumn("delivery_rank", F.row_number().over(latest_delivery))


def classify_duplicates(frame: DataFrame, config: PipelineConfig) -> tuple[DataFrame, DataFrame]:
    from pyspark.sql import Window
    from pyspark.sql import functions as F

    deliveries = frame.withColumn(
        "delivery_duplicate", F.when(F.col("delivery_rank") > 1, F.lit("source_redelivery"))
    )
    current = deliveries.filter(F.col("delivery_rank") == 1)
    if config.optimized:
        current = current.repartition(config.partitions, "composite_join_key")

    history = Window.partitionBy("composite_join_key").orderBy(
        F.col("posted_at").asc_nulls_last(), F.col("observed_at").asc()
    )
    compared = (
        current.withColumn("previous_posting_key", F.lag("posting_key").over(history))
        .withColumn("previous_content_hash", F.lag("content_hash").over(history))
        .withColumn("previous_description", F.lag("description_normalized").over(history))
        .withColumn("previous_posted_at", F.lag("posted_at").over(history))
        .withColumn(
            "description_similarity",
            F.when(
                F.col("previous_description").isNotNull(),
                F.lit(1.0)
                - (
                    F.levenshtein("description_normalized", "previous_description")
                    / F.greatest(
                        F.length("description_normalized"),
                        F.length("previous_description"),
                        F.lit(1),
                    )
                ),
            ),
        )
        .withColumn(
            "days_since_previous",
            F.datediff(F.to_date("posted_at"), F.to_date("previous_posted_at")),
        )
        .withColumn(
            "duplicate_reason",
            F.when(
                F.col("content_hash") == F.col("previous_content_hash"),
                F.lit("exact_repost"),
            ).when(
                (F.col("description_similarity") >= config.duplicate_similarity_threshold)
                & (F.col("days_since_previous").between(0, config.duplicate_window_days)),
                F.lit("near_repost"),
            ),
        )
    )

    delivery_duplicates = deliveries.filter(F.col("delivery_rank") > 1).select(
        "posting_key",
        F.lit(None).cast("string").alias("canonical_posting_key"),
        F.col("delivery_duplicate").alias("duplicate_reason"),
        F.lit(1.0).alias("similarity_score"),
        "composite_join_key",
    )
    repost_duplicates = compared.filter(F.col("duplicate_reason").isNotNull()).select(
        "posting_key",
        F.col("previous_posting_key").alias("canonical_posting_key"),
        "duplicate_reason",
        F.col("description_similarity").alias("similarity_score"),
        "composite_join_key",
    )
    duplicates = delivery_duplicates.unionByName(repost_duplicates)
    canonical = compared.filter(F.col("duplicate_reason").isNull()).drop(
        "previous_posting_key",
        "previous_content_hash",
        "previous_description",
        "previous_posted_at",
        "description_similarity",
        "days_since_previous",
        "duplicate_reason",
    )
    return canonical, duplicates


def extract_skill_matches(
    spark: SparkSession,
    canonical: DataFrame,
    taxonomy_path: str,
    minimum_canonical_skills: int,
) -> DataFrame:
    from pyspark.ml.feature import NGram, RegexTokenizer
    from pyspark.sql import functions as F

    taxonomy = (
        spark.read.option("header", True).csv(taxonomy_path)
        .select("canonical_skill", "alias", "category")
        .dropna()
        .withColumn("canonical_skill", _normalized(F.col("canonical_skill")))
        .withColumn("alias_normalized", _normalized(F.col("alias")))
        .dropDuplicates(["canonical_skill", "alias_normalized"])
    )
    canonical_skill_count = taxonomy.select("canonical_skill").distinct().count()
    if canonical_skill_count < minimum_canonical_skills:
        raise ValueError(
            f"taxonomy has {canonical_skill_count} canonical skills; "
            f"minimum is {minimum_canonical_skills}"
        )

    tokenizer = RegexTokenizer(
        inputCol="description_normalized",
        outputCol="tokens",
        pattern=r"\s+",
        gaps=True,
        minTokenLength=1,
    )
    terms = tokenizer.transform(canonical)
    term_columns = ["tokens"]
    for size in (2, 3, 4):
        output = f"ngrams_{size}"
        terms = NGram(n=size, inputCol="tokens", outputCol=output).transform(terms)
        term_columns.append(output)

    terms = terms.select(
        "posting_key",
        F.explode(F.array_distinct(F.flatten(F.array(*[F.col(c) for c in term_columns])))).alias(
            "alias_normalized"
        ),
    )
    return (
        terms.join(F.broadcast(taxonomy), "alias_normalized", "inner")
        .select(
            "posting_key",
            "canonical_skill",
            "category",
            F.col("alias_normalized").alias("matched_alias"),
        )
        .dropDuplicates(["posting_key", "canonical_skill"])
    )


def partition_profile(frame: DataFrame) -> dict[str, float | int]:
    counts = frame.rdd.mapPartitionsWithIndex(
        lambda index, rows: [(index, sum(1 for _ in rows))]
    ).collect()
    values = [count for _, count in counts]
    total = sum(values)
    non_empty = [count for count in values if count > 0]
    maximum = max(values, default=0)
    mean = total / len(values) if values else 0.0
    return {
        "partition_count": len(values),
        "non_empty_partitions": len(non_empty),
        "max_partition_rows": maximum,
        "mean_partition_rows": round(mean, 3),
        "skew_ratio": round(maximum / mean, 3) if mean else 0.0,
    }
