# Make Commands Used In This Project

Last updated: 2026-03-30
Scope: Project entrypoint commands from Makefile for setup, pipeline, validation, and app runtime.

## How To Read This File

For each command, this guide explains:
- What it is used for
- When to use it
- Where to run it
- How it works
- Recommended tags/options (flags/variables) and why
- Alternatives

---

## 1) Setup Virtual Environment (pyproject path)

Command:

```bash
make setup-venv
```

Used for:
- Create .venv and install dev dependencies from project metadata.

When to use:
- First-time setup on a machine

Where to use:
- Repository root

How it works:
- Creates virtual environment and runs pip install -e .[dev].

Tags/options and why:
- No extra flags usually needed

Alternatives:
- make setup-venv-req (requirements-based setup)

---

## 2) Setup Virtual Environment (requirements path)

Command:

```bash
make setup-venv-req
```

Used for:
- Create .venv and install from requirements-dev.txt.

When to use:
- Environments preferring requirements pin path

Where to use:
- Repository root

How it works:
- Creates .venv and installs dependency list from requirements file.

Tags/options and why:
- Choose one setup path only for consistency

Alternatives:
- make setup-venv

---

## 3) Install/Refresh Dependencies

Command:

```bash
make install
```

Used for:
- Update pip and reinstall project dependencies in active interpreter context.

When to use:
- After dependency changes
- In CI bootstrap

Where to use:
- Repository root

How it works:
- Uses configured PYTHON variable (prefers .venv/bin/python if available).

Tags/options and why:
- Override interpreter if needed:
  - make install PYTHON=python3.12

Alternatives:
- .venv/bin/python -m pip install -e .[dev]

---

## 4) Lint

Command:

```bash
make lint
```

Used for:
- Run static lint checks across src, tests, app.

When to use:
- Before commits/PRs
- In CI quality gates

Where to use:
- Repository root

How it works:
- Executes ruff check over target directories.

Tags/options and why:
- Keep as non-mutating check; use direct ruff --fix intentionally when needed

Alternatives:
- .venv/bin/python -m ruff check src tests app

---

## 5) Format

Command:

```bash
make format
```

Used for:
- Apply Black formatting to source/tests/app.

When to use:
- Before lint and commit

Where to use:
- Repository root

How it works:
- Executes black across key project directories.

Tags/options and why:
- Project-level consistency and diff hygiene

Alternatives:
- .venv/bin/python -m black src tests app

---

## 6) Run Tests

Command:

```bash
make test
```

Used for:
- Execute full pytest suite.

When to use:
- Before merge/release
- After feature or docs-linked behavior changes

Where to use:
- Repository root

How it works:
- Runs pytest through project interpreter context.

Tags/options and why:
- Use targeted pytest files for faster local loops when needed

Alternatives:
- .venv/bin/python -m pytest

---

## 7) Ingest Raw Data To Bronze

Command:

```bash
make ingest
```

Used for:
- Run ingestion pipeline from raw sources to bronze outputs.

When to use:
- New raw data
- Clean rebuild of data pipeline

Where to use:
- Repository root

How it works:
- Invokes src.ingestion.run with source and target arguments.

Tags/options and why:
- Managed internally by Make target for consistency

Alternatives:
- .venv/bin/python -m src.ingestion.run --source data/raw --target data/bronze

---

## 8) Profile Raw Sources

Command:

```bash
make profile-phase03
```

Used for:
- Generate profiling artifacts for raw-source analysis.

When to use:
- Data contract/schema validation cycles

Where to use:
- Repository root

How it works:
- Runs src.profiling.profile_raw_sources with configured input/output directories.

Tags/options and why:
- Output path fixed to docs/phase_03/artifacts for traceability

Alternatives:
- Direct python -m invocation with custom paths

---

## 9) Build dbt Models

Command:

```bash
make dbt-run
```

Used for:
- Materialize dbt models in DuckDB warehouse.

When to use:
- After ingestion and before app/quality checks

Where to use:
- Repository root

How it works:
- Calls dbt runner wrapper with run action.

Tags/options and why:
- DBT_THREADS=1 recommended in CI for deterministic low-resource behavior:
  - DBT_THREADS=1 make dbt-run

Alternatives:
- dbt run (direct CLI)

---

## 10) Run dbt Tests

Command:

```bash
make dbt-test
```

Used for:
- Validate dbt model contracts/relationships.

When to use:
- Immediately after make dbt-run

Where to use:
- Repository root

How it works:
- Calls dbt runner wrapper with test action.

Tags/options and why:
- DBT_THREADS=1 can align runtime behavior with CI

Alternatives:
- dbt test

---

## 11) Run dbt Snapshots

Command:

```bash
make dbt-snapshot
```

Used for:
- Persist SCD-style historical dimensions.

When to use:
- Snapshot refresh cycles and historical dimension validation

Where to use:
- Repository root

How it works:
- Calls dbt runner wrapper with snapshot action.

Tags/options and why:
- Keep sequence after model build for consistency

Alternatives:
- dbt snapshot

---

## 12) Run ML Pipeline

Command:

```bash
make ml-run
```

Used for:
- Generate clustering and forecasting artifacts.

When to use:
- After dbt layer is updated

Where to use:
- Repository root

How it works:
- Executes src.ml.run_all module.

Tags/options and why:
- No standard flags required in current Make abstraction

Alternatives:
- .venv/bin/python -m src.ml.run_all

---

## 13) Run Quality Gates

Command:

```bash
make quality-check
```

Used for:
- Execute governance/freshness/data-quality checks.

When to use:
- Before release or dashboard demos

Where to use:
- Repository root

How it works:
- Runs src.quality.run_checks and writes artifact report.

Tags/options and why:
- Direct module mode allows custom freshness thresholds when needed

Alternatives:
- .venv/bin/python -m src.quality.run_checks

---

## 14) Seed CI Bronze Fixtures

Command:

```bash
make ci-seed-bronze
```

Used for:
- Populate synthetic bronze data for CI where raw files are unavailable.

When to use:
- CI workflows and local CI parity tests

Where to use:
- Repository root

How it works:
- Runs src.tools.ci_seed_bronze with target directory.

Tags/options and why:
- Keep target stable for workflow consistency

Alternatives:
- Direct python module invocation

---

## 15) Launch Application

Command:

```bash
make app
```

Used for:
- Start Streamlit dashboard including all implemented features.

When to use:
- Local stakeholder demos and analyst sessions

Where to use:
- Repository root

How it works:
- Runs python -m streamlit run app/main.py through project interpreter.

Tags/options and why:
- This target avoids global streamlit path issues by using project interpreter

Alternatives:
- .venv/bin/python -m streamlit run app/main.py
- ./run_full_system.sh for full pipeline + launch

---

## Recommended End-To-End Command Sequences

## A) First setup and full run

```bash
make setup-venv
make ingest
make dbt-run
make dbt-test
make dbt-snapshot
make ml-run
make quality-check
make app
```

## B) Fast day-to-day dev cycle

```bash
make install
make lint
make test
make app
```

## C) CI-parity local check

```bash
make ci-seed-bronze
DBT_THREADS=1 make dbt-run
DBT_THREADS=1 make dbt-test
make quality-check
make test
```
