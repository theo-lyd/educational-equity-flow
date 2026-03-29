# Phase 08: Data Quality, Governance & SLAs

Status: Completed (2026-03-29)

## 5W1H (Who, What, When, Where, Why, How)

### Who
- Project maintainer and Copilot coding agent implemented and validated Phase 08 safeguards.
- Primary consumers: orchestration/CI maintainers (Phase 09) and dashboard/review stakeholders requiring trustable outputs.

### What
- Implemented executable quality/governance checks combining:
	- Great Expectations-style validation on model outputs,
	- referential integrity checks,
	- freshness SLA checks with warning/fail thresholds,
	- operational minimum-volume checks.
- Added CI workflow to run dbt + quality + pytest gates on push/PR.
- Added test coverage for quality checker behavior.

### When
- Implemented and validated on 2026-03-29 after Phase 07 artifact pipeline completion.

### Where
- Quality checker implementation:
	- `src/quality/run_checks.py`
	- `src/quality/__init__.py`
- Test coverage:
	- `tests/test_phase08_quality.py`
- Command wiring:
	- `Makefile` (`quality-check`)
	- `README.md`
- CI quality gate:
	- `.github/workflows/quality-gates.yml`
- Artifact output:
	- `warehouse/artifacts/phase08_quality_report.json`

### Why
- Modeling accuracy alone is insufficient for product-grade analytics.
- Teams need automated detection of integrity/freshness regressions before release.
- Governance reports provide observability and auditability for thesis/policy usage.

### How
- Added a Python quality runner that connects to DuckDB and executes grouped check packs.
- Added explicit thresholds (warn/fail) for freshness and minimum expected data volume.
- Wrote JSON quality report with status/fail/warn counts and check details.
- Added CI workflow that enforces dbt + quality + tests as release gates.

## Objective(s)
- Enforce reliability, integrity, and freshness as product-grade guarantees.

## Deliverable(s)
- Great Expectations suites, dbt test gates, freshness SLA checks.

### Delivered assets
- Programmatic Great Expectations checks over Gold outputs.
- Referential integrity and freshness SLA checks with configurable thresholds.
- Quality report artifact generation for observability.
- CI workflow that executes quality gates automatically.

## Concrete Tasks
- Implement GE checks for value ranges, integrity, and schema expectations.
- Add referential integrity checks across school/university entities.
- Implement freshness checks on Stichtag.
- Define warning vs fail quality thresholds.
- Wire quality checks into CI pipeline.

## Completion Checklist
- [x] Implement Great Expectations checks for core output validity.
- [x] Add referential integrity checks across critical marts/dimensions.
- [x] Implement freshness checks with warn/fail thresholds.
- [x] Add operational minimum-volume check.
- [x] Emit structured quality report artifact.
- [x] Add command-level runner (`make quality-check`).
- [x] Add test coverage for checker behavior.
- [x] Wire quality gates into CI workflow.

## Done Criteria
- Quality failures are detected and block critical releases.
- SLA checks are automated and observable.

Done criteria outcome:
- Achieved. Quality checks now return non-zero on failure and are wired into CI job execution.

## Validation Evidence
- End-to-end command validation:
	- `make dbt-run` PASS
	- `make dbt-test` PASS (17 tests)
	- `make quality-check` PASS (`status=pass`, `fails=0`, `warns=0`)
	- `make test` PASS (10 tests)
- Artifact evidence:
	- `warehouse/artifacts/phase08_quality_report.json`
- CI gating added:
	- `.github/workflows/quality-gates.yml`

## Quality Gates Implemented

### Great Expectations checks
- `ags` not null
- `ags` unique
- `end_to_end_completion_rate` in expected bounds (mostly threshold)
- `compounded_transition_rate` in expected bounds (mostly threshold)

### Referential integrity checks
- `gold_stage_funnel.ags` must exist in `int_district_current.ags`
- `gold_transition_rates.ags` must exist in `gold_stage_funnel.ags`

### Freshness SLA checks
- Stage 3 latest year evaluated against warn/fail thresholds.
- Stage 5 latest year evaluated against warn/fail thresholds.
- Status levels: `pass`, `warn`, `fail`.

### Operational checks
- Minimum expected transition row count threshold.

## Threshold Policy (Initial)
- `freshness_warn_years`: 3
- `freshness_fail_years`: 6
- `min_cluster_rows`: 100

These are intentionally conservative defaults and should be tuned with domain owners as data cadence becomes clearer.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| GE ecosystem emits third-party deprecation warnings during pytest | Dependency stack (`pyparsing`, `marshmallow`) warnings from installed package versions | Warning noise may obscure project-specific warnings | Kept warnings non-fatal and validated checker outputs + status logic | Revisit dependency pinning/upgrade path in maintenance cycle; keep warning budget monitoring |
| Freshness semantics differ across stage sources | Stage datasets have different update cadences and historical depth | False-positive SLA failures if thresholds are too strict | Implemented configurable warn/fail thresholds and report-level visibility | Tune thresholds periodically with source owners and observed refresh cadence |

## Residual Risks
- Current SLA thresholds are static and may need periodic recalibration.
- CI workflow assumes raw/bronze prerequisites are available in runner context.
- Great Expectations API/version changes may require minor checker updates.

## Handoff Readiness (to Phase 09)
- Quality and governance checks are executable locally and in CI.
- Fail/warn observability is available via structured JSON artifacts.
- Pipeline is ready for orchestration hardening and broader CI/CD rollout.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| None yet | - | - | - | - |
