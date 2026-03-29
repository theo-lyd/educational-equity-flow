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

## Phase 07 Deep-Dive (Novice-Friendly)

This section explains each major algorithm, model, framework, and design choice used in Phase 07 using the following structure:
- What it does
- When to use it
- Why to use it
- How it works
- What exactly it is doing in this project
- Possible issues (general + project-specific)
- How issues are resolved
- How to tune/optimize for this context

### 1) DuckDB feature extraction layer

What it does:
- Reads analytical tables quickly and turns them into model-ready feature data.

When to use it:
- When your transformed data already lives in local DuckDB/dbt tables and you want reproducible feature engineering.

Why to use it:
- Very fast on local analytical workloads.
- Simple deployment model (single-file database).
- Easy to reproduce on another machine.

How it works:
- SQL queries aggregate and join Gold marts into one row per district (AGS).

What it does here:
- Builds clustering features from transition, leakage, and subject resilience marts.
- Builds Stage-5 yearly series for forecasting.

Possible issues:
- Schema drift upstream breaks feature SQL.
- Null-heavy columns reduce model stability.

Issues encountered here:
- Several downstream features had sparse/null patterns.

How resolved:
- Added robust null handling in model preprocessing and documented caveats.

How to tune/optimize:
- Add dbt tests for feature-contract columns.
- Materialize a dedicated feature model in dbt for stricter lineage.
- Add null-rate thresholds as pre-ML quality gates.

### 2) Feature engineering from Gold marts

What it does:
- Converts policy KPIs into numerical variables for ML.

When to use it:
- Always before fitting clustering/forecasting models.

Why to use it:
- Model quality depends heavily on feature quality, often more than algorithm choice.

How it works:
- Aggregates district-level rates and shares into a compact feature frame.

What it does here:
- Uses:
	- transition rates 1->2, 2->3, 3->4, 4->5
	- end-to-end completion
	- compounded transition
	- average leakage differential
	- average international share
	- average subject completion share

Possible issues:
- Feature leakage (future information in training feature).
- Highly correlated/redundant features.
- Missingness and noisy ratios.

Issues encountered here:
- Sparse downstream-stage coverage yields missing values for some districts.

How resolved:
- Imputation + all-null column handling + explicit caveat documentation.

How to tune/optimize:
- Add feature-correlation diagnostics and remove redundant columns.
- Add robust outlier clipping for unstable ratios.
- Build per-year panel features when temporal depth improves.

### 3) scikit-learn Pipeline

What it does:
- Chains preprocessing and model fitting into one deterministic workflow.

When to use it:
- Any time preprocessing must exactly match model training behavior.

Why to use it:
- Prevents training/inference mismatch.
- Improves reproducibility and code maintainability.

How it works:
- Sequentially applies:
	- SimpleImputer
	- StandardScaler
	- KMeans

What it does here:
- Ensures all districts are preprocessed consistently before segmentation.

Possible issues:
- Wrong step order can distort results.
- Unhandled all-null columns can still break upstream logic.

Issues encountered here:
- k-selection initially evaluated raw NaN features and failed.

How resolved:
- Preprocessed data before silhouette-based k selection.

How to tune/optimize:
- Persist fitted pipeline objects for strict reproducibility.
- Add schema validation before pipeline fit.

### 4) SimpleImputer (median)

What it does:
- Replaces missing values with a robust central value.

When to use it:
- When models cannot consume NaNs directly.

Why to use it:
- KMeans requires finite numeric inputs.
- Median is less outlier-sensitive than mean.

How it works:
- Computes per-column median on observed values and fills missing cells.

What it does here:
- Fills sparse transition/leakage feature gaps.

Possible issues:
- Can hide meaningful missingness patterns.
- Poor fit for multimodal distributions.

Issues encountered here:
- Entire columns can be null for specific data slices.

How resolved:
- Added explicit all-null replacement before imputation.

How to tune/optimize:
- Add missingness indicator features.
- Compare median vs grouped imputation by region/cluster.

### 5) StandardScaler

What it does:
- Standardizes feature scales so distance calculations are balanced.

When to use it:
- Distance-based methods (KMeans, kNN, PCA).

Why to use it:
- Prevents larger-range features from dominating clustering.

How it works:
- Applies z-score normalization per feature.

What it does here:
- Normalizes mixed KPI rates/shares before KMeans.

Possible issues:
- Sensitive to heavy outliers.

How resolved in this context:
- Scaling is applied after imputation; still acceptable as a baseline.

