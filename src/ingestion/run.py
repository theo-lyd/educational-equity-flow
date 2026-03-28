"""Phase 02 ingestion entrypoint.

This module provides a stable command interface early in the project lifecycle.
It performs a smoke run and writes a small artifact proving the command executed.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a baseline ingestion smoke command.")
    parser.add_argument("--source", default="data/raw", help="Path to raw data directory")
    parser.add_argument("--target", default="data/bronze", help="Path to bronze output directory")
    return parser


def run_smoke(source: str, target: str) -> dict[str, object]:
    source_path = Path(source)
    target_path = Path(target)
    target_path.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(
        str(p.relative_to(source_path)) for p in source_path.rglob("*") if p.is_file()
    ) if source_path.exists() else []

    artifact_dir = Path("warehouse") / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {
        "run_type": "phase_02_smoke",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "source": str(source_path),
        "target": str(target_path),
        "raw_file_count": len(raw_files),
    }

    with (artifact_dir / "ingest_smoke.json").open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    return payload


def main() -> int:
    args = build_parser().parse_args()
    result = run_smoke(source=args.source, target=args.target)
    print(
        "Ingestion smoke run complete:",
        f"source={result['source']}",
        f"target={result['target']}",
        f"raw_file_count={result['raw_file_count']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
