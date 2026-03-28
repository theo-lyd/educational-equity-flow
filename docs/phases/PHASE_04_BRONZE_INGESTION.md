# Phase 04: Bronze Ingestion (CSV + XML to Parquet)

## Objective(s)
- Build resilient ingestion from messy raw files to typed partitioned parquet.

## Deliverable(s)
- Python ingestion package, partitioned bronze parquet, metadata manifest.

## Concrete Tasks
- Implement true-start scanner for metadata-heavy CSVs.
- Implement ISO-8859-1-safe CSV parsing and cleaning.
- Implement XML flattening parser.
- Normalize AGS and category values.
- Add manifest-based incremental/upsert ingest behavior.
- Write ingestion unit tests and smoke tests.

## Done Criteria
- All raw files ingest successfully.
- Re-runs are idempotent and selective for changed files.

## Validation Evidence
- Add row counts, schema checks, and manifest diffs.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| None yet | - | - | - | - |
