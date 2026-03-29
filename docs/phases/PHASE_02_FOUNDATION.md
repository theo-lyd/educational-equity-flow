# Phase 02: Environment & Repository Foundation

Status: Completed (2026-03-28)

## 5W1H (Who, What, When, Where, Why, How)

### Who
- Project maintainer as environment owner.
- Copilot coding agent as implementation/validation support.
- Future contributors and CI runners as consumers of this reproducible baseline.

### What
- Established a deterministic Python project foundation and command surface.
- Added dependency management in both modern (`pyproject.toml`) and compatibility (`requirements*.txt`) forms.
- Added consistent local task entrypoints via `Makefile`.
- Added baseline application, ingestion, and dbt command wrappers.

### When
- Completed on 2026-03-28 during project bootstrapping before Phase 03/04 code expansion.

### Where
- Core artifacts:
	- `pyproject.toml`
	- `requirements.txt`
	- `requirements-dev.txt`
	- `Makefile`
	- `.env.example`
	- `README.md`
- Scaffold folders:
	- `src/`, `tests/`, `app/`, `dbt/`, `warehouse/`

### Why
- Later phases (profiling, ingestion, dbt modeling) are fragile without deterministic tooling.
- A shared command interface reduces onboarding friction and execution mistakes.
- Reproducible dependency locking prevents inconsistent local/CI behavior.

### How
- Created scaffold directories and baseline module entrypoints.
- Pinned dependencies and dev tools.
- Added `Makefile` tasks for setup, tests, ingestion, dbt wrapper, and app run.
- Validated setup paths (pyproject-first and requirements-first) and corrected packaging metadata.
- Hardened command reproducibility by preferring `.venv/bin/python` when present.

## Objective(s)
- Establish reproducible local development and project scaffolding.

## Deliverable(s)
- Dependency files, folder structure, and executable project commands.

## Concrete Tasks
- Create core folders: src, dbt, tests, app, warehouse, docs.
- Add dependency management and pinned versions.
- Add lint/format/test tooling and base config.
- Add task runner commands (ingest, dbt, test, app).
- Validate first clean setup run.

## Done Criteria
- A fresh environment can install and run baseline commands.
- Project structure is ready for implementation phases.

## Validation Evidence
- `make setup-venv`: completed after hatch wheel config fix; editable install works.
- `make setup-venv-req`: completed; requirements-based path works.
- `make ingest`: now targets Phase 04 ingestion flow and generates `warehouse/artifacts/ingest_bronze.json`.
- `make dbt-run`: completed; wrapper executed and skipped safely pending `dbt_project.yml`.
- `make test`: completed; smoke tests passed.
- `make app`: completed; Streamlit launched successfully and exposed local URL `http://localhost:8501`.

## Setup Assessment and Decisions (2026-03-28)

### Complexity Assessment
- Current setup complexity is moderate and appropriate for Phase 02.
- The baseline command surface remains small (`setup`, `ingest`, `dbt-run`, `test`, `app`) and is reproducible.

### Airflow Runtime Strategy (for Phase 09)
- Preferred default: run Airflow in Docker.
- Rationale:
	- Better dependency isolation from analytics stack libraries.
	- More reproducible onboarding and CI behavior.
	- Closer parity with production orchestration patterns.
- Non-Docker Airflow is acceptable only when Docker is unavailable or restricted and the team accepts higher dependency-conflict risk.

### Redundancy Review and Resolution
- Identified redundancy:
	- Two dependency personas are supported (`pyproject.toml` and `requirements*.txt`).
	- Prior quickstart path could lead users to run overlapping installs in sequence.
- Resolution implemented:
	- `make setup-venv` is now the recommended pyproject-first bootstrap.
	- `make setup-venv-req` is the explicit requirements-first bootstrap.
	- README now instructs users to choose one path, not both.
- Policy going forward:
	- Keep `pyproject.toml` as the modern default source for local development.
	- Keep `requirements*.txt` for compatibility workflows and constrained environments.

### Reproducibility Command Policy
- `Makefile` now auto-selects `.venv/bin/python` when available.
- Rationale:
	- Avoid accidental use of system Python in fresh shells.
	- Keep `make test` / `make ingest` behavior consistent with `make setup-venv` outputs.
- Outcome:
	- Reduced environment-dependent failures and easier local/CI parity.

## Completion Checklist
- [x] Core folders scaffolded (`src`, `dbt`, `tests`, `app`, `warehouse`).
- [x] Pinned dependency management added (`pyproject.toml`).
- [x] Lint/format/test tooling configured (`ruff`, `black`, `pytest`).
- [x] Task runner commands added in `Makefile` (`ingest`, `dbt-run`, `test`, `app`).
- [x] Baseline command execution validated.

## Key Decisions and Trade-offs
- Decision: dual dependency paths (`pyproject` and `requirements`) during early phases.
	- Benefit: supports both modern editable installs and constrained environments.
	- Trade-off: introduces documentation/maintenance overhead.
- Decision: phase-aware `dbt-run` no-op before dbt project initialization.
	- Benefit: stable command interface from day one.
	- Trade-off: command success does not yet imply modeling completeness.
- Decision: prefer virtualenv interpreter in Make targets.
	- Benefit: stronger reproducibility.
	- Trade-off: assumes `.venv` path convention.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| dbt command needed to work before dbt project exists | Phase 02 intentionally scaffolds command interface before Phase 05 dbt modeling | Baseline setup could fail and block progression | Implemented a defensive dbt wrapper that no-ops with clear message when `dbt_project.yml` is absent | Keep wrappers phase-aware so early phases remain executable and deterministic |
| Initial virtual environment had no `pip` module | Existing `.venv` was not created with pip bootstrap | Dependency installation and command validation would fail | Recreated `.venv` with `virtualenv` and installed pinned packages successfully | Standardize setup with `virtualenv .venv` before first `make install` |
| Install-path overlap in quickstart created avoidable dependency reinstalls | README previously suggested bootstrap steps that could be interpreted as sequentially cumulative | Longer setup time and higher confusion risk for contributors | Split setup into mutually exclusive commands: `setup-venv` and `setup-venv-req`; documented one-path-only usage | Keep one recommended default path and document alternatives as explicit substitutes |
| Pyproject-first setup initially failed during editable install | Hatch build target was not explicitly configured for current package layout (`src`) | Default modern setup path was non-functional | Added `[tool.hatch.build.targets.wheel] packages = ["src"]` to `pyproject.toml` and re-validated bootstrap | Validate both setup personas whenever packaging metadata changes |
| `make test` failed in non-activated shells after setup | `PYTHON` default in `Makefile` initially pointed to system interpreter | False negatives and environment confusion despite healthy `.venv` | Updated `Makefile` to prefer `.venv/bin/python` when present | Keep all project task runners interpreter-aware and test from fresh shells |

## Residual Risks
- A full dbt project is intentionally not present yet; Phase 05 must initialize model structure and profiles safely.
- Team members using custom environment layouts may still need local overrides.

## Handoff Readiness (to Phase 03)
- Environment reproducibility is established.
- Commands for profiling/testing are available and validated.
- No critical infrastructure blocker remains for source-contract profiling work.
