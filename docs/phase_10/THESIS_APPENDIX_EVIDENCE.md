# Thesis Appendix Evidence (Phase 10)

## Architecture Summary

- Ingestion: Python multi-format loaders (CSV/XLSX/XML) produce partitioned Bronze parquet.
- Transformation: dbt on DuckDB builds Silver harmonization models and Gold policy marts.
- Intelligence: clustering and forecasting artifacts generated in `warehouse/artifacts/`.
- Governance: quality checks enforce referential integrity, freshness, and operational thresholds.
- Delivery: Streamlit dashboard exposes leakage funnel, anomaly map, SCD timeline, resilience views, and an observational causal analysis panel.

## Lineage Summary

1. `data/raw/*` -> Bronze ingestion (`src/ingestion/`) -> `data/bronze/`
2. `data/bronze/**/*.parquet` -> `dbt/models/staging/*` -> Silver tables
3. Silver tables -> `dbt/models/marts/*` -> Gold marts (`gold_stage_funnel`, `gold_transition_rates`, `gold_leakage_differential`, `gold_subject_resilience`)
4. Gold marts -> ML pipeline (`src/ml/run_all.py`) -> phase 07 artifacts
5. Gold marts + artifacts -> quality checks (`src/quality/run_checks.py`) -> phase 08 report
6. Gold marts + snapshot history -> Streamlit (`app/main.py`) for policy interpretation
7. Gold transition/leakage outputs -> Causal module (`src/dashboard/causal_inference.py`) for matching diagnostics, ATE estimation, and counterfactual scenarios

## Reproducibility Checklist

- Environment setup:
  - `make setup-venv`
- Data preparation and model build:
  - `make ingest`
  - `make dbt-run`
  - `make dbt-test`
- Intelligence and governance:
  - `make ml-run`
  - `make quality-check`
- App launch:
  - `make app`

## Core Evidence Artifacts

- `warehouse/artifacts/phase07_cluster_assignments.csv`
- `warehouse/artifacts/phase07_cluster_summary.csv`
- `warehouse/artifacts/phase07_forecast.csv`
- `warehouse/artifacts/phase07_report.json`
- `warehouse/artifacts/phase08_quality_report.json`
- `dbt/target/manifest.json`
- `dbt/target/run_results.json`

## Model Card (Compact)

### Segmentation model
- Family: K-Means.
- Inputs: transition-rate and leakage-derived district features.
- Selection: silhouette-based choice of cluster count.
- Primary use: district policy targeting tiers.

### Forecast model
- Family: hierarchical fallback (Prophet -> linear trend -> naive).
- Target: aggregate completion trajectory over 5-year horizon.
- Primary use: directional planning, not individual-level prediction.
- Key caveat: sensitive to source cadence and structural breaks.

## Testing Evidence

- Unit and pipeline tests via `make test`.
- dbt assertions via `make dbt-test`.
- governance checks via `make quality-check`.
- CI orchestration checks in `.github/workflows/`.
- Causal analysis coverage includes `tests/test_causal_inference.py` and `tests/test_causal_ui_wiring.py`.
