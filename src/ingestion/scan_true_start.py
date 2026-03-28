"""Detect header/data start positions in metadata-heavy CSV exports."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class ScanResult:
    header_index: int
    data_start_index: int


def scan_true_start(lines: list[str], delimiter: str = ";") -> ScanResult:
    header_index = 0
    for i, line in enumerate(lines):
        low = line.lower()
        if "jahr" in low and delimiter in line:
            header_index = i
        if "geschlecht" in low and delimiter in line:
            header_index = min(header_index or i, i)
            break
        if line.count(delimiter) >= 5 and i > 0:
            header_index = i
            break

    year_re = re.compile(r"\b(19|20)\d{2}\b")
    ags_re = re.compile(r";\d{5};")
    data_start = header_index + 1
    for i in range(header_index + 1, len(lines)):
        line = lines[i]
        if not line.strip():
            continue
        if year_re.search(line) or ags_re.search(line):
            data_start = i
            break

    return ScanResult(header_index=header_index, data_start_index=data_start)
