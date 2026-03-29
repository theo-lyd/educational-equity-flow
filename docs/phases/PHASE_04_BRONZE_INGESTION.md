# Phase 04: Bronze Ingestion (CSV + XML to Parquet)

Status: Completed (2026-03-28)

## 5W1H (Who, What, When, Where, Why, How)

### Who
- Primary implementer: repository maintainer and Copilot coding agent during Phase 04 execution.
- Primary consumers: downstream dbt/Silver model developers (Phase 05), quality-governance checks (Phase 08), and dashboard/forecast stages (Phases 07 and 10).
- Operational stakeholders: anyone running local ingestion (`make ingest`) or CI ingestion jobs.

### What
- Implemented a resilient Bronze ingestion pipeline handling mixed raw formats:
	- Statistical CSV sources with metadata/header noise and varying true-data start positions.
	- Flat CSV extracts with explicit dimension/value columns.
	- XLSX workbooks with irregular headers.
	- XML cube-style extracts requiring coordinate flattening.
- Standardized output into a common Bronze schema and partitioned parquet layout.
- Added manifest-based selective reprocessing for idempotent incremental runs.
- Added regression coverage for partition write behavior, idempotency, and stale-partition cleanup.

### When
- Execution window: 2026-03-28.
- Completion checkpoint: after full force ingest + immediate incremental rerun validation.

### Where
- Implementation modules:
	- `src/ingestion/scan_true_start.py`
	- `src/ingestion/normalizers.py`
	- `src/ingestion/csv_ingestor.py`
	- `src/ingestion/xlsx_ingestor.py`
	- `src/ingestion/xml_ingestor.py`
	- `src/ingestion/manifest.py`
	- `src/ingestion/run.py`
- Test coverage:
	- `tests/test_phase04_ingestion.py`
- Data outputs and run artifacts:
	- `data/bronze/dataset=<dataset>/year=<year>/*.parquet`
	- `data/bronze/ingestion_manifest.json`
	- `warehouse/artifacts/ingest_bronze.json`

### Why
- Raw source files are heterogeneous, semi-structured, and include quality markers/metadata conventions that block direct analytical use.
- Bronze standardization is required to:
	- Provide consistent typing and dimensions for Silver dbt transformations.
	- Enable safe reruns without duplicate accumulation.
	- Preserve lineage from source file to parquet output.

### How
- Discovery and routing:
	- Recursively discover `.csv`, `.xlsx`, `.xml` under raw source path.
	- Route each file to a format-specific ingestor.
- Normalization:
	- Normalize AGS codes and labels.
	- Parse numeric values including scaled abbreviations/markers.
	- Coerce to canonical Bronze columns/types.
- Partitioned output strategy:
	- Write parquet by `dataset` and `year` partitions.
	- Clean dataset target directory before rewriting changed sources to avoid stale partitions.
- Incremental behavior:
	- Compare source SHA-256 against manifest to decide process vs skip.
	- Record row counts, output paths, and timestamps in manifest.
- Verification:
	- Unit/integration tests.
	- Full force run over repository raw data.
	- Immediate rerun proving idempotent skip behavior.

## Objective(s)
- Build resilient ingestion from messy raw files to typed partitioned parquet.

## Deliverable(s)
- Python ingestion package, partitioned bronze parquet, metadata manifest.

### Delivered implementation modules
- `src/ingestion/scan_true_start.py`
- `src/ingestion/normalizers.py`
- `src/ingestion/csv_ingestor.py`
- `src/ingestion/xlsx_ingestor.py`
- `src/ingestion/xml_ingestor.py`
- `src/ingestion/manifest.py`
- `src/ingestion/run.py`
- `tests/test_phase04_ingestion.py`

### Bronze schema contract (canonical columns)
- `dataset`
- `source_file`
- `year`
- `ags`
- `region`
- `dimension_1`
- `dimension_2`
- `dimension_3`
- `metric_name`
- `raw_value`
- `value`
- `quality`

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
- Test suite validation:
	- `make test` completed (`6 passed`, warning-free).
- Full ingestion validation (force reprocess):
	- `python -m src.ingestion.run --source data/raw --target data/bronze --force`
	- Result: `raw_file_count=9 processed=9 skipped=0 rows_written=214977`
- Incremental/idempotent validation (immediate re-run):
	- `python -m src.ingestion.run --source data/raw --target data/bronze`
	- Result: `raw_file_count=9 processed=0 skipped=9 rows_written=0`
- Artifact evidence written:
	- `warehouse/artifacts/ingest_bronze.json`
	- `data/bronze/ingestion_manifest.json`

## Operational Notes (Runbook)
- Baseline execution command:
	- `make ingest`
- Full reset/rebuild of processed datasets:
	- `python -m src.ingestion.run --source data/raw --target data/bronze --force`
- Incremental rerun (manifest-aware):
	- `python -m src.ingestion.run --source data/raw --target data/bronze`
- Expected behavior:
	- Unchanged files are skipped.
	- Changed/new files are reprocessed only.
	- Dataset-level cleanup prevents stale partitions on reprocess.

## Completion Checklist
- [x] Implement true-start scanner for metadata-heavy CSVs.
- [x] Implement ISO-8859-1-safe CSV parsing and cleaning.
- [x] Implement XML flattening parser.
- [x] Normalize AGS and category values.
- [x] Add manifest-based incremental/upsert ingest behavior.
- [x] Add tests for partitioned write, idempotency, and stale-partition cleanup.
- [x] Validate full ingest and incremental re-run on repository raw files.

## Architecture and Data Contract Decisions
- Decision: canonical long-form Bronze schema across all source types.
	- Benefit: simplifies Silver model unions and shared macros.
	- Trade-off: some source-specific context is mapped into generic dimensions.
- Decision: dataset/year partitioned parquet writes.
	- Benefit: better query locality and incremental replacement behavior.
	- Trade-off: requires careful stale-partition hygiene.
- Decision: manifest SHA-256 change detection for selective processing.
	- Benefit: idempotent reruns and lower runtime cost.
	- Trade-off: manifest integrity becomes operationally important.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| `make test` failed despite successful `setup-venv` | `Makefile` defaulted to system `python`, not project `.venv` interpreter | Commands could fail in clean environments (`pytest`/deps not found) and break reproducibility | Updated `PYTHON` fallback logic to auto-prefer `.venv/bin/python` when present | Keep Make targets environment-aware and validate from fresh shell sessions |
| Stale year partitions persisted after parser logic changes | Partitioned parquet writer overwrote touched paths but did not remove old dataset partitions | Downstream readers could observe outdated partitions and inflated/incorrect aggregates | Added dataset-level cleanup before rewriting a processed source dataset | Keep a regression test ensuring reprocess removes stale partitions (`test_phase04_reprocess_removes_stale_partitions`) |
| `openpyxl` default-style warning in run/test output | Source XLSX files omit default style metadata | Warning noise could mask meaningful warnings and reduce signal in validation logs | Added targeted warning suppression for the known message in ingestion path and pytest filter for test output | Keep warning filters message-specific and revisit only if parsing behavior changes |

## Residual Risks
- Semantic drift in source labels/axes may require additional normalization mapping in later runs.
- `unknown` year partitions can still appear when sources omit explicit time dimension.
- Historical regional boundary changes are not yet handled at Bronze level (intended for Silver snapshots).

## Handoff Readiness (to Phase 05)
- Bronze ingestion is stable, tested, and idempotent.
- Source contracts and Bronze schema are sufficient inputs for dbt Silver harmonization.
- Remaining work is expected and scoped to Phase 05 (dbt project initialization, conformed dimensions, tests, snapshots).
