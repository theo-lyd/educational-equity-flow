"""CSV ingestion to normalized Bronze records."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import polars as pl

from .normalizers import infer_quality, normalize_ags, normalize_label, parse_numeric
from .scan_true_start import scan_true_start


def _read_lines(path: Path, encoding: str = "iso-8859-1") -> list[str]:
    with path.open("r", encoding=encoding, errors="replace") as fh:
        return [line.rstrip("\n") for line in fh]


def _build_metric_names(header_rows: list[list[str]], width: int) -> list[str]:
    metric_names: list[str] = []
    for col in range(width):
        parts: list[str] = []
        for row in header_rows:
            if col < len(row):
                value = normalize_label(row[col])
                if value and value not in {"Anzahl", "WS 2023/24"}:
                    parts.append(value)
        metric = " | ".join(dict.fromkeys(parts))
        metric_names.append(metric if metric else f"col_{col}")
    return metric_names


def ingest_statistical_csv(path: Path) -> pl.DataFrame:
    lines = _read_lines(path)
    scan = scan_true_start(lines, delimiter=";")

    header_rows_raw = []
    for i in range(max(scan.data_start_index - 3, 0), scan.data_start_index):
        header_rows_raw.append(lines[i].split(";"))

    data_rows = [
        row
        for row in csv.reader(lines[scan.data_start_index :], delimiter=";")
        if row and any(cell.strip() for cell in row)
    ]

    width = max((len(r) for r in data_rows), default=0)
    header_rows = [r + [""] * (width - len(r)) for r in header_rows_raw]
    metric_names = _build_metric_names(header_rows, width)

    header_text = " ".join(" ".join(r) for r in header_rows)
    default_year_match = re.search(r"\b(19|20)\d{2}\b", header_text)
    default_year = default_year_match.group(0) if default_year_match else None

    records: list[dict[str, object]] = []
    for row in data_rows:
        row = row + [""] * (width - len(row))
        first = row[0].strip() if row else ""
        has_row_year = first.isdigit() and len(first) == 4

        if has_row_year:
            year = first
            ags = normalize_ags(row[1] if len(row) > 1 else None)
            region = normalize_label(row[2] if len(row) > 2 else None)
            dimension_1 = None
            metric_start = 3
        else:
            year = default_year
            ags = normalize_ags(row[0] if len(row) > 0 else None)
            region = normalize_label(row[1] if len(row) > 1 else None)
            dimension_1 = normalize_label(row[2] if len(row) > 2 else None)
            metric_start = 3

        for idx in range(metric_start, width):
            raw = row[idx].strip()
            value = parse_numeric(raw)
            records.append(
                {
                    "dataset": path.stem,
                    "source_file": path.name,
                    "year": year,
                    "ags": ags,
                    "region": region,
                    "dimension_1": dimension_1,
                    "dimension_2": None,
                    "dimension_3": None,
                    "metric_name": metric_names[idx],
                    "raw_value": raw,
                    "value": value,
                    "quality": infer_quality(raw),
                }
            )

    return pl.DataFrame(records)


def ingest_flat_csv(path: Path) -> pl.DataFrame:
    df = pl.read_csv(path, separator=";", encoding="iso8859-1", ignore_errors=True)
    for col in df.columns:
        if df[col].dtype == pl.String:
            df = df.with_columns(pl.col(col).str.strip_chars())

    def _series(name: str) -> pl.Series:
        if name in df.columns:
            return df.get_column(name).cast(pl.Utf8, strict=False)
        return pl.Series(name=name, values=[None] * df.height, dtype=pl.Utf8)

    raw_value = _series("value")
    quality = raw_value.map_elements(infer_quality, return_dtype=pl.Utf8)
    value = raw_value.map_elements(parse_numeric, return_dtype=pl.Float64)

    return pl.DataFrame(
        {
            "dataset": [path.stem] * df.height,
            "source_file": [path.name] * df.height,
            "year": _series("time"),
            "ags": _series("1_variable_attribute_code").map_elements(
                normalize_ags, return_dtype=pl.Utf8
            ),
            "region": _series("1_variable_attribute_label").map_elements(
                normalize_label, return_dtype=pl.Utf8
            ),
            "dimension_1": _series("2_variable_attribute_code"),
            "dimension_2": _series("3_variable_attribute_code"),
            "dimension_3": _series("4_variable_attribute_code"),
            "metric_name": _series("value_variable_label").map_elements(
                normalize_label, return_dtype=pl.Utf8
            ),
            "raw_value": raw_value,
            "value": value,
            "quality": quality,
        }
    )


def ingest_csv(path: Path) -> pl.DataFrame:
    if path.name.endswith("_flat.csv"):
        return ingest_flat_csv(path)
    return ingest_statistical_csv(path)
