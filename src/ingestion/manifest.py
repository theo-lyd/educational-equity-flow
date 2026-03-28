"""Manifest utilities for incremental ingestion behavior."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def file_fingerprint(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "sha256": digest,
        "size_bytes": path.stat().st_size,
        "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
    }


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"generated_utc": None, "files": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def should_process(path: Path, manifest: dict[str, Any], force: bool = False) -> bool:
    if force:
        return True
    entry = manifest.get("files", {}).get(path.name)
    if not entry:
        return True
    return entry.get("sha256") != file_fingerprint(path)["sha256"]


def update_manifest_entry(
    manifest: dict[str, Any], path: Path, row_count: int, output_paths: list[str], dataset: str
) -> None:
    manifest.setdefault("files", {})
    fp = file_fingerprint(path)
    manifest["files"][path.name] = {
        **fp,
        "row_count": row_count,
        "dataset": dataset,
        "output_paths": output_paths,
        "ingested_utc": datetime.now(UTC).isoformat(),
    }
    manifest["generated_utc"] = datetime.now(UTC).isoformat()


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
