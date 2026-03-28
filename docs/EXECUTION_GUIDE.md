# Educational Equity & Talent Leakage Pipeline

This is your end-to-end, phase-by-phase execution guide for building a production-grade analytics engineering capstone in this repository.

It is designed for:
- A complete beginner implementing an industry-standard data platform.
- MSc thesis quality (technical rigor + reproducibility + presentation quality).
- Guided delivery through this chat, where I execute the project files/code and you provide prompts/decisions.

---

## 0) How We Will Work Together

You asked for hands-on execution. We will use this operating model:

1. You prompt phase by phase (or ask me to continue automatically).
2. I implement code, configs, tests, docs, and CI directly in this repo.
3. I run commands, debug, validate, and report results.
4. I keep a phase-specific issue log in each phase document.

Important boundaries:
- I can fully implement code and documentation in this workspace.
- I cannot run external cloud deployments unless credentials/services are provided.
- For anything environment-specific (tokens, secrets), I will prepare exact steps and templates.

---

## 1) Project Target Architecture (What "Done" Looks Like)

At completion, this repository will contain:

- `data/raw/` source files (already present).
- `data/bronze/` cleaned partitioned parquet outputs.
- `warehouse/analytics.duckdb` (or equivalent) with modeled data.
- `src/` Python ingestion + ML + forecasting modules.
- `dbt/` project with staging/intermediate/marts + snapshots + tests.
- `great_expectations/` validations for quality gates.
- `.github/workflows/` CI pipelines for tests, dbt slim CI, freshness checks.
- `app/` Streamlit dashboard for policy storytelling.
- `docs/phases/` phase records, decision logs, issue logs, and evidence.

### Source of Truth Matrix (Pinned Primary/Fallback Files)

Use one canonical source per stage for production transformations. Keep fallback files for reconciliation and ingestion resilience tests.

| Funnel Stage | Metric Intent | Primary File | Fallback File(s) | Notes |
|---|---|---|---|---|
| Stage 1 | 7th grade pipeline pool | `data/raw/21111-01-03-4.xlsx` | `data/raw/21111-01-03-4-B.xlsx` | Same table family; primary uses regional depth suitable for district analysis. |
| Stage 2 | 11th grade academic-track continuation | `data/raw/21111-01-03-4.xlsx` | `data/raw/21111-01-03-4-B.xlsx` | Extracted from the same school table by class/year dimension. |
| Stage 3 | School completion / graduation outcome | `data/raw/21111-02-06-4-B.csv` | `data/raw/21111-02-06-4.csv` | Use one variant as canonical to avoid double counting. |
| Stage 4 | University student/enrollment stage | `data/raw/21311-01-01-4-B.csv` | `data/raw/21311-01-01-4.xlsx` | CSV is easier for automated ingestion; XLSX retained for parity checks. |
| Stage 5 | Degree/exam completion outcome | `data/raw/21321-01-01-4_flat.csv` | `data/raw/21321-01-01-4-B.xml` | Flat CSV is canonical for marts; XML is mandatory for multi-format ingestion demonstration. |
| Cross-stage keying | AGS and district harmonization | All above | N/A | AGS standardization macro in dbt remains the single key policy. |

Source control policy:
- Never aggregate primary and fallback for the same stage in the same run.
- Use fallback only for one of: missing primary source, schema drift fallback, parity/reconciliation tests.
- Record the active source choice per run in `metadata_manifest.json`.

### Execution Order by Stage (Commands + Expected Outputs)

Run stages in this order so outputs stay deterministic and easy to debug.

