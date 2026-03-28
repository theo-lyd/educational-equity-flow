# Phase 03 Source Contracts

This document defines the source-contract baseline generated from raw-file profiling.

## Contract Scope

- Profiled files: 8 raw source files used by stages 1-5.
- Machine-readable artifacts:
  - `docs/phase_03/artifacts/schema_snapshots.json`
  - `docs/phase_03/artifacts/source_contracts.json`
  - `docs/phase_03/artifacts/RAW_PROFILING_SUMMARY.md`

## Cross-File Contract Rules

Every source contract includes the following required checks for downstream ingestion:

- Must include geo key dimensions: `AGS` or `KREISE`.
- Must include time dimension: `JAHR`.
- Accepted quality markers: `-`, `.`, `x`, `X`, `e`.
- Ingestion normalization requirements:
  - normalize AGS to 5-digit string;
  - normalize abbreviations/scales (`dar.`, `Mio`, `K`);
  - drop metadata rows before true header row.

## File-Type Specific Profiling Outcomes

### CSV family

- Encoding detected as `iso-8859-1` for statistical CSV extracts.
- Delimiter detected as `;`.
- Metadata/header offsets vary by file, requiring dynamic header/data-start detection.

### XLSX family

- Multi-row header layout present in both stage-1/2 and stage-4 workbook variants.
- Header row index is not fixed across files.

### XML family

- XML contains explicit axes for canonical dimensions.
- Detected axis variables from `21321-01-01-4-B.xml`:
  - `KREISE`, `HS-FG2`, `GESINS`, `JAHR`.
- Coordinate-based measure records and quality markers are present in `VALUE` nodes.

## Usage in Validation

- Profiling can be regenerated with:
  - `make profile-phase03`
- Test coverage validates contract artifact generation and core file inclusion:
  - `tests/test_phase03_contracts.py`

## Phase-Forward Note

Contracts in this phase intentionally capture constraints and required dimensions rather than final transformed schema. In Phase 04 ingestion, these contracts become executable parsing/validation gates.
