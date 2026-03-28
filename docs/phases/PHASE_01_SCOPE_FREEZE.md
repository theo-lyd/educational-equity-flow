# Phase 01: Scope Freeze & Thesis Framing

Status: Completed

## Objective(s)
- Translate the brief into a measurable analytics engineering thesis scope.
- Define policy-facing KPIs and acceptance criteria.

## Deliverable(s)
- Project charter with research questions and KPI definitions.
- Scope boundaries and non-functional requirements.

Delivered artifacts
- `docs/phase_01/PROJECT_CHARTER.md`
- `docs/phase_01/KPI_DEFINITIONS.md`
- `docs/phase_01/SCOPE_BOUNDARIES.md`
- `docs/phase_01/ARCHITECTURE_V1.md`
- `data/raw/RAW_STATE_LOCK.csv`

## Concrete Tasks
- Define primary research questions and hypotheses.
- Define KPI formulas for all funnel stages (1-5).
- Define district-level resilience score logic.
- Document in-scope and out-of-scope items.
- Define acceptance criteria for technical and policy outputs.

Execution checklist
- [x] Research questions and hypotheses documented.
- [x] Five-stage KPI formulas defined (including Stage 5 completion).
- [x] District resilience score v1 defined.
- [x] Scope boundaries and assumptions documented.
- [x] Technical and policy acceptance criteria defined.
- [x] Architecture and data-flow v1 documented.
- [x] Raw data state verified and locked with deterministic hashes.

## Done Criteria
- KPI formulas are unambiguous and approved.
- Scope is frozen and recorded in this phase file.

Done criteria outcome
- Achieved. Formulas, scope, architecture, and acceptance criteria are now fixed and versioned.

## Validation Evidence
- Raw lock evidence: `data/raw/RAW_STATE_LOCK.csv`
- Charter: `docs/phase_01/PROJECT_CHARTER.md`
- KPI formulas: `docs/phase_01/KPI_DEFINITIONS.md`
- Scope boundaries: `docs/phase_01/SCOPE_BOUNDARIES.md`
- Architecture v1: `docs/phase_01/ARCHITECTURE_V1.md`

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| Raw data baseline was mutable and untracked | New raw files were added without a lock artifact | Non-reproducible KPI outputs and hard-to-audit thesis results | Generated `data/raw/RAW_STATE_LOCK.csv` with file size, timestamp, and SHA-256 for each raw file | Require lock-file refresh and review before any ingest/model run |
