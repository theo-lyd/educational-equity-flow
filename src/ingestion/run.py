"""Phase 04 bronze ingestion entrypoint."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from .csv_ingestor import ingest_csv
from .manifest import load_manifest, save_manifest, should_process, update_manifest_entry
from .xlsx_ingestor import ingest_xlsx
from .xml_ingestor import ingest_xml

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 04 Bronze ingestion.")
    parser.add_argument("--source", default="data/raw", help="Path to raw data directory")
    parser.add_argument("--target", default="data/bronze", help="Path to bronze output directory")
    parser.add_argument(
        "--manifest",
        default=None,
        help="Optional manifest path (defaults to <target>/ingestion_manifest.json)",
    )
    parser.add_argument("--force", action="store_true", help="Force reprocessing all files")
    return parser


def _discover_sources(source_path: Path) -> list[Path]:
    if not source_path.exists():
        return []
    supported = {".csv", ".xml", ".xlsx"}
    return sorted(
        [p for p in source_path.rglob("*") if p.is_file() and p.suffix.lower() in supported]
    )


def _ingest_file(path: Path) -> pl.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return ingest_csv(path)
    if suffix == ".xml":
        return ingest_xml(path)
    if suffix == ".xlsx":
        return ingest_xlsx(path)
    raise ValueError(f"Unsupported source file type: {path}")


def _normalize_bronze_frame(df: pl.DataFrame) -> pl.DataFrame:
    out = df
    for col in BRONZE_COLUMNS:
        if col not in out.columns:
            out = out.with_columns(pl.lit(None).alias(col))

    return out.select(BRONZE_COLUMNS).with_columns(
        pl.col("dataset").cast(pl.Utf8, strict=False),
        pl.col("source_file").cast(pl.Utf8, strict=False),
        pl.col("year").cast(pl.Utf8, strict=False),
        pl.col("ags").cast(pl.Utf8, strict=False),
        pl.col("region").cast(pl.Utf8, strict=False),
        pl.col("dimension_1").cast(pl.Utf8, strict=False),
        pl.col("dimension_2").cast(pl.Utf8, strict=False),
        pl.col("dimension_3").cast(pl.Utf8, strict=False),
        pl.col("metric_name").cast(pl.Utf8, strict=False),
        pl.col("raw_value").cast(pl.Utf8, strict=False),
        pl.col("value").cast(pl.Float64, strict=False),
        pl.col("quality").cast(pl.Utf8, strict=False),
    )


def _write_partitioned(df: pl.DataFrame, target: Path, source_stem: str) -> list[str]:
    written: list[str] = []
    years = sorted(set(df.get_column("year").fill_null("unknown").to_list()))
    for year in years:
        year_label = year if year else "unknown"
        part = df.filter(pl.col("year").fill_null("unknown") == year_label)
        dataset = str(part[0, "dataset"] or source_stem)
        out_dir = target / f"dataset={dataset}" / f"year={year_label}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{source_stem}.parquet"
        part.write_parquet(out_path, compression="zstd")
        written.append(str(out_path))
    return written


def _clean_dataset_output(target: Path, dataset: str) -> None:
    dataset_dir = target / f"dataset={dataset}"
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)


def run_ingestion(
    source: str,
    target: str,
    manifest_path: str | None = None,
    force: bool = False,
) -> dict[str, object]:
    source_path = Path(source)
    target_path = Path(target)
    target_path.mkdir(parents=True, exist_ok=True)

    sources = _discover_sources(source_path)
    manifest_file = (
        Path(manifest_path) if manifest_path else target_path / "ingestion_manifest.json"
    )
    manifest = load_manifest(manifest_file)

    processed_files: list[str] = []
    skipped_files: list[str] = []
    total_rows = 0

    for src in sources:
        if not should_process(src, manifest=manifest, force=force):
            skipped_files.append(str(src.relative_to(source_path)))
            continue

        frame = _normalize_bronze_frame(_ingest_file(src))
        _clean_dataset_output(target_path, src.stem)
        written_paths = _write_partitioned(frame, target_path, source_stem=src.stem)
        update_manifest_entry(
            manifest=manifest,
            path=src,
            row_count=frame.height,
            output_paths=written_paths,
            dataset=src.stem,
        )
        processed_files.append(str(src.relative_to(source_path)))
        total_rows += frame.height

    save_manifest(manifest_file, manifest)

    artifact_dir = Path("warehouse") / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {
        "run_type": "phase_04_bronze_ingestion",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "source": str(source_path),
        "target": str(target_path),
        "manifest": str(manifest_file),
        "raw_file_count": len(sources),
        "processed_file_count": len(processed_files),
        "skipped_file_count": len(skipped_files),
        "processed_files": processed_files,
        "skipped_files": skipped_files,
        "rows_written": total_rows,
        "force": force,
    }

    with (artifact_dir / "ingest_bronze.json").open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    return payload


def run_smoke(source: str, target: str) -> dict[str, object]:
    """Backward-compatible alias used by earlier tests."""
    return run_ingestion(source=source, target=target)


def main() -> int:
    args = build_parser().parse_args()
    result = run_ingestion(
        source=args.source,
        target=args.target,
        manifest_path=args.manifest,
        force=args.force,
    )
    print(
        "Bronze ingestion complete:",
        f"source={result['source']}",
        f"target={result['target']}",
        f"raw_file_count={result['raw_file_count']}",
        f"processed={result['processed_file_count']}",
        f"skipped={result['skipped_file_count']}",
        f"rows_written={result['rows_written']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
