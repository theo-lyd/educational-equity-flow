"""Minimal dbt command wrapper used during early project setup."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run dbt commands from the configured project dir.")
    parser.add_argument("command", nargs="?", default="run", choices=["run", "test"])
    return parser


def run_dbt(command: str, dbt_dir: str | None = None) -> int:
    project_dir = Path(dbt_dir or os.getenv("DBT_PROJECT_DIR", "dbt"))
    if not project_dir.exists():
        print(f"dbt directory '{project_dir}' not found yet. Skipping for Phase 02.")
        return 0

    project_file = project_dir / "dbt_project.yml"
    if not project_file.exists():
        print(
            f"{project_file} is missing. dbt project will be added in a later phase; skipping now."
        )
        return 0

    cmd = ["dbt", command]
    completed = subprocess.run(cmd, cwd=project_dir, check=False)
    return completed.returncode


def main() -> int:
    args = build_parser().parse_args()
    code = run_dbt(command=args.command)
    if code == 0:
        print(f"dbt wrapper finished for command '{args.command}'.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
