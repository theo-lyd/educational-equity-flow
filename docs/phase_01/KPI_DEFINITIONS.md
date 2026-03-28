# Phase 01 KPI Definitions

## Entity grain
District (`ags_5`) x reference period (`year` or `school_year`) x cohort segment (`gender`, `nationality_group`) x subject group (where applicable).

## Stage model
- Stage 1: 7th grade cohort pool
- Stage 2: 11th grade continuation
- Stage 3: school completion (abitur/related completion outcomes)
- Stage 4: university enrollment/student stage
- Stage 5: university completion (passed exams/degrees)

## Core KPI formulas

1. Stage transition rate
$$
T_{i\rightarrow j}(d,t,g,n)=\frac{N_j(d,t,g,n)}{N_i(d,t,g,n)}\times 100
$$

2. Stage leakage rate
$$
L_{i\rightarrow j}(d,t,g,n)=100-T_{i\rightarrow j}(d,t,g,n)
$$

3. International-domestic leakage differential
$$
\Delta L_{i\rightarrow j}(d,t,g)=L^{intl}_{i\rightarrow j}(d,t,g)-L^{dom}_{i\rightarrow j}(d,t,g)
$$

4. Full funnel retention (Stage 1 to Stage 5)
$$
R_{1\rightarrow 5}(d,t,g,n)=\frac{N_5(d,t,g,n)}{N_1(d,t,g,n)}\times 100
$$

5. Full funnel leakage
$$
L_{1\rightarrow 5}(d,t,g,n)=100-R_{1\rightarrow 5}(d,t,g,n)
$$

6. Subject-level completion share (HS-FG2)
$$
S_{fg}(d,t,n)=\frac{N_{5,fg}(d,t,n)}{\sum_{fg}N_{5,fg}(d,t,n)}\times 100
$$

## District resilience score (initial definition)
Weighted score where higher is better:
$$
Resilience(d,t)=w_1\cdot T_{1\rightarrow2}+w_2\cdot T_{2\rightarrow3}+w_3\cdot T_{3\rightarrow4}+w_4\cdot T_{4\rightarrow5}-w_5\cdot |\Delta L_{1\rightarrow5}|
$$

Default weights for baseline implementation:
- `w1 = 0.20`
- `w2 = 0.20`
- `w3 = 0.25`
- `w4 = 0.25`
- `w5 = 0.10`

## KPI quality constraints
- Rates must be in `[0, 100]`.
- Denominator must be positive for transition calculations.
- Null-safe behavior: return `null` when denominator is zero.
- AGS keys must be standardized before KPI joins.

## Acceptance thresholds for Phase 01 completion
- All KPI formulas documented and mathematically explicit.
- Grain definition and denominator policy fixed.
- Stage 5 integrated into canonical funnel model.
