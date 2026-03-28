# Phase 02: Environment & Repository Foundation

Status: Completed (2026-03-28)

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
- `make ingest`: completed; generated `warehouse/artifacts/ingest_smoke.json`.
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

## Completion Checklist
- [x] Core folders scaffolded (`src`, `dbt`, `tests`, `app`, `warehouse`).
- [x] Pinned dependency management added (`pyproject.toml`).
- [x] Lint/format/test tooling configured (`ruff`, `black`, `pytest`).
- [x] Task runner commands added in `Makefile` (`ingest`, `dbt-run`, `test`, `app`).
- [x] Baseline command execution validated.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| dbt command needed to work before dbt project exists | Phase 02 intentionally scaffolds command interface before Phase 05 dbt modeling | Baseline setup could fail and block progression | Implemented a defensive dbt wrapper that no-ops with clear message when `dbt_project.yml` is absent | Keep wrappers phase-aware so early phases remain executable and deterministic |
| Initial virtual environment had no `pip` module | Existing `.venv` was not created with pip bootstrap | Dependency installation and command validation would fail | Recreated `.venv` with `virtualenv` and installed pinned packages successfully | Standardize setup with `virtualenv .venv` before first `make install` |
| Install-path overlap in quickstart created avoidable dependency reinstalls | README previously suggested bootstrap steps that could be interpreted as sequentially cumulative | Longer setup time and higher confusion risk for contributors | Split setup into mutually exclusive commands: `setup-venv` and `setup-venv-req`; documented one-path-only usage | Keep one recommended default path and document alternatives as explicit substitutes |
| Pyproject-first setup initially failed during editable install | Hatch build target was not explicitly configured for current package layout (`src`) | Default modern setup path was non-functional | Added `[tool.hatch.build.targets.wheel] packages = ["src"]` to `pyproject.toml` and re-validated bootstrap | Validate both setup personas whenever packaging metadata changes |
