# Defense Script and Q&A Risk Log (Phase 10)

## 7-Minute Defense Script

### 1. Problem and policy value (1 minute)
- This project measures where educational talent leakage occurs between school progression, graduation, university entry, and completion.
- It provides district-level evidence to prioritize interventions with finite public resources.

### 2. Data and engineering approach (2 minutes)
- Multi-format public statistics are ingested with robust parsing for messy metadata and encoded inputs.
- Data is normalized into Bronze parquet, modeled in dbt Silver/Gold on DuckDB, and protected by quality gates.
- Historical district dimension handling is implemented with snapshots to support boundary-change-aware analysis.

### 3. Analytical outputs (2 minutes)
- Leakage funnel quantifies drop-offs across five stages.
- District anomaly map prioritizes where completion and leakage divergence is largest.
- Subject resilience analysis identifies differential completion by examination group.
- Clustering and forecasts provide segmentation and short-term planning signals.

### 4. Reliability and reproducibility (1 minute)
- End-to-end commands and CI workflows reproduce modeled outputs from clean checkout.
- dbt tests, governance checks, and run artifacts provide traceable evidence.

### 5. Limits and governance posture (1 minute)
- Results are ecological and district-level, not causal or individual-level.
- Forecasts are directional planning aids and include fallback behavior.
- Warning-level dependency deprecations are monitored and tracked as maintenance debt.

## Q&A Risk Log

| Likely Question | Risk | Answer Strategy | Supporting Evidence |
|---|---|---|---|
| Are results reproducible by another reviewer? | Credibility risk if no deterministic run path | Show execution order and CI checks; reference artifacts and commands | `docs/phase_10/THESIS_APPENDIX_EVIDENCE.md`, `.github/workflows/` |
| How do you handle changing district boundaries? | Time-series comparability risk | Demonstrate SCD snapshot timeline toggle and historical validity columns | `snapshots.snap_district_boundaries`, `app/main.py` |
| Are these causal claims about migration/background? | Ethical and methodological risk | State clearly: observational descriptive analytics, not causal inference | Phase docs and dashboard narrative |
| Why trust quality of source transformations? | Data integrity risk | Present dbt tests + quality checker outputs and thresholds | `phase08_quality_report.json`, dbt test suite |
| Could the model fail in production due to package drift? | Operational risk | Explain pinned dependencies, CI checks, and warning monitoring policy | `pyproject.toml`, Phase 08 warning policy |
| Why are map coordinates not official geometries in CI mode? | Interpretation risk | Clarify pseudo-coordinate mode is deterministic fallback for environment portability; production can swap official geometry layer | Dashboard caption and Phase 10 notes |
