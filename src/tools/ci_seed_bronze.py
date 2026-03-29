"""Create minimal Bronze parquet fixtures for CI dbt/quality checks."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import polars as pl


BRONZE_COLUMNS = [
    "dataset",
    "source_file",
    "year",
    "ags",
    "region",
    "dimension_1",
    "dimension_2",
    "dimension_3",
    "metric_name",
    "raw_value",
    "value",
    "quality",
]

BRONZE_SCHEMA = {
    "dataset": pl.Utf8,
    "source_file": pl.Utf8,
    "year": pl.Utf8,
    "ags": pl.Utf8,
    "region": pl.Utf8,
    "dimension_1": pl.Utf8,
    "dimension_2": pl.Utf8,
    "dimension_3": pl.Utf8,
    "metric_name": pl.Utf8,
    "raw_value": pl.Utf8,
    "value": pl.Float64,
    "quality": pl.Utf8,
}


def _write_rows(base: Path, dataset: str, year: str, rows: list[dict[str, object]]) -> None:
    frame = pl.DataFrame(rows)
    for col in BRONZE_COLUMNS:
        if col not in frame.columns:
            frame = frame.with_columns(pl.lit(None).alias(col))
    frame = frame.select(BRONZE_COLUMNS).cast(BRONZE_SCHEMA, strict=False)

    out_dir = base / f"dataset={dataset}" / f"year={year}"
    out_dir.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(out_dir / f"{dataset}.parquet", compression="zstd")


def seed_bronze(target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    ags_values = [f"{value:05d}" for value in range(10001, 10121)]

    school_rows = []
    stage2_rows = []
    grad_rows = []
    uni_total_rows = []
    uni_group_rows = []
    stage5_rows = []

    for idx, ags in enumerate(ags_values, start=1):
        region = f"Region-{idx}"
        school_rows.append(
            {
                "dataset": "21111-01-03-4",
                "source_file": "21111-01-03-4.xlsx",
                "year": None,
                "ags": ags,
                "region": region,
                "dimension_1": "Insgesamt",
                "metric_name": "7. Klassenstufe",
                "raw_value": str(1000 + idx * 100),
                "value": float(1000 + idx * 100),
                "quality": "ok",
            }
        )
        stage2_rows.append(
            {
                "dataset": "21111-01-03-4",
                "source_file": "21111-01-03-4.xlsx",
                "year": None,
                "ags": ags,
                "region": region,
                "dimension_1": "Insgesamt",
                "metric_name": "11. Jahrgangsstufe / Einführungsphase",
                "raw_value": str(700 + idx * 70),
                "value": float(700 + idx * 70),
                "quality": "ok",
            }
        )
        grad_rows.append(
            {
                "dataset": "21111-02-06-4-B",
                "source_file": "21111-02-06-4-B.csv",
                "year": "2024",
                "ags": ags,
                "region": region,
                "metric_name": "Absolvierende/Abgehende allgemeinbildender Schulen nach dem Abschluss | mit Allgemeiner und fachgebundener Hochschulreife | Insgesamt",
                "raw_value": str(500 + idx * 50),
                "value": float(500 + idx * 50),
                "quality": "ok",
            }
        )
        uni_total_rows.append(
            {
                "dataset": "21311-01-01-4-B",
                "source_file": "21311-01-01-4-B.csv",
                "year": None,
                "ags": ags,
                "region": region,
                "dimension_1": "Insgesamt",
                "metric_name": "Insgesamt",
                "raw_value": str(900 + idx * 90),
                "value": float(900 + idx * 90),
                "quality": "ok",
            }
        )

        population = float(900 + idx * 90)
        intl = max(100.0, population * (0.2 + (idx % 3) * 0.05))
        domestic = population - intl
        uni_group_rows.extend(
            [
                {
                    "dataset": "21311-01-01-4",
                    "source_file": "21311-01-01-4.csv",
                    "year": None,
                    "ags": ags,
                    "region": region,
                    "dimension_1": "Insgesamt",
                    "metric_name": "Insgesamt",
                    "raw_value": str(population),
                    "value": float(population),
                    "quality": "ok",
                },
                {
                    "dataset": "21311-01-01-4",
                    "source_file": "21311-01-01-4.csv",
                    "year": None,
                    "ags": ags,
                    "region": region,
                    "dimension_1": "Insgesamt",
                    "metric_name": "deutsch",
                    "raw_value": str(domestic),
                    "value": float(domestic),
                    "quality": "ok",
                },
                {
                    "dataset": "21311-01-01-4",
                    "source_file": "21311-01-01-4.csv",
                    "year": None,
                    "ags": ags,
                    "region": region,
                    "dimension_1": "Insgesamt",
                    "metric_name": "ausländisch",
                    "raw_value": str(intl),
                    "value": float(intl),
                    "quality": "ok",
                },
            ]
        )

        stage5_rows.extend(
            [
                {
                    "dataset": "21321-01-01-4_flat",
                    "source_file": "21321-01-01-4_flat.csv",
                    "year": "2023",
                    "ags": ags,
                    "region": region,
                    "dimension_1": "INSGESAMT",
                    "dimension_2": "INSGESAMT",
                    "metric_name": "Bestandene Prüfungen",
                    "raw_value": str(400 + idx * 35),
                    "value": float(400 + idx * 35),
                    "quality": "ok",
                },
                {
                    "dataset": "21321-01-01-4_flat",
                    "source_file": "21321-01-01-4_flat.csv",
                    "year": "2023",
                    "ags": ags,
                    "region": region,
                    "dimension_1": "HS-FG01",
                    "dimension_2": "INSGESAMT",
                    "metric_name": "Bestandene Prüfungen",
                    "raw_value": str(100 + idx * 10),
                    "value": float(100 + idx * 10),
                    "quality": "ok",
                },
                {
                    "dataset": "21321-01-01-4_flat",
                    "source_file": "21321-01-01-4_flat.csv",
                    "year": "2023",
                    "ags": ags,
                    "region": region,
                    "dimension_1": "HS-FG02",
                    "dimension_2": "INSGESAMT",
                    "metric_name": "Bestandene Prüfungen",
                    "raw_value": str(120 + idx * 10),
                    "value": float(120 + idx * 10),
                    "quality": "ok",
                },
            ]
        )

    _write_rows(target, "21111-01-03-4", "unknown", school_rows + stage2_rows)
    _write_rows(target, "21111-02-06-4-B", "2024", grad_rows)
    _write_rows(target, "21311-01-01-4-B", "unknown", uni_total_rows)
    _write_rows(target, "21311-01-01-4", "unknown", uni_group_rows)
    _write_rows(target, "21321-01-01-4_flat", "2023", stage5_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Bronze parquet fixture data for CI.")
    parser.add_argument("--target", default="data/bronze", help="Bronze output directory")
    args = parser.parse_args()

    seed_bronze(Path(args.target))
    print(f"CI bronze seed complete: target={args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
