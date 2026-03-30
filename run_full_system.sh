#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

if [[ ! -d ".venv" ]]; then
  echo "[setup] Creating virtual environment and installing dependencies..."
  make setup-venv
fi

echo "[setup] Ensuring dependencies are up to date..."
make install

echo "[pipeline] Running ingestion..."
make ingest

echo "[pipeline] Building dbt models..."
make dbt-run

echo "[pipeline] Running dbt tests..."
make dbt-test

echo "[pipeline] Running dbt snapshots..."
make dbt-snapshot

echo "[ml] Running clustering and forecasting..."
make ml-run

echo "[quality] Running governance checks..."
make quality-check

echo "[app] Launching full dashboard at http://localhost:8501 ..."
make app
