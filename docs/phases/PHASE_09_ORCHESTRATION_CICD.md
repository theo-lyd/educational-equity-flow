# Phase 09: Orchestration & CI/CD

## Objective(s)
- Automate ingestion, transformation, testing, and quality checks.

## 5W1H

- What: Implemented CI/CD orchestration with slim PR checks, full master pipeline gates, and scheduled freshness monitoring.
- Why: Ensure every change is validated automatically while keeping PR feedback fast and enforcing stronger release quality on master.
- Who: Data platform engineer (owner), analytics engineer (dbt model/test owner), QA/governance owner (quality thresholds and freshness).
- Where: GitHub Actions workflows under `.github/workflows/` plus existing `make` entrypoints.
- When: Phase 09 execution after governance checks were stabilized in Phase 08.
- How: Added three workflows and a synthetic Bronze seed generator so CI can run without tracked raw source files.

## Deliverable(s)
- GitHub Actions workflows with clear pass/fail gates.

### Implemented Deliverables

- Added `.github/workflows/ci-pr.yml` for pull request slim checks:
	- environment setup,
	- lint (`make lint`),
	- unit/integration tests (`make test`),
	- dbt parse/compile smoke (`dbt parse`, `dbt compile`),
	- artifact upload for dbt parse outputs.
- Added `.github/workflows/pipeline-master.yml` for full push-to-master checks:
	- synthetic Bronze fixture generation (`make ci-seed-bronze`),
	- dbt build/test (`make dbt-run`, `make dbt-test`),
	- governance checks (`make quality-check`),
	- pytest suite (`make test`),
	- artifact upload (`run_results.json`, `manifest.json`, quality report).
- Added `.github/workflows/freshness-alert.yml` for scheduled monitoring:
	- weekly cron plus manual dispatch,
	- fixture seeding + dbt run,
	- freshness-focused quality execution,
	- quality report artifact upload.
- Added `src/tools/ci_seed_bronze.py` and `make ci-seed-bronze` to produce deterministic Bronze parquet fixtures in CI.
- Kept `.github/workflows/quality-gates.yml` as a manual (`workflow_dispatch`) compatibility workflow while moving PR/push automation to dedicated Phase 09 workflows.

## Concrete Tasks
- Add workflows for linting, tests, dbt run/test, and quality checks.
- Add slim CI behavior for efficient dbt pull request checks.
- Add freshness alert workflow on schedule.
- Configure artifacts/logs for traceability.

### Execution Notes

- PR workflow is intentionally slim to keep feedback cycle short while still validating Python code quality and dbt graph compilation.
- Master workflow enforces full integration gates and is the primary merge confidence path.
- Freshness workflow is intentionally isolated so stale-data detection can alert independently of feature delivery cadence.
- Artifact retention is configured per workflow (`7`, `14`, and `30` days) to balance traceability and storage.

## Done Criteria
- Pull requests run required checks automatically.
- Failures are actionable from CI logs.

### Done Criteria Status

- Met: Required checks are codified in event-triggered GitHub Actions workflows.
- Met: All critical steps are explicit and fail-fast (`make`/dbt exit codes gate job status).
- Met: Key machine-readable artifacts are uploaded for post-run diagnosis.

## Validation Evidence
- Add CI run links/screenshots and check outputs.

### Local Pre-CI Validation (Executed)

- Command executed:
	- `make ci-seed-bronze && make dbt-run && make dbt-test && make quality-check && make test`
- Result:
	- dbt run: PASS (7 models)
	- dbt test: PASS (17 tests)
	- quality check: PASS (0 fails, 0 warns)
	- pytest: PASS (10 passed)

### Evidence Artifacts Produced

- `warehouse/artifacts/phase08_quality_report.json`
- `dbt/target/run_results.json`
- `dbt/target/manifest.json`

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| dbt read failed on CI seed parquet (`dimension_2` type mismatch) | Polars wrote incompatible inferred schemas across dataset parquet files | CI false failures and blocked PR merges | Enforced explicit Bronze schema casting (`BRONZE_SCHEMA`) before parquet write | Keep synthetic fixture writers schema-locked and add local dbt run in change validation |
| Quality gate failed in CI seed mode (`minimum_transition_rows`) | Synthetic fixture volume (10 AGS rows) was below governance threshold (`min_cluster_rows=100`) | Master pipeline would fail despite healthy orchestration logic | Expanded fixture generator to 120 AGS rows | Align synthetic data size with operational thresholds; validate with `make quality-check` before merge |

## Post-Implementation CI Incident Log (2026-03-29)

### Incident A: full-pipeline failed after push (`ff2eb5a`)

- Run: `pipeline-master` (`23710912625`)
- Symptom: `Process completed with exit code 2` in `Run tests`.
- Actual failing check: `tests/test_phase03_contracts.py::test_phase03_profile_outputs_contracts` with `assert 0 >= 8`.
- Root cause: test depended on repository `data/raw` files that are intentionally untracked and absent in GitHub runner context.
- Fix implemented:
	- refactored `tests/test_phase03_contracts.py` to generate synthetic CSV/XLSX/XML fixtures in `tmp_path`.
	- preserved contract assertions while removing external data dependency.
- Additional hardening in same cycle:
	- upgraded action versions to modern majors (`actions/checkout@v6`, `actions/setup-python@v6`).
- Validation:
	- local: `make test`, `make ci-seed-bronze`, `make dbt-run`, `make dbt-test`, `make quality-check` all pass.

### Incident B: full-pipeline failed after warning-removal push (`dd102a7`)

- Run: `pipeline-master` (`23711073198`)
- Symptom: `dbt-test` crashed with fatal Python multiprocessing/GIL error (`PyEval_SaveThread ... GIL is released`).
- Root cause: runner-specific multiprocessing instability under dbt/duckdb threaded execution.
- Fix implemented:
	- made dbt thread count configurable in `dbt/profiles.yml` via `DBT_THREADS` env var.
	- set `DBT_THREADS=1` in CI workflows that execute dbt (`pipeline-master`, `quality-gates`, `freshness-alert`).
- Validation:
	- local with `DBT_THREADS=1`: `make dbt-run` and `make dbt-test` pass.

### Final Verification Outcome

- Successful run: `pipeline-master` (`23711135572`) on commit `3a68507`.
- Status: completed successfully.
- Node action warning status: no remaining Node 20 platform warnings found in run logs.
- Remaining warning class: library-level Python deprecation warnings from Great Expectations dependency chain during pytest.

### Operational Decision on Remaining GE Deprecation Warnings

- Decision: do not fail CI for these warnings currently.
- Rationale:
	- they are third-party dependency deprecation notices, not project logic failures,
	- core gates (dbt, quality checks, tests) are passing deterministically.
- Control:
	- keep warnings visible in logs,
	- track dependency upgrade/pinning work as maintenance debt,
	- revisit if warnings escalate to runtime errors in upcoming dependency releases.

## Risks and Follow-ups

- Risk: CI fixture drift versus production raw patterns could mask edge-case parsing issues.
- Mitigation: Keep raw ingestion tests and occasional end-to-end runs against controlled raw snapshots.
- Follow-up: Add branch protection rule mapping (`ci-pr` required on PR, `pipeline-master` required on master) in repository settings.
