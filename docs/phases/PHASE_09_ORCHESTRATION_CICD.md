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
- Retired overlapping legacy workflow `.github/workflows/quality-gates.yml` to prevent duplicate CI runs on the same events.

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

## Risks and Follow-ups

- Risk: CI fixture drift versus production raw patterns could mask edge-case parsing issues.
- Mitigation: Keep raw ingestion tests and occasional end-to-end runs against controlled raw snapshots.
- Follow-up: Add branch protection rule mapping (`ci-pr` required on PR, `pipeline-master` required on master) in repository settings.