How to tune/optimize:
- Evaluate RobustScaler if outliers increase.
- Clip extreme values before scaling.

### 6) KMeans clustering

What it does:
- Groups districts into behavioral segments using centroid-based distance minimization.

When to use it:
- Unsupervised segmentation on numeric features.

Why to use it:
- Fast, interpretable baseline for policy segmentation.

How it works:
- Iteratively assigns points to nearest centroid and updates centroids until convergence.

What it does here:
- Segments 457 districts into 6 clusters and stores assignments/summaries.

Possible issues:
- Sensitive to initialization and scaling.
- Assumes roughly convex/spherical clusters.

Issues encountered here:
- Initial failure due NaN handling prior to k selection.

How resolved:
- Added preprocessing before both k-selection and final fit.

How to tune/optimize:
- Increase k search range and compare stability.
- Run bootstrap stability checks.
- Compare with GMM or density-based alternatives in future iterations.

### 7) Silhouette score for k-selection

What it does:
- Quantifies cluster compactness/separation to choose k.

When to use it:
- During unsupervised model selection.

Why to use it:
- Provides objective signal instead of choosing k by guesswork.

How it works:
- Compares each sample's within-cluster distance to nearest other-cluster distance.

What it does here:
- Evaluates candidate k values and selects best silhouette score.

Possible issues:
- Can prefer simplistic cluster structures.
- Sensitive to noisy or sparse features.

Issues encountered here:
- Required preprocessed matrix to avoid NaN-based failure.

How resolved:
- Silhouette now computed on imputed/scaled matrix.

How to tune/optimize:
- Add secondary indices (Davies-Bouldin / Calinski-Harabasz).
- Combine with business interpretability and stability criteria.

### 8) Cluster narrative labeling

What it does:
- Converts numeric cluster IDs into policy-friendly narratives.

When to use it:
- When non-technical stakeholders consume segmentation outputs.

Why to use it:
- Cluster IDs alone are not actionable for policy audiences.

How it works:
- Ranks clusters by selected KPI means and maps them to narrative labels.

What it does here:
- Produces labels such as:
	- High Resilience
	- Stable Transition
	- Recovery Potential
	- High Leakage Risk
	- Data Sparse Segment
	- Emerging Segment

Possible issues:
- Label semantics can become subjective.

How resolved in this context:
- Logic is explicit in code and documented in this phase file.

How to tune/optimize:
- Move label mapping to configuration.
- Add policy-review signoff for labeling logic.

### 9) Prophet forecasting (primary method)

What it does:
- Fits decomposable time-series model (trend/seasonality) for forecasting.

When to use it:
- Adequate history and stable runtime backend are available.

Why to use it:
- Practical baseline for business forecasting with clear structure.

How it works:
- Fits additive trend/seasonality model and predicts future periods.

What it does here:
- First-choice method, attempted only when minimum points and runtime support allow.

Possible issues:
- Can fail at runtime due Stan backend availability.
- Requires enough points to produce meaningful trend.

Issues encountered here:
- Environment could import Prophet but fail backend at fit/initialization.
- Current Stage 5 time series has only one point.

How resolved:
- Added method hierarchy and explicit fallback metadata.

How to tune/optimize:
- Raise minimum-point threshold with stronger evidence requirements.
- Add rolling backtests once multi-year series exists.
- Tune changepoint priors and seasonality once data depth improves.

### 10) Linear trend fallback (secondary)

What it does:
- Uses linear regression over time to project near-term trend.

When to use it:
- Data has at least two points, but Prophet is unavailable or underpowered.

Why to use it:
- Extracts trend signal better than flat naive forecast on sparse-medium data.

How it works:
- Fits line with `numpy.polyfit` and extrapolates horizon years.
- Uses residual-based (or minimum proportional) uncertainty band.

What it does here:
- Mid-tier fallback between Prophet and naive.

Possible issues:
- Can over/under-shoot when trend is unstable.

How resolved in this context:
- Kept method deterministic and bounded with simple uncertainty handling.

How to tune/optimize:
- Add slope caps and robust trend estimation.
- Use weighted trend fitting if newer years are more reliable.

### 11) Naive last-value fallback (tertiary safety net)

What it does:
- Forecasts future years as the last observed value.

When to use it:
- Extremely sparse history (especially a single point) or hard runtime failures.

Why to use it:
- Deterministic and honest when data cannot support trend learning.

How it works:
- Repeats last value over forecast horizon with a small uncertainty band.

What it does here:
- Active method for current dataset because Stage 5 has one training point.
- Explicitly reported in artifact metadata with fallback reason.