| Order | Stage | Exact Run Command | Expected Output |
|---|---|---|---|
| 1 | Stage 1 + Stage 2 ingestion (school base and continuation) | `python -m src.ingestion.run --stage stage_1_2 --source data/raw/21111-01-03-4.xlsx` | Bronze parquet partitions for stage 1/2 created in `data/bronze/school/`; manifest updated with file hash, row counts, and run timestamp. |
| 2 | Stage 3 ingestion (school completion) | `python -m src.ingestion.run --stage stage_3 --source data/raw/21111-02-06-4-B.csv` | Bronze parquet for completion outcomes in `data/bronze/graduation/`; metadata rows removed; typed columns validated. |
| 3 | Stage 4 ingestion (university enrollment/student stock) | `python -m src.ingestion.run --stage stage_4 --source data/raw/21311-01-01-4-B.csv` | Bronze parquet in `data/bronze/university_enrollment/`; AGS and demographic fields normalized. |
| 4 | Stage 5 ingestion (flat completion source) | `python -m src.ingestion.run --stage stage_5 --source data/raw/21321-01-01-4_flat.csv` | Bronze parquet in `data/bronze/university_completion/`; HS-FG2 subject groups preserved for STEM analytics. |
| 5 | Stage 5 XML parity run (multi-format proof) | `python -m src.ingestion.run --stage stage_5_xml --source data/raw/21321-01-01-4-B.xml` | Flattened XML parquet generated in `data/bronze/university_completion_xml/`; row-level parity check report against flat CSV output. |
| 6 | Silver harmonization | `dbt run --select staging intermediate` | Conformed silver models built with AGS standardization and cohort-ready joins. |
| 7 | Silver quality gate | `dbt test --select staging intermediate` | All key integrity/uniqueness/not-null tests pass, or failing entities are explicitly listed. |
| 8 | Gold leakage marts | `dbt run --select marts` | Final funnel, transition, leakage differential, and subject-level marts materialized. |
| 9 | Gold quality + governance checks | `great_expectations checkpoint run leakage_pipeline_checkpoint` | GE validation results generated; critical failures block progression. |
| 10 | Intelligence layer | `python -m src.ml.run_all` | Cluster assignments and 5-year forecasts generated in `warehouse/artifacts/`. |
| 11 | Dashboard run | `streamlit run app/main.py` | Interactive dashboard starts and loads funnel, anomaly, and timeline views from gold outputs. |

Acceptance checks after stage execution:
- `data/bronze/` contains new partition folders for each completed stage.
- `metadata_manifest.json` reflects only changed/new source processing.
- Silver and gold runs produce no unresolved key mismatches on AGS/time joins.
- Stage 5 flat and XML outputs are reconcilable within defined tolerance.

---

## 2) Execution Phases Overview

1. Phase 01: Scope Freeze & Thesis Framing
2. Phase 02: Environment & Repo Foundation
3. Phase 03: Data Profiling and Source Contracts
4. Phase 04: Bronze Ingestion Engine (CSV + XML -> Parquet)
5. Phase 05: Silver Layer with dbt (Harmonization + SCD)
6. Phase 06: Gold Marts (Leakage Funnel + Transition Rates)
7. Phase 07: ML Clustering + Forecasting
8. Phase 08: Data Quality, Governance, and SLAs
9. Phase 09: Orchestration and CI/CD Automation
10. Phase 10: Dashboard, Thesis Evidence, and Defense Prep

Each phase has an individual file in `docs/phases/` with objective(s), deliverable(s), concrete tasks, done criteria, and an issue log.

---

## 3) Detailed Phase-by-Phase Guide

## Phase 01: Scope Freeze & Thesis Framing
Objective(s)
- Convert the project brief into formal research + engineering scope.
- Define measurable success criteria for your MSc and stakeholder value.

Deliverable(s)
- Problem statement, research questions, KPIs, and acceptance criteria.
- Architecture and data-flow diagram v1.
- Thesis-quality project charter.

Concrete tasks
- Define core KPIs:
  - International retention rate between each education stage.
  - Leakage differential (international vs domestic).
  - District resilience score.
  - Stage-5 completion metrics using examination dataset.
- Define hypotheses for analysis (example: districts with high enrollment but low completion indicate structural barriers).
- Define non-functional requirements:
  - Reproducibility, lineage, quality thresholds, freshness SLA.
- Define out-of-scope items to avoid scope creep.

Done criteria
- A signed-off `Phase 01` doc with clear KPI formulas and success criteria.
- Reviewer can understand what business/policy decision this system enables.

---

## Phase 02: Environment & Repo Foundation
Objective(s)
- Create a reliable local engineering environment and project scaffolding.

Deliverable(s)
- Dependency management (`pyproject.toml` or `requirements.txt`).
- Standard folders (`src`, `dbt`, `tests`, `docs`, `app`, `warehouse`).
- Initial Makefile/tasks and pre-commit quality checks.

Concrete tasks
- Install and pin:
  - Python 3.11+
  - DuckDB
  - Polars/Pandas
  - dbt-duckdb
  - Great Expectations
  - scikit-learn
  - prophet
  - streamlit
- Add basic commands:
  - `make ingest`
  - `make dbt-run`
  - `make test`
  - `make app`
- Add lint/format tooling (ruff + black or equivalent).
- Create a `.env.example` for future secret/config patterns.

Done criteria
- `pip install` and basic commands run without errors.
- Repo has predictable structure and entrypoints.

---

## Phase 03: Data Profiling and Source Contracts
Objective(s)
- Understand the real structure, encoding, and quirks of all raw datasets.

Deliverable(s)
- Data profiling report and source contracts (schema expectations per file).
- Parsing strategy for metadata headers/footers and `ISO-8859-1`.

