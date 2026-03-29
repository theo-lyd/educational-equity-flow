"""Normalization helpers for Phase 04 ingestion."""

from __future__ import annotations

import re
from typing import Any

QUALITY_MARKERS = {"-", ".", "x", "X", "e", ""}


def normalize_ags(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in QUALITY_MARKERS:
        return None
    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    return digits.zfill(5)


def normalize_label(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("dar.", "darunter")
    text = re.sub(r"\s+", " ", text)
    return text


def parse_numeric(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text in QUALITY_MARKERS:
        return None

    multiplier = 1.0
    if text.endswith("Mio"):
        multiplier = 1_000_000.0
        text = text[:-3].strip()
    elif text.endswith("K"):
        multiplier = 1_000.0
        text = text[:-1].strip()

    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def infer_quality(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value).strip()
    if text in QUALITY_MARKERS:
        return text or "-"
    return "ok"
