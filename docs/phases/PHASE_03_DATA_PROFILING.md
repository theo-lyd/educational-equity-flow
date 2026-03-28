# Phase 03: Data Profiling & Source Contracts

Status: Completed (2026-03-28)

## Objective(s)
- Understand raw data structure, semantics, and ingestion constraints.

## Deliverable(s)
- Profiling report and source contracts per dataset/file type.

## Concrete Tasks
- Profile each CSV for encoding, separator, header offset, footer noise.
- Profile XML hierarchy and flattening strategy.
- Identify key dimensions (AGS, year, sex, nationality, subject group).
- Define source contracts: required columns, types, ranges.
- Record normalization rules for abbreviations and scaled values.

## Done Criteria
- Contracts exist and are referenced by ingestion tests.
- No unknown critical field remains undocumented.

## Validation Evidence
- Profiling artifacts generated from executable profiler:
	- `docs/phase_03/artifacts/RAW_PROFILING_SUMMARY.md`
	- `docs/phase_03/artifacts/schema_snapshots.json`
	- `docs/phase_03/artifacts/source_contracts.json`
- Human-readable source contract narrative:
	- `docs/phase_03/SOURCE_CONTRACTS.md`
- Reproducible command:
	- `make profile-phase03`
- Contract validation tests:
	- `tests/test_phase03_contracts.py`

## Completion Checklist
- [x] Profile each CSV for encoding, separator, header offset, and metadata noise.
- [x] Profile XML hierarchy and flattening-relevant structure.
- [x] Identify core dimensions used for cross-stage harmonization.
- [x] Define machine-readable source contracts with required rules and quality markers.
- [x] Persist schema snapshots and profiling summary artifacts.
- [x] Add test coverage for contract artifact generation.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| XLSX parsing warning (`Workbook contains no default style`) during profiling | Source workbook formatting omits a default style entry | Cosmetic warning noise; potential concern about parse fidelity | Continued read-only profiling with `openpyxl` and validated extracted header rows/columns in artifacts | Keep parser warnings non-fatal and validate schema output artifacts in tests |
