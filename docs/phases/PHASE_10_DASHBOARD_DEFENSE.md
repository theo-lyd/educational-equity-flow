# Phase 10: Dashboard, Thesis Evidence & Defense

Status: Completed (2026-03-29)

## Objective(s)
- Deliver executive storytelling and thesis-grade reproducibility evidence.

## 5W1H

- What: Built a data-driven Streamlit dashboard with leakage funnel, district anomaly map, SCD boundary timeline toggle, and subject resilience views; added thesis appendix and defense/Q&A artifacts.
- Why: Convert technical pipeline outputs into interpretable policy storytelling while preserving reproducibility and technical defense readiness.
- Who: Project maintainer and Copilot coding agent as implementation owner; thesis reviewers and policy stakeholders as end users.
- Where: `app/main.py`, `src/dashboard/phase10.py`, `docs/phase_10/*`, and Phase 10 run records in this document.
- When: Implemented after CI/CD hardening and governance closure (Phase 09).
- How: Queried Gold/Snapshot tables from DuckDB, rendered interactive visuals with Streamlit + Altair, and documented defense evidence and risk responses.

## Deliverable(s)
- Streamlit dashboard, thesis appendix artifacts, defense narrative.

### Delivered Assets

- Dashboard implementation:
	- `app/main.py`
	- `src/dashboard/phase10.py`
	- `src/dashboard/__init__.py`
- Thesis evidence appendix:
	- `docs/phase_10/THESIS_APPENDIX_EVIDENCE.md`
- Defense script and risk Q&A:
	- `docs/phase_10/DEFENSE_SCRIPT_AND_QA.md`
- Test coverage for Phase 10 dashboard data logic:
	- `tests/test_phase10_dashboard.py`

## Concrete Tasks
- Build leakage funnel Sankey and district anomaly map.
- Build SCD timeline toggle (historical/current boundaries).
- Add subject-level talent resilience visuals.
- Build evidence appendix (architecture, lineage, tests, model cards).
- Prepare defense script and Q&A risk log.

### Implementation Notes

- Leakage funnel is rendered as a Sankey-style stage-flow and drop-off visual using Gold funnel aggregates.
- District anomaly map uses deterministic AGS-based pseudo-coordinates for CI-safe portability when official district geometries are not packaged.
- SCD timeline toggle switches between `int_district_current` (current) and `snapshots.snap_district_boundaries` (historical) records.
- Evidence panel surfaces phase-07/08 artifact metadata for reproducibility visibility in the dashboard.

## Done Criteria
- Reviewer can reproduce end-to-end results from clean checkout.
- Dashboard and evidence support policy interpretation and technical scrutiny.

### Done Criteria Status

- Met: Dashboard now presents phase-aligned policy visuals from warehouse Gold/Snapshot tables.
- Met: Appendix and defense narrative artifacts document reproducibility and technical scrutiny responses.
- Met: New Phase 10 data-layer tests verify deterministic coordinate mapping, funnel transform shape, and SCD mode loading behavior.

## Validation Evidence
- Add reproducibility run logs and final screenshot pack.

### Executed Validation

- `make test` -> PASS (includes `tests/test_phase10_dashboard.py`)
- `DBT_THREADS=1 make dbt-run` -> PASS
- `DBT_THREADS=1 make dbt-test` -> PASS
- `make app` entrypoint available for dashboard launch and reviewer walkthrough.
- Final release pass completed across major targets; see `docs/phase_10/FINAL_RELEASE_READINESS_REPORT.md`.

### Artifact and Evidence References

- Reproducibility appendix: `docs/phase_10/THESIS_APPENDIX_EVIDENCE.md`
- Defense narrative and Q&A: `docs/phase_10/DEFENSE_SCRIPT_AND_QA.md`
- Quality evidence: `warehouse/artifacts/phase08_quality_report.json`
- ML evidence: `warehouse/artifacts/phase07_report.json`

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| District geometry files are not versioned in this workspace | Repository currently ships modeled metrics but not bundled geospatial boundary assets | A strict geo-accurate district map could not be rendered in offline/CI-safe mode | Implemented deterministic AGS-based pseudo-coordinate anomaly map and documented constraint in dashboard caption and defense log | Add optional geometry package integration path in future maintenance cycle for production-grade choropleth |
| Altair schema validation error on first dashboard run (`xOffset` unsupported) | Environment uses Altair v4 schema where `xOffset` channel is invalid | App failed at runtime before visualization render | Removed `xOffset` and rebuilt funnel view with Altair-v4-compatible encodings | Keep chart specs aligned to pinned visualization library versions and include startup smoke check |
| App launch command/path confusion caused command-not-found and subsequent connection/404 symptoms | `make app` previously relied on global `streamlit` binary availability in PATH | App could fail to start in non-activated shells, leading to failed browser/API connection attempts | Updated Makefile app target to `$(PYTHON) -m streamlit run app/main.py`; verified successful startup | Prefer environment-bound command entrypoints for all executable targets |
| Repository-wide lint gate currently fails in legacy modules | Pre-existing style/import violations in non-Phase-10 modules | Strict CI release gate cannot be fully green on `make lint` without remediation pass | Documented as non-blocking technical debt in final readiness report; runtime/data gates still pass | Schedule dedicated lint-remediation phase and then enforce lint as hard gate |

## Handoff Notes

- Phase 10 closes delivery scope across technical execution, policy visualization, and thesis defense support.
- Future improvement path: replace pseudo-coordinate map with official district shapefiles/GeoJSON once a vetted geometry source is added to repository data assets.