Possible issues:
- No trend awareness.

How resolved in this context:
- Method is disclosed, caveated, and designed as fallback only.

How to tune/optimize:
- Replace automatically with linear/Prophet once point thresholds are met.
- Add drift-based naive variant when 2+ points exist.

### 12) Testing and reliability layer (pytest)

What it does:
- Guards against regressions in pipeline logic and artifact generation.

When to use it:
- Every phase with executable logic.

Why to use it:
- ML pipelines are sensitive to silent breakages.

How it works:
- Unit tests for fallback methods and integration-like test for end-to-end artifact generation.

What it does here:
- Verifies:
	- naive forecast behavior,
	- linear fallback behavior,
	- run_all artifact generation and metadata expectations.

Possible issues:
- Floating point precision differences.
- Environment-dependent Prophet behavior.

Issues encountered here:
- Strict equality failed for float predictions.
- Prophet backend failures in test environments.

How resolved:
- Switched to approximate assertions for float checks.
- Added robust forecast fallback handling.

How to tune/optimize:
- Add cluster stability tests.
- Add feature contract tests (null-rate thresholds).
- Add offline regression fixtures to compare artifact distributions over time.

## Phase 07.5 Improvement Checklist (Before Phase 08)

Prioritization uses:
- Impact: effect on model quality/reliability and policy usefulness.
- Effort: expected implementation complexity/time.

### High Impact / Low Effort

1) Add ML data-quality gates before training.
- Why: catches sparse/malformed feature frames before model run.
- Do:
	- fail/flag if feature null-rate exceeds threshold,
	- fail/flag if district count drops unexpectedly,
	- fail/flag if forecast training points below declared threshold.

2) Add explicit method-selection rules to config.
- Why: keeps forecast strategy transparent and auditable.
- Do:
	- `min_points_prophet`,
	- `min_points_linear`,
	- fallback order and uncertainty-band policy.

3) Persist model-run metadata as first-class governance artifact.
- Why: supports reproducibility audits.
- Do:
	- include git commit SHA,
	- include feature schema hash,
	- include selected k and score diagnostics.

4) Add quick feature diagnostics artifact.
- Why: often-overlooked but critical for debugging model behavior.
- Do:
	- per-feature min/max/mean/std/null-rate,
	- outlier counts,
	- correlation summary.

### High Impact / Medium Effort

5) Add cluster stability checks.
- Why: single-run silhouette can be misleading.
- Do:
	- rerun clustering on bootstrap samples,
	- compute stability score (e.g., adjusted Rand between runs),
	- include stability in model acceptance criteria.

6) Introduce temporal backtesting once >=4 Stage-5 points exist.
- Why: forecasting without backtest is weak for production confidence.
- Do:
	- rolling-origin evaluation,
	- MAE/MAPE/RMSE tracking,
	- compare Prophet vs linear vs naive.

7) Separate training data snapshot from live tables.
- Why: prevents accidental drift between reruns.
- Do:
	- create fixed training views/tables with run IDs,
	- train from snapshot only,
	- keep lineage to upstream dbt run.

### Medium Impact / Low Effort

8) Improve narrative-label governance.
- Why: cluster names influence stakeholder interpretation.
- Do:
	- move label map to config,
	- add short policy meaning per label,
	- version label definition changes.

9) Add deterministic random seeds to all stochastic steps and log them.
- Why: reproducibility and troubleshooting.
- Do:
	- centralized seed constant,
	- write seed values into report metadata.

10) Add artifact schema tests.
- Why: downstream dashboards can break on subtle column changes.
- Do:
	- validate required columns in each CSV/JSON artifact,
	- enforce type checks.

### High Impact / High Effort

11) Expand forecasting from single national Stage-5 aggregate to district-level panel forecasting.
- Why: policy actions are district-specific.
- Do:
	- construct district-year panel with enough history,
	- support hierarchical reconciliation (district -> state -> national),
	- add uncertainty calibration.

12) Add MLOps monitoring baseline.
- Why: production-readiness requires drift/performance monitoring.
- Do:
	- data drift metrics for input features,
	- concept drift alarms for segment movement,
	- forecast error tracking once future actuals arrive.

## Suggested 2-Week Execution Plan (Practical)

Week 1:
- Implement items 1, 2, 3, 4, 9, 10.

Week 2:
- Implement items 5 and 8.
- Prepare design docs for items 6, 7, 11, 12 pending data-depth growth and Phase 08 governance hooks.