Concrete tasks
- Profile each raw file:
  - Detect separator, encoding, header start line, null markers.
  - Identify key columns (`AGS`, year, gender, nationality dimensions).
  - Identify scaling abbreviations (`dar.`, `Mio`, `K`) and normalization rules.
- Profile XML structure (`21321-01-01-4-B.xml`):
  - Map hierarchical paths to flat columns.
- Define source contracts:
  - Required columns, datatypes, accepted value ranges.

Done criteria
- Contracts exist and can be referenced by ingestion tests.
- No unknown critical field remains unexplained.

---

## Phase 04: Bronze Ingestion Engine (CSV + XML -> Parquet)
Objective(s)
- Build resilient ingestion that transforms messy source files into clean bronze parquet.

Challenge context to implement explicitly
- Input CSVs can contain 5-10 lines of unstructured metadata headers/footers and `ISO-8859-1` encoding.
- Ingestor must detect the true tabular start dynamically (for example `AGS` token or first valid year row).
- Normalization must handle German shorthand/scales (for example `dar.` = `darunter`, `Mio`, `K`) before typing.
- Bronze output must be partitioned parquet for efficient DuckDB analytics.
- Late-arriving regional data must be supported through manifest-driven upsert behavior.

Deliverable(s)
- Python ingestion modules for CSV and XML.
- Partitioned parquet outputs with metadata manifest and upsert behavior.

Concrete tasks
- Implement `src/ingestion/scan_true_start.py`:
  - Search for the true tabular start row using markers like `AGS` or a valid year token.
- Implement `src/ingestion/csv_ingestor.py`:
  - Read `ISO-8859-1` safely.
  - Drop non-data rows/footers (including variable-length metadata blocks).
  - Normalize column names and dimension values.
- Implement `src/ingestion/xml_ingestor.py`:
  - Parse hierarchical XML and flatten to long format.
- Implement normalization helpers:
  - Zero-pad AGS to 5.
  - Convert scaled values (`Mio`, `K`) to integer counts.
  - Expand abbreviations (for example `dar.` -> `darunter`) for consistent semantics.
  - Standardize gender/nationality labels.
- Implement manifest logic:
  - `metadata_manifest.json` tracks processed file hash + ingest timestamp + row counts.
  - Reprocess only changed/new files.
  - Support regional late-arrivals (for example Bavaria) without full historical reprocessing.
- Write bronze parquet partitioning strategy:
  - By dataset + year (and optionally region/state).

Done criteria
- All raw datasets ingest successfully to bronze parquet.
- Re-running ingestion without changes is idempotent.
- Changed file triggers targeted re-ingestion only.

---

## Phase 05: Silver Layer with dbt (Harmonization + SCD)
Objective(s)
- Harmonize multiple datasets into coherent analytic entities with historical correctness.

Deliverable(s)
- dbt project with staging/intermediate models, snapshots, tests, and docs.

Concrete tasks
- Initialize dbt project configured for DuckDB.
- Build `stg_*` models:
  - One per source domain with strict casting and standard naming.
- Add AGS macro:
  - Central macro for zero-padding and null-safe key cleaning.
- Add conformed dimensions:
  - District, time, demographic, subject group.
- Build cohort-alignment models:
  - Window functions to compare cohorts through stages over time.
- Add SCD Type 2 snapshot for district boundary changes:
  - Preserve historical records for merged districts.
- Implement dbt tests:
  - Uniqueness, not-null, accepted values, relationships.

Done criteria
- `dbt run` + `dbt test` pass.
- Silver schema supports stable joins across all pipeline stages.
- Historical district logic validated on sample merger scenario.

---

## Phase 06: Gold Marts (Leakage Funnel + Transition Rates)
Objective(s)
- Build decision-ready marts that quantify educational leakage and resilience.

Deliverable(s)
- Gold tables powering policy analysis and dashboarding.

Concrete tasks
- Create stage-level metric models:
  - Stage 1: 7th Grade
  - Stage 2: 11th Grade
  - Stage 3: Graduation (Abitur)
  - Stage 4: University enrollment
  - Stage 5: Degree completion (new exam statistics data)
- Create transition mart:
  - Transition rates between stages per district/year/cohort.
- Create leakage differential mart:
  - International vs domestic drop-off percentages.
- Add subject-level completion mart:
  - HS-FG2 groups for STEM talent resilience.
- Build anomaly flags:
  - Districts better/worse than expected baseline.

Done criteria
- Gold tables are queryable with consistent keys and definitions.
- KPI formulas match phase 1 definitions exactly.

---

