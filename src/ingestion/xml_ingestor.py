"""XML ingestion to normalized Bronze records."""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

import polars as pl

from .normalizers import infer_quality, normalize_ags, parse_numeric


def _parse_coordinate(coord: str) -> dict[str, str]:
    parts = re.findall(r"\[([^\]]+)\]\.\[([^\]]+)\]", coord)
    return {k: v for k, v in parts}


def ingest_xml(path: Path) -> pl.DataFrame:
    records: list[dict[str, object]] = []

    for event, elem in ET.iterparse(path, events=("start",)):
        tag = elem.tag.split("}")[-1]
        if tag != "VALUE":
            continue

        coord = elem.attrib.get("COORDINATE", "")
        parsed = _parse_coordinate(coord)
        raw = elem.attrib.get("ORIG", "")
        quality = elem.attrib.get("QUALITY", "")

        records.append(
            {
                "dataset": path.stem,
                "source_file": path.name,
                "year": parsed.get("JAHR"),
                "ags": normalize_ags(parsed.get("KREISE")),
                "region": None,
                "dimension_1": parsed.get("HS-FG2"),
                "dimension_2": parsed.get("GESINS"),
                "dimension_3": None,
                "metric_name": "HS-W06_bestandene_pruefungen",
                "raw_value": raw,
                "value": parse_numeric(raw),
                "quality": quality if quality else infer_quality(raw),
            }
        )

        elem.clear()

    return pl.DataFrame(records)
