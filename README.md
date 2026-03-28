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
- `make ingest` runs a baseline smoke ingestion entrypoint and writes `warehouse/artifacts/ingest_smoke.json`.
- `make dbt-run` is wired and will no-op until dbt project files are implemented in later phases.

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
