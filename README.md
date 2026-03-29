# educational-equity-flow
An end-to-end Analytics Engineering system tracking student success and talent leakage in the German education system. Built with DuckDB, dbt, and Python to harmonize federal statistics into actionable policy insights

## Phase 02 Quickstart

Prerequisite: Python 3.11+

Default (pyproject-first, recommended):

```bash
make setup-venv
make ingest
make dbt-run
make test
make app
```

Alternative (requirements-first):

```bash
make setup-venv-req
make ingest
make dbt-run
make test
make app
```

Important: pick one setup path (`setup-venv` or `setup-venv-req`). Do not run both in sequence for the same environment.

Notes:
- `make ingest` runs the Phase 04 Bronze ingestion and writes `warehouse/artifacts/ingest_bronze.json`.
- Bronze output is written as partitioned parquet under `data/bronze/dataset=<dataset>/year=<year>/`.
- Incremental/idempotent behavior is tracked in `data/bronze/ingestion_manifest.json`.
- `make ci-seed-bronze` writes synthetic Bronze fixtures for CI so workflows can run without tracked raw source files.
- `make dbt-run` builds Silver dbt models.
- `make dbt-test` runs dbt model tests.
- `make dbt-snapshot` captures SCD Type 2 district-boundary history snapshots.
- `make ml-run` executes Phase 07 clustering and forecasting artifact generation.
- `make quality-check` executes Phase 08 quality/governance checks and writes `warehouse/artifacts/phase08_quality_report.json`.

## CI Workflows (Phase 09)

- `.github/workflows/ci-pr.yml`: pull-request slim checks (lint, pytest, dbt parse/compile).
- `.github/workflows/pipeline-master.yml`: full push-to-master pipeline (CI seed, dbt run/test, quality checks, pytest, artifacts).
- `.github/workflows/freshness-alert.yml`: weekly scheduled freshness monitoring with report artifact upload.

## Project Execution Guide

- Master guide: `docs/EXECUTION_GUIDE.md`
- Phase docs: `docs/phases/`

### Phase Files

- `docs/phases/PHASE_01_SCOPE_FREEZE.md`
- `docs/phases/PHASE_02_FOUNDATION.md`
- `docs/phases/PHASE_03_DATA_PROFILING.md`
- `docs/phases/PHASE_04_BRONZE_INGESTION.md`
- `docs/phases/PHASE_05_SILVER_DBT.md`
- `docs/phases/PHASE_06_GOLD_MARTS.md`
- `docs/phases/PHASE_07_ML_FORECASTING.md`
- `docs/phases/PHASE_08_QUALITY_GOVERNANCE.md`
- `docs/phases/PHASE_09_ORCHESTRATION_CICD.md`
- `docs/phases/PHASE_10_DASHBOARD_DEFENSE.md`
