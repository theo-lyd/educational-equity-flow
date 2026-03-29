# Phase 03: Data Profiling & Source Contracts

Status: Completed (2026-03-28)

## 5W1H (Who, What, When, Where, Why, How)

### Who
- Data profiling implemented by project maintainer with Copilot execution support.
- Primary consumers: ingestion engineers (Phase 04), dbt modelers (Phase 05), and quality-governance checks (Phase 08).

### What
- Profiled all raw source families (CSV, XLSX, XML) to capture real-world ingestion constraints.
- Produced machine-readable schema snapshots and source contracts.
- Produced human-readable contract guidance for normalization and quality-marker handling.

### When
- Completed on 2026-03-28 before finalizing production Bronze ingestion logic.

### Where
- Artifacts and narrative:
	- `docs/phase_03/artifacts/RAW_PROFILING_SUMMARY.md`
	- `docs/phase_03/artifacts/schema_snapshots.json`
	- `docs/phase_03/artifacts/source_contracts.json`
	- `docs/phase_03/SOURCE_CONTRACTS.md`
- Execution/test entrypoints:
	- `src/profiling/profile_raw_sources.py`
	- `tests/test_phase03_contracts.py`

### Why
- Source files are heterogeneous and contain critical parsing variability (encoding, header offsets, markers).
- Without explicit contracts, ingestion can silently drift or fail with low observability.
- Contracting early reduces fragile assumptions in downstream Bronze/Silver logic.

### How
- Ran file-type-specific profiling logic for CSV/XLSX/XML.
- Captured detected encodings/delimiters/header starts, inferred field shapes, and marker distributions.
- Encoded contract rules for required geo/time keys and accepted quality markers.
- Added reproducible generation command and tests to guard against artifact regressions.

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

## High-Signal Profiling Outcomes
- CSV statistical files require dynamic true-start detection due to metadata/header noise.
- Core CSV encoding/delimiter expectations are stable enough to codify (`iso-8859-1`, `;`).
- XML source exposes canonical dimensional axes required for flattening (`KREISE`, `JAHR`, and thematic dimensions).
- Quality-marker conventions are consistent across files and can be centralized (`-`, `.`, `x`, `X`, `e`).

## Contract Guarantees Established
- Every profiled source has a machine-readable contract artifact.
- Required dimension policy is explicit: geo key (`AGS` or `KREISE`) + time key (`JAHR`).
- Normalization contract is explicit: AGS formatting, abbreviation handling, and metadata-row trimming.

## Completion Checklist
- [x] Profile each CSV for encoding, separator, header offset, and metadata noise.
- [x] Profile XML hierarchy and flattening-relevant structure.
- [x] Identify core dimensions used for cross-stage harmonization.
- [x] Define machine-readable source contracts with required rules and quality markers.
- [x] Persist schema snapshots and profiling summary artifacts.
- [x] Add test coverage for contract artifact generation.

## Key Decisions and Trade-offs
- Decision: maintain both machine-readable (`json`) and narrative (`md`) contract views.
	- Benefit: automation + human interpretability.
	- Trade-off: dual maintenance burden.
- Decision: tolerate known workbook formatting warnings during profiling while validating output artifacts.
	- Benefit: avoids blocking progress on non-fatal source quirks.
	- Trade-off: warning management needed to preserve log signal quality.
- Decision: profile-driven ingestion strategy over hand-authored assumptions.
	- Benefit: robust to source variation.
	- Trade-off: more initial implementation complexity in parser logic.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| XLSX parsing warning (`Workbook contains no default style`) during profiling | Source workbook formatting omits a default style entry | Cosmetic warning noise; potential concern about parse fidelity | Continued read-only profiling with `openpyxl` and validated extracted header rows/columns in artifacts | Keep parser warnings non-fatal and validate schema output artifacts in tests |

## Residual Risks
- Upstream agencies may introduce schema/metadata drift not covered in current profiles.
- Some semantic labels may require contextual interpretation in Silver harmonization.

## Handoff Readiness (to Phase 04)
- Contract artifacts and parsing rules are sufficient to implement resilient Bronze ingestion.
- Known source quirks are documented with actionable parser policies.
- No unresolved contract blocker remains for ingestion implementation.