## Phase 07: ML Clustering + Forecasting
Objective(s)
- Add intelligence layer for segmentation and forward-looking policy planning.

Deliverable(s)
- K-Means cluster outputs and Prophet forecasts with evaluation artifacts.

Concrete tasks
- Feature engineering from gold marts:
  - Mean leakage rates, volatility, completion ratio, STEM completion share.
- Train K-Means model:
  - Determine k using elbow/silhouette.
  - Label clusters as policy narratives (High Performer, High Leakage, etc.).
- Train Prophet model:
  - Forecast international university completion/enrollment (5 years).
- Evaluate and stress-test assumptions:
  - Backtesting where possible.
- Save model artifacts and reproducible scoring scripts.

Done criteria
- Cluster assignments and forecasts regenerate deterministically.
- Model limitations and assumptions are documented clearly.

---

## Phase 08: Data Quality, Governance, and SLAs
Objective(s)
- Treat data as a product: enforce quality, integrity, and freshness.

Deliverable(s)
- Great Expectations suites, dbt test coverage, freshness policy checks, and alert logic.

Concrete tasks
- Great Expectations checks:
  - `expect_column_values_to_be_between(0, 100)` for rates.
  - Cross-table referential checks (district/time links).
  - Null and schema drift detection.
- Freshness monitor:
  - Validate latest `Stichtag` freshness threshold.
- Build quality gate command:
  - Pipeline fails if critical tests fail.
- Define severity tiers:
  - Warning vs hard-fail quality rules.

Done criteria
- Failing data quality scenario is correctly caught and reported.
- CI blocks merge on critical failures.

---

## Phase 09: Orchestration and CI/CD Automation
Objective(s)
- Automate repeatable runs and production-style validation on every PR.

Deliverable(s)
- GitHub Actions workflows for lint/test/dbt/quality/freshness.

Concrete tasks
- Create workflows:
  - Python unit tests and linting.
  - dbt slim CI (state-aware model testing).
  - Freshness SLA monitor.
- Add artifacts and logs for traceability.
- Add branch protection-compatible checks.
- Optional scheduled run (daily/weekly).

Done criteria
- PR triggers all required checks automatically.
- Failures are visible and actionable via logs.

---

## Phase 10: Dashboard, Thesis Evidence, and Defense Prep
Objective(s)
- Deliver an executive-facing narrative tool and academic-grade evidence package.

Deliverable(s)
- Streamlit app + reproducible figures + thesis appendix evidence.

Concrete tasks
- Build dashboard pages:
  - Leakage funnel (Sankey).
  - District anomaly map (choropleth).
  - SCD timeline toggle (historical vs current boundaries).
  - Subject-level STEM resilience insights.
- Add methodology page:
  - Data lineage, caveats, assumptions, quality status.
- Build thesis evidence pack:
  - Architecture diagrams.
  - Model cards.
  - Test coverage summary.
  - Reproducibility instructions.
- Prepare defense script:
  - Problem -> architecture -> quality -> insights -> limitations -> policy actions.

Done criteria
- A reviewer can reproduce results from clean checkout.
- Dashboard and thesis appendix show traceability from raw data to policy insight.

---

## 4) Cross-Phase Documentation Standard (Mandatory)

For each phase file in `docs/phases/`, always maintain:

- `Objectives`
- `Deliverables`
- `Task Checklist`
- `Validation Evidence`
- `Issues Encountered` with:
  - Problem
  - Root cause
  - Potential implications
  - Resolution
  - Prevention action

This directly satisfies your requirement to document issues phase-by-phase for expert review.

---

## 5) Suggested Milestone Timeline (Beginner-Friendly)

- Week 1: Phases 01-02
- Week 2: Phase 03
- Week 3-4: Phase 04
- Week 5-6: Phase 05
- Week 7: Phase 06
- Week 8: Phase 07
- Week 9: Phase 08
- Week 10: Phase 09
- Week 11-12: Phase 10 + thesis packaging

---

## 6) Definition of Final Project Success

Your capstone is successful when all are true:

- End-to-end run works from raw files to dashboard.
- Data quality checks and CI gates are active and meaningful.
- Leakage metrics are explainable and reproducible.
- Stage 5 completion data from exam statistics is fully integrated.
- District-level and subject-level insights support actionable policy narratives.
- Documentation is strong enough for both industry experts and professors.

---

## 7) How to Prompt Me Next

Use any of these:

- "Start Phase 01 and implement everything needed."
- "Execute Phase 02 now and run validations."
- "Continue to the next phase automatically until blocked."
- "Show me what is completed vs pending across all phases."

I will execute code directly in this workspace, keep docs updated, and include issue logs per phase as we progress.
