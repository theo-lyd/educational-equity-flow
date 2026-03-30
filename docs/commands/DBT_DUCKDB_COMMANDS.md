# dbt and DuckDB Commands Used In This Project

Last updated: 2026-03-30
Scope: Commands used for modeling, testing, snapshots, parse/compile checks, and warehouse inspection.

## How To Read This File

Each command includes:
- What it is used for
- When to use it
- Where to run it
- How it works
- Recommended tags/options (flags) and why
- Alternatives

---

## A) dbt Commands

## 1) Install dbt Package Dependencies

Command:

```bash
cd dbt
dbt deps --profiles-dir .
```

Used for:
- Download dbt package dependencies.

When to use:
- Initial setup
- After modifying packages.yml

Where to use:
- dbt project directory

How it works:
- Resolves package references into dbt_packages folder.

Tags/options and why:
- --profiles-dir . ensures local profile path in CI/project context

Alternatives:
- Use project wrapper in src.tools.dbt_runner if standardized there

---

## 2) Parse Project

Command:

```bash
cd dbt
dbt parse --profiles-dir .
```

Used for:
- Validate model graph and syntax without running SQL.

When to use:
- Fast PR checks

Where to use:
- dbt project directory

How it works:
- Builds internal manifest and catches compile/graph issues quickly.

Tags/options and why:
- --profiles-dir . keeps profile resolution deterministic in CI

Alternatives:
- dbt compile (heavier but renders SQL)

---

## 3) Compile Project

Command:

```bash
cd dbt
dbt compile --profiles-dir .
```

Used for:
- Render SQL for all selected models without executing.

When to use:
- SQL review and CI slim checks

Where to use:
- dbt project directory

How it works:
- Resolves Jinja/macros/refs and writes compiled SQL into target.

Tags/options and why:
- --profiles-dir . for explicit profile location

Alternatives:
- dbt build for full execution+tests

---

## 4) Run Models

Project wrapper command used in this repo:

```bash
make dbt-run
```

Equivalent core dbt behavior:

```bash
dbt run
```

Used for:
- Execute model SQL and materialize tables/views.

When to use:
- After ingestion updates
- Before app launch and quality checks

Where to use:
- Repository root via Make target (recommended)

How it works:
- Runs model DAG in dependency order.

Tags/options and why:
- DBT_THREADS=1 used in CI for deterministic low-resource runs

Alternatives:
- dbt build (run + test in one command)

---

## 5) Run dbt Tests

Project wrapper command:

```bash
make dbt-test
```

Equivalent core dbt command:

```bash
dbt test
```

Used for:
- Validate model-level quality constraints.

When to use:
- After dbt run and before release

Where to use:
- Repository root via Make target

How it works:
- Executes generic and singular test queries.

Tags/options and why:
- Keep run/test sequence paired for reliable feedback

Alternatives:
- dbt build for combined execution path

---

## 6) Run Snapshots

Project wrapper command:

```bash
make dbt-snapshot
```

Equivalent core dbt command:

```bash
dbt snapshot
```

Used for:
- Track slowly changing dimensions (historical district boundary state).

When to use:
- On data refresh cycles where dimensional history matters

Where to use:
- Repository root via Make target

How it works:
- Writes versioned historical rows using snapshot strategy.

Tags/options and why:
- Use consistent schedule with model refresh to avoid stale SCD state

Alternatives:
- Manual SCD handling in SQL (higher maintenance)

---

## B) DuckDB Commands

## 7) Interactive DuckDB Session

Command:

```bash
duckdb warehouse/analytics.duckdb
```

Used for:
- Open interactive SQL shell against warehouse.

When to use:
- Debugging data quality and model outputs

Where to use:
- Repository root (or path where DB file exists)

How it works:
- Starts embedded DuckDB CLI connected to file DB.

Tags/options and why:
- Provide explicit DB path to avoid creating accidental new files

Alternatives:
- Python access via duckdb.connect in scripts

---

## 8) One-Off SQL Query

Command pattern:

```bash
duckdb warehouse/analytics.duckdb "SELECT COUNT(*) FROM gold_stage_funnel;"
```

Used for:
- Fast sanity checks in scripts/docs/troubleshooting.

When to use:
- Verify table presence, row counts, specific metrics

Where to use:
- Shell from repository root

How it works:
- Executes SQL string and exits with printed result.

Tags/options and why:
- Keep query simple for scriptable checks in CI/local docs

Alternatives:
- .venv/bin/python -c "import duckdb; ..." for programmable output

---

## 9) Python-Module Wrapper Invocation

Command pattern used by project tooling:

```bash
.venv/bin/python -m src.tools.dbt_runner run
```

Used for:
- Standardized dbt invocation from Python wrapper.

When to use:
- In Make targets and automation where environment handling is centralized

Where to use:
- Repository root

How it works:
- Wrapper maps high-level action to dbt command with project defaults.

Tags/options and why:
- Use explicit interpreter path for environment consistency

Alternatives:
- Direct dbt CLI commands

---

## Recommended Operational Order

For full refresh cycles:
1) make ingest
2) make dbt-run
3) make dbt-test
4) make dbt-snapshot
5) make quality-check
6) make app

Why this order:
- Models depend on freshly ingested data
- Tests validate modeled output before snapshots and app consumption
- Snapshot history stays aligned with current modeled state
