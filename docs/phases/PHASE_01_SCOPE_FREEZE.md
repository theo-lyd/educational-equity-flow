# Phase 01: Scope Freeze & Thesis Framing

Status: Completed (2026-03-28)

## 5W1H (Who, What, When, Where, Why, How)

### Who
- Project owner and thesis author as business/problem owner.
- Copilot coding agent as implementation/documentation support.
- Primary future consumers: policy analysts, reviewers, and downstream phase implementers.

### What
- Converted the high-level project brief into a bounded, measurable thesis/engineering scope.
- Defined canonical KPI formulas for the five-stage educational funnel.
- Defined resilience-score intent and acceptance criteria for technical and policy outputs.
- Locked the raw-file baseline to guarantee reproducibility across subsequent phases.

### When
- Completed during project bootstrap window before any heavy code implementation.
- Baseline lock and scope freeze recorded on 2026-03-28.

### Where
- Scope artifacts:
	- `docs/phase_01/PROJECT_CHARTER.md`
	- `docs/phase_01/KPI_DEFINITIONS.md`
	- `docs/phase_01/SCOPE_BOUNDARIES.md`
	- `docs/phase_01/ARCHITECTURE_V1.md`
- Reproducibility lock artifact:
	- `data/raw/RAW_STATE_LOCK.csv`

### Why
- Without explicit scope and KPI definitions, downstream phases risk inconsistent metric semantics.
- Without a raw baseline lock, analyses cannot be defended as reproducible in thesis or policy contexts.
- This phase establishes a shared contract for all later engineering/modeling decisions.

### How
- Drafted charter, research questions, and hypotheses with policy relevance.
- Formalized stage KPI formulas and target interpretations.
- Documented in-scope/out-of-scope boundaries and non-functional requirements.
- Generated lockfile entries (hash + size + timestamp) for raw-state immutability checks.

## Objective(s)
- Translate the brief into a measurable analytics engineering thesis scope.
- Define policy-facing KPIs and acceptance criteria.

## Deliverable(s)
- Project charter with research questions and KPI definitions.
- Scope boundaries and non-functional requirements.
- Raw-state lock for deterministic pipeline execution.

## Concrete Tasks
- Define primary research questions and hypotheses.
- Define KPI formulas for all funnel stages (1-5).
- Define district-level resilience score logic.
- Document in-scope and out-of-scope items.
- Define acceptance criteria for technical and policy outputs.
- Record immutable raw baseline lock for reproducibility.

## Completion Checklist
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
- Raw-state lock can be used to detect drift before running any transformation layer.

## Validation Evidence
- Raw lock evidence: `data/raw/RAW_STATE_LOCK.csv`.
- Charter: `docs/phase_01/PROJECT_CHARTER.md`.
- KPI formulas: `docs/phase_01/KPI_DEFINITIONS.md`.
- Scope boundaries: `docs/phase_01/SCOPE_BOUNDARIES.md`.
- Architecture v1: `docs/phase_01/ARCHITECTURE_V1.md`.

## Key Decisions and Trade-offs
- Decision: Treat this phase as a semantic contract layer, not a coding phase.
	- Benefit: downstream phases can move faster with less ambiguity.
	- Trade-off: requires up-front detail before visible implementation output.
- Decision: enforce raw lockfile early.
	- Benefit: traceable reproducibility and easier root-cause analysis for data drift.
	- Trade-off: lock refresh process adds governance overhead when raw files change.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| Raw data baseline was mutable and untracked | New raw files were added without a lock artifact | Non-reproducible KPI outputs and hard-to-audit thesis results | Generated `data/raw/RAW_STATE_LOCK.csv` with file size, timestamp, and SHA-256 for each raw file | Require lock-file refresh and review before any ingest/model run |

## Residual Risks
- KPI definitions may still require semantic refinement after observing modeled outputs in later phases.
- Administrative boundary changes can affect district comparability and must be addressed in Silver snapshots.

## Handoff Readiness (to Phase 02)
- Scope and KPI semantics are sufficiently stable for implementation.
- Reproducibility policy is established.
- No blocking ambiguity remains for environment/repository foundation work.
