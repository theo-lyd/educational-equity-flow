# Phase 05: Silver Layer (dbt Harmonization + SCD)

## Objective(s)
- Build harmonized, historically consistent analytical entities.

## Deliverable(s)
- dbt staging/intermediate models, macros, snapshots, tests.

## Concrete Tasks
- Initialize dbt-duckdb project and source definitions.
- Build stg models with standardized naming and types.
- Add AGS standardization macro (zero-padding to 5).
- Implement conformed dimensions and cohort alignment logic.
- Implement SCD Type 2 snapshots for district boundary changes.
- Add dbt tests (not null, unique, accepted values, relationships).

## Done Criteria
- dbt run/test passes.
- Historical and current boundary views are both supported.

## Validation Evidence
- Add dbt docs artifacts and test result logs.

## Issues Encountered
| Problem | Root Cause | Potential Implication(s) | Resolution | Prevention Action |
|---|---|---|---|---|
| None yet | - | - | - | - |
