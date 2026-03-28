# Phase 01 Project Charter

## Project title
Educational Equity and Talent Leakage Pipeline for German District-Level Policy Intelligence

## Thesis statement
This project builds a production-oriented analytics engineering system that tracks student progression from school to higher education completion and quantifies where international-background cohorts are disproportionately lost across the educational pipeline.

## Problem statement
Administrative education datasets are fragmented by source format, metadata conventions, and regional coding differences. Policymakers need a reproducible district-level system that explains where student leakage occurs and which districts show resilience despite structural pressure.

## Public value objective
Provide transparent, district-level evidence that supports targeted interventions for improving educational equity and retaining international talent.

## Primary stakeholders
- State and district education policymakers
- Public-sector analysts and statistical offices
- Academic supervisors and industry reviewers

## Research questions
1. At which transition stage does the largest international cohort leakage occur by district?
2. Which districts outperform expected outcomes after controlling for baseline intake levels?
3. Does leakage differ significantly between international and domestic cohorts across the same stages?
4. Which subject groups (HS-FG2) show strongest or weakest completion resilience?
5. Can short-term trends forecast future completion risk for international cohorts?

## Hypotheses
- H1: Leakage is not uniform; district-level variation is high and policy-relevant.
- H2: International cohorts have larger transition losses than domestic cohorts in at least one key stage.
- H3: Some districts are positive outliers that can be used as policy benchmarks.
- H4: Stage 5 completion metrics reveal additional leakage not visible from enrollment-only views.

## Success criteria
- End-to-end reproducibility from raw data to dashboard and quality reports.
- KPI formulas are explicit, testable, and stable across reruns.
- District-level outputs are interpretable and suitable for policy briefing.
- Historical key harmonization supports valid comparisons over time.

## Non-functional requirements
- Reproducibility: deterministic outputs from fixed inputs.
- Traceability: clear lineage from raw files to marts and dashboard.
- Data quality: automated constraints and integrity checks.
- Performance: columnar storage with partitioned parquet and DuckDB.
- Maintainability: modular Python plus dbt models and tests.

## Risks and mitigations
- Source schema drift: mitigated by source contracts and manifest checks.
- Regional key inconsistency: mitigated by AGS standardization rules.
- Metadata row noise in CSV: mitigated by true-start detection.
- Misinterpretation risk: mitigated by methodology and caveat notes in dashboard.
