# Phase 01 Scope Boundaries

## In scope
- Build a reproducible local pipeline from raw files to policy-facing dashboard.
- Integrate five-stage educational funnel with Stage 5 completion.
- Support multi-format ingestion (CSV, XLSX, XML) in architecture.
- Use DuckDB + parquet + dbt + Python transformations.
- Implement data quality and freshness checks in automated workflow.
- Produce district-level leakage and resilience analytics.

## Out of scope
- Live production cloud deployment to managed infrastructure.
- Real-time streaming ingestion.
- Causal policy impact estimation beyond descriptive and predictive analytics.
- Individual-level student tracking (project remains aggregate and privacy-safe).

## Assumptions
- Source files in `data/raw/` are the authoritative inputs for this thesis run.
- AGS-based district joins are sufficiently stable after harmonization rules.
- Missing values and suppression markers are handled as documented in Bronze/Silver rules.

## Phase acceptance criteria
- Charter, KPI definitions, architecture v1, and boundaries are complete.
- All formulas and terms are clear for reviewer replication.
- Data lock artifact exists and captures current raw baseline hashes.
