# Phase 05: Silver Layer (dbt Harmonization + SCD)

Status: Completed (2026-03-29)

## 5W1H (Who, What, When, Where, Why, How)

### Who
- Project maintainer and Copilot coding agent implemented and validated dbt Silver assets.
- Primary consumers: Gold mart builders (Phase 06), ML feature engineering (Phase 07), and governance checks (Phase 08).

### What
- Initialized a runnable dbt-duckdb project connected to `warehouse/analytics.duckdb`.
- Implemented Silver staging and intermediate models from Bronze parquet inputs.
- Added reusable AGS normalization macro.
- Added SCD Type 2 snapshot for district boundary history behavior.
- Added dbt tests for key integrity and data-quality constraints.

### When
- Executed and validated on 2026-03-29 immediately after Phase 04 completion.

### Where
- dbt project/config:
	- `dbt/dbt_project.yml`
	- `dbt/profiles.yml`
- Macro:
	- `dbt/macros/normalize_ags.sql`
- Models:
	- `dbt/models/staging/stg_bronze_events.sql`
	- `dbt/models/intermediate/int_metric_facts.sql`
	- `dbt/models/intermediate/int_district_current.sql`
- Model tests:
	- `dbt/models/staging/staging.yml`
	- `dbt/models/intermediate/intermediate.yml`
- Snapshot:
	- `dbt/snapshots/snap_district_boundaries.sql`
- Command wrappers:
	- `src/tools/dbt_runner.py`
	- `Makefile` (`dbt-run`, `dbt-test`, `dbt-snapshot`)

### Why
- Bronze data is normalized but still too raw for stable analytics joins and KPI logic.
- Silver must provide conformed dimensions/typing and a controlled historical view contract.
- dbt assets introduce repeatable transformations, tests, and lineage-ready structure.

### How
- Read Bronze parquet directly using DuckDB `read_parquet(..., hive_partitioning=true)`.
- Standardized AGS via macro (digits-only, canonical 5-char key behavior).
- Built a canonical staging layer (`stg_bronze_events`) and intermediate analytical tables.
- Built current district view and SCD snapshot for historical boundary tracking.
- Executed dbt run/test/snapshot commands to validate functionality.

## Objective(s)
- Build harmonized, historically consistent analytical entities.

## Deliverable(s)
- dbt staging/intermediate models, macros, snapshots, tests.

### Delivered Assets
- Config and environment:
	- `dbt/dbt_project.yml`
	- `dbt/profiles.yml`
- Harmonization macro:
	- `dbt/macros/normalize_ags.sql`
- Silver models:
	- `stg_bronze_events`: canonical staged event grain
	- `int_metric_facts`: conformed metric grain with `cohort_key`
	- `int_district_current`: latest known region mapping per AGS
- SCD history:
	- `snap_district_boundaries`
- Quality gates:
	- not_null, unique, accepted_values tests across staging/intermediate layers

## Concrete Tasks
- Initialize dbt-duckdb project and source definitions.
- Build stg models with standardized naming and types.
- Add AGS standardization macro (zero-padding/normalization to 5).
- Implement conformed dimensions and cohort alignment logic.
- Implement SCD Type 2 snapshots for district boundary changes.
- Add dbt tests (not null, unique, accepted values).

## Done Criteria
- `dbt run`/`dbt test` passes.
- Historical and current boundary views are both supported.

## Validation Evidence
- Build command:
	- `make dbt-run`
	- Result: PASS=3 (1 view + 2 table models)
- Test command:
	- `make dbt-test`
	- Result: PASS=9 tests, WARN=0, ERROR=0
- Snapshot command:
	- `make dbt-snapshot`
	- Result: PASS=1 snapshot (`snap_district_boundaries`)
- Regression safety:
	- `make test` remains green (`6 passed`)

## Completion Checklist
- [x] Initialize dbt project and local profile for DuckDB.
- [x] Build staging model from Bronze parquet.
- [x] Add AGS normalization macro and apply in staging layer.
- [x] Build intermediate conformed metric and district-current models.
- [x] Implement SCD Type 2 snapshot for district boundaries.
- [x] Add and pass dbt tests.
- [x] Validate dbt run/test/snapshot commands through project wrappers.

## Architecture and Data Contract Decisions
- Decision: read Bronze parquet directly in Silver staging.
	- Benefit: zero-copy modeling path and rapid development.
	- Trade-off: model SQL must remain aligned with Bronze partition conventions.
- Decision: central AGS normalization macro in dbt.
	- Benefit: one consistent key policy for all downstream joins.
	- Trade-off: strict normalization can null out malformed keys; quality monitoring required.
- Decision: maintain both current-state district view and SCD snapshot.
	- Benefit: supports present-day reporting and historically correct analysis.
	- Trade-off: snapshot lifecycle/state management becomes part of operations.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| `dbt` command not found from wrapper | Virtual environment executable path was not guaranteed in subprocess PATH | `make dbt-run/test/snapshot` could fail despite installed packages | Updated wrapper to resolve dbt executable from active Python virtualenv (`Path(sys.executable).with_name('dbt')`) | Keep tool wrappers interpreter-aware and avoid PATH assumptions |
| dbt generic test deprecation warning for `accepted_values` | Test config used top-level arguments format deprecated in dbt 1.10+ | Warning noise and future compatibility risk | Migrated test config to `arguments:` block in schema YAML | Track dbt deprecations and update schema/test syntax proactively |

## Residual Risks
- Boundary-change fidelity depends on source label consistency and update cadence.
- Additional conformed dimensions (demographic/subject) may need refinement for Gold marts.
- Snapshot growth management (retention/maintenance) will need orchestration in later phases.

## Handoff Readiness (to Phase 06)
- Silver models are runnable, tested, and snapshot-enabled.
- Conformed metric and district views are available for Gold funnel/transition marts.
- No blocker remains to start Phase 06 mart development.
