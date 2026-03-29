# Phase 06: Gold Layer (Leakage Funnel + Transition Marts)

Status: Completed (2026-03-29)

## 5W1H (Who, What, When, Where, Why, How)

### Who
- Project maintainer and Copilot coding agent implemented and validated Gold marts.
- Primary consumers: dashboard/storytelling layer (Phase 10), ML/forecasting features (Phase 07), and governance checks (Phase 08).

### What
- Implemented four Gold marts over Silver entities:
	- district stage funnel (stages 1-5)
	- transition-rate mart
	- international-vs-domestic leakage differential mart
	- HS-FG2 subject resilience mart
- Added model tests to keep Gold contracts query-safe.

### When
- Executed and validated on 2026-03-29 after Phase 05 Silver completion.

### Where
- Gold models:
	- `dbt/models/marts/gold_stage_funnel.sql`
	- `dbt/models/marts/gold_transition_rates.sql`
	- `dbt/models/marts/gold_leakage_differential.sql`
	- `dbt/models/marts/gold_subject_resilience.sql`
- Gold model tests:
	- `dbt/models/marts/marts.yml`
- Supporting config update:
	- `dbt/dbt_project.yml` (marts materialization)

### Why
- Silver provides harmonized events but not decision-ready KPI tables.
- Gold marts are needed for direct district-level transition/leakage analysis and downstream presentation.
- Stage 5 subject-group resilience is required to support talent-leakage interpretation.

### How
- Built stage-specific aggregates from canonical dataset mappings in `int_metric_facts`.
- Unified district-level funnel output and derived transition rates.
- Computed leakage differential on a consistent domestic+international denominator.
- Built subject-level completion-share mart using HS-FG2 groups.
- Executed dbt run/test and reconciled outputs in DuckDB.

## Objective(s)
- Produce decision-ready marts for district-level leakage and resilience.

## Deliverable(s)
- Final funnel tables (stages 1-5), transition-rate mart, leakage differential mart.

### Delivered assets
- `gold_stage_funnel`
- `gold_transition_rates`
- `gold_leakage_differential`
- `gold_subject_resilience`

## Concrete Tasks
- Build stage-level metric models for all education stages.
- Integrate Stage 5 (degree completion) from exam statistics data.
- Build transition rates between stages by district/cohort/time.
- Build international-vs-domestic leakage differential metrics.
- Add subject-level (HS-FG2) talent resilience mart.

## Completion Checklist
- [x] Add marts layer to dbt project config.
- [x] Build district stage funnel model across stages 1-5.
- [x] Build transition-rate mart with end-to-end completion indicator.
- [x] Build leakage differential mart using stable denominator logic.
- [x] Build HS-FG2 subject resilience mart.
- [x] Add schema tests for Gold entities.
- [x] Validate with dbt run/test and reconciliation queries.

## Done Criteria
- Gold marts align to phase-1 KPI definitions.
- Metrics are queryable and reproducible.

Done criteria outcome:
- Achieved for implemented Gold scope with documented caveats on cross-stage temporal alignment.

## Validation Evidence
- `make dbt-run`:
	- PASS=7 models (staging, intermediate, marts)
- `make dbt-test`:
	- PASS=17 tests, WARN=0, ERROR=0
- Reconciliation snapshots from `warehouse/analytics.duckdb`:
	- `gold_stage_funnel`: 457 rows / 457 AGS keys
	- `gold_transition_rates`: 457 rows
	- `gold_leakage_differential`: 1652 rows
	- `gold_subject_resilience`: 2841 rows across 9 HS-FG2 groups
- Leakage differential bounded check after denominator fix:
	- min = -1.0, max = 1.0

## Key Decisions and Trade-offs
- Decision: use canonical source mappings per stage (not unioning primary + fallback simultaneously).
	- Benefit: avoids double-counting and aligns with source-of-truth policy.
	- Trade-off: fallback reconciliation is separate work, not merged into production aggregates.
- Decision: aggregate stage funnel at district level by AGS with stage-specific year columns.
	- Benefit: robust joins despite heterogeneous source time fields.
	- Trade-off: strict cohort-time comparability remains limited until richer temporal harmonization.
- Decision: compute leakage differential using `international / (international + domestic)` and `domestic / (international + domestic)`.
	- Benefit: interpretable, bounded differential in [-1, 1].
	- Trade-off: excludes records where neither domestic nor international values are present.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| Leakage differential initially produced values outside expected range | Shares were initially divided by `Insgesamt`, which can differ from `deutsch + ausländisch` for some slices | Misleading interpretation of differential magnitude | Rebased shares on `deutsch + ausländisch` denominator and regenerated marts | Keep bounded-range sanity checks for all rate/differential metrics |
| Sparse downstream stages in some funnel rows | Source files differ in temporal/granularity coverage and AGS availability per stage | Null-heavy transitions for some districts and years | Preserved explicit nulls and stage-year columns rather than forcing imputation | Add cohort alignment refinement in later iteration (Phase 07/08 data-quality hardening) |

## Residual Risks
- Cross-stage temporal comparability is partially constrained by source-year heterogeneity.
- Stage mapping remains dependent on current metric label conventions.
- Additional policy-oriented KPI calibration may be needed once dashboard narratives are finalized.

## Handoff Readiness (to Phase 07)
- Gold marts are built, tested, and queryable for feature engineering.
- Transition and leakage indicators are available for clustering/forecasting inputs.
- No blocking issue remains to start Phase 07 execution.
