# Phase 01 Architecture V1

## Architecture summary
The solution follows a medallion design:
- Bronze: resilient ingestion and normalization from raw files
- Silver: harmonized conformed entities with dbt
- Gold: leakage and transition marts for policy analytics

## Data flow v1 (logical)

```mermaid
flowchart LR
  A[data/raw CSV XLSX XML] --> B[Bronze Ingestion Python Polars]
  B --> C[data/bronze partitioned parquet]
  C --> D[DuckDB warehouse]
  D --> E[dbt Silver staging intermediate snapshots]
  E --> F[dbt Gold marts leakage transitions resilience]
  F --> G[ML KMeans Prophet scoring]
  F --> H[Great Expectations and dbt tests]
  F --> I[Streamlit dashboard]
  H --> J[GitHub Actions quality and freshness gates]
  G --> I
```

## Control points
- Raw lock file: `data/raw/RAW_STATE_LOCK.csv`
- Incremental ingest control: `metadata_manifest.json` (Phase 04 implementation)
- Freshness check key: latest `Stichtag`
- Key harmonization rule: AGS normalized to 5 digits

## Review notes
- Stage 5 uses flat CSV as canonical with XML parity ingestion.
- Fallback source files are retained for reconciliation, not aggregation.
