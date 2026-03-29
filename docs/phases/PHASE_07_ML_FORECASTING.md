# Phase 07: ML Clustering & Forecasting

Status: Completed (2026-03-29)

## 5W1H (Who, What, When, Where, Why, How)

### Who
- Project maintainer and Copilot coding agent implemented and validated the Phase 07 pipeline.
- Primary consumers: policy dashboard (Phase 10), governance checks (Phase 08), and thesis defense narrative.

### What
- Implemented deterministic district segmentation using K-Means over Gold-derived features.
- Implemented 5-year forecasting pipeline with Prophet primary mode and robust fallback mode.
- Generated versioned ML artifacts for cluster assignments, summaries, and forecast outputs.

### When
- Executed and validated on 2026-03-29 after Gold marts were available.

### Where
- ML pipeline implementation:
	- `src/ml/run_all.py`
	- `src/ml/__init__.py`
- Tests:
	- `tests/test_phase07_ml.py`
- Command wiring:
	- `Makefile` (`ml-run`)
	- `README.md`
- Output artifacts:
	- `warehouse/artifacts/phase07_cluster_assignments.csv`
	- `warehouse/artifacts/phase07_cluster_summary.csv`
	- `warehouse/artifacts/phase07_forecast.csv`
	- `warehouse/artifacts/phase07_report.json`

### Why
- Gold marts quantify transitions/leakage but do not provide direct segmentation or forward outlook.
- Clustering provides district archetypes for targeted intervention strategies.
- Forecasting provides scenario planning input for medium-term policy discussion.

### How
- Feature engineering from Gold marts:
	- transition rates,
	- end-to-end completion,
	- leakage differential,
	- subject completion share.
- K selection by silhouette scoring with deterministic random seed.
- Cluster narrative labeling by resilience/leakage profile ranking.
- Forecast generation:
	- Prophet used when sufficient data points/backends are available.
	- linear-trend fallback used when data is enough for trend estimation but insufficient for reliable Prophet.
	- deterministic naive fallback used when time-series support is insufficient.

## Objective(s)
- Segment districts and forecast future outcomes for policy planning.

## Deliverable(s)
- K-Means cluster outputs, Prophet forecasts, model documentation.

### Delivered assets
- Phase 07 orchestration script with artifact writer.
- Cluster assignment and summary outputs.
- 5-year forecast output with method metadata and fallback reason tracking.

## Concrete Tasks
- Engineer modeling features from gold marts.
- Train and evaluate K-Means; determine best k.
- Label clusters into policy narratives.
- Train Prophet forecast for 5-year outlook.
- Save model artifacts and reproducible scoring scripts.

## Completion Checklist
- [x] Implement reusable Phase 07 ML pipeline module.
- [x] Build district-level feature frame from Gold marts.
- [x] Train deterministic K-Means with automatic k selection.
- [x] Attach interpretable policy narrative labels to clusters.
- [x] Implement forecast pipeline with Prophet-first and deterministic fallback.
- [x] Generate versioned artifacts in `warehouse/artifacts/`.
- [x] Add test coverage for fallback and artifact generation.
- [x] Validate dbt + ML + pytest execution chain.

## Done Criteria
- Models run deterministically and outputs are versioned.
- Assumptions, caveats, and evaluation are documented.

Done criteria outcome:
- Achieved, with explicit forecast-data sparsity caveat documented below.

## Validation Evidence
- Command validation:
	- `make dbt-run` PASS
	- `make dbt-test` PASS (17 tests)
	- `make ml-run` PASS
	- `make test` PASS (8 tests)
- Artifact evidence (`warehouse/artifacts/phase07_report.json`):
	- `cluster_assignment_rows`: 457
	- `cluster_count`: 6
	- `selected_k`: 6
	- `silhouette`: 0.3526871688151161
	- `forecast_rows`: 5
	- `forecast_method`: `naive_last_value`
	- `fallback_reason`: `insufficient_time_points_for_prophet`
- Forecast output years:
	- 2024-2028 (5-year horizon)

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| K-Means failed due NaN features during k-selection | Some gold-derived features are sparse/null for subsets of districts | Pipeline crash and non-reproducible ML stage | Added preprocessing for all-null columns + median imputation + scaling before k-selection and training | Keep explicit null-handling checks before clustering |
| Prophet unavailable at runtime for local test context (Stan backend issue) | Environment can import Prophet but still fail model initialization/training | Forecast stage could fail nondeterministically by environment | Added robust try/fallback to deterministic naive forecast and recorded fallback metadata in artifacts | Keep forecast method + fallback reason in report for transparent reproducibility |
| Forecast quality degraded for sparse but non-singleton time series | Prophet is not robust with low points and backend variability; naive fallback may underuse available trend signal | Underfitting medium-sparse series | Added hierarchical fallback: Prophet -> linear trend -> naive last value | Keep explicit minimum-point thresholds per forecast method and record selected method |
| Limited yearly points for Stage 5 series | Current modeled data has one year of stage-5 totals in Gold funnel | Prophet cannot produce meaningful fitted trend from a single point | Switched automatically to naive last-value forecast with confidence band and explicit caveat | Revisit Prophet modeling when multi-year Stage 5 history becomes available |

## Residual Risks
- Forecast quality is constrained by current temporal depth (single Stage 5 year).
- Cluster narratives are sensitive to null-heavy transition features for some districts.
- Additional model diagnostics/backtests require broader multi-year training windows.

## Handoff Readiness (to Phase 08)
- ML artifacts are deterministic and versioned.
- Caveats and fallback logic are explicitly documented.
- Pipeline is ready for quality-governance hardening and SLA checks in Phase 08.
