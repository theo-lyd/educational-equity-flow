# Dashboard and ML Functionality User Guide

**Version:** Phase 10  
**Purpose:** Complete reference for understanding, using, and interpreting the Educational Equity and Talent Leakage Observatory dashboard and forecasting pipeline

---

## Table of Contents

1. [Overview](#overview)
2. [Dashboard Features and Components](#dashboard-features-and-components)
3. [Dashboard Tabs and Charts](#dashboard-tabs-and-charts)
4. [ML Functionality](#ml-functionality)
5. [How to Use the Dashboard](#how-to-use-the-dashboard)
6. [Interpretation Guide](#interpretation-guide)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What is the Dashboard?

The **Educational Equity and Talent Leakage Observatory** is an interactive Streamlit-based dashboard that visualizes educational progression data across districts. It provides policymakers and researchers with:

- **Leakage Analysis**: Track where students drop out in the educational pipeline
- **Geographic Prioritization**: Identify districts with highest risk scores
- **Temporal Consistency**: Track boundary changes and their impact on time-series interpretation
- **Subject-Level Heterogeneity**: Understand completion rates by subject and demographic group
- **Reproducibility Evidence**: Access metadata about underlying ML models and data quality

### Key Statistics

- **Data Source**: Multiple public education registries (CSV and XML formats)
- **Time Scope**: Multi-year historical snapshot with current-year data
- **Geography**: District-level (AGS-coded administrative boundaries)
- **Coverage**: All districts across all subjects and demographic groups
- **Update Frequency**: Runs on-demand via `make app` command

### Running the Dashboard

```bash
# Activate virtual environment and run dashboard
source .venv/bin/activate
make app

# Or directly:
python -m streamlit run app/main.py
```

The dashboard will expose URLs on `localhost:8501` and network interfaces.

---

## Dashboard Features and Components

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                     │
│                  (app/main.py)                           │
├─────────────────────────────────────────────────────────┤
│  View Selector (Sidebar)                                │
│  • Dashboard Mode (Full analytics view)                 │
│  • Reviewer Walkthrough Mode (5-step guided tour)       │
├─────────────────────────────────────────────────────────┤
│           Data Layer: Dashboard Data Loaders             │
│          (src/dashboard/phase10.py)                      │
├─────────────────────────────────────────────────────────┤
│            DuckDB Analytics Database                     │
│  (warehouse/analytics.duckdb)                           │
│  • Gold Layer Tables (business facts)                    │
│  • Snapshots (historical SCD records)                    │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Raw Data** → Ingested via Bronze tables (CSV/XML parsing)
2. **Intermediate Models** → Silver layer (dimensional preparation)
3. **Business Facts** → Gold layer (district/subject/leakage aggregations)
4. **Dashboard Queries** → Data loaders fetch Gold tables and snapshots
5. **Visualization** → Altair charts and interactive Streamlit components

---

## Dashboard Tabs and Charts

### 1. **Header Section**

**Component:** Hero Banner  
**Content:**
- Title: "Educational Equity and Talent Leakage Observatory"
- Subtitle: "Phase 10 dashboard for policy interpretation, reproducibility evidence, and defense readiness"
- Visual: Gradient background with project branding colors

**Purpose:** Establish context and professional presentation for reviewers

---

### 2. **KPI Strip** (Metrics Row)

**Location:** Immediately below header  
**Contains 4 Key Metrics:**

| Metric | Field | Calculation | Purpose |
|--------|-------|-------------|---------|
| **Districts** | Count | `COUNT(DISTINCT ags)` from `gold_stage_funnel` | Shows scale of analysis (typical: 400+) |
| **Stage 1 Cohort** | `stage_1_students` | `SUM(stage_1_students)` | Total students entering Grade 7 |
| **Stage 5 Completions** | `stage_5_degree_completions` | `SUM(stage_5_degree_completions)` | Total students completing degree |
| **End-to-End Rate** | Completion Rate | `Stage 5 / Stage 1` | Overall pipeline completion percentage |

**Interpretation:**
- **Low End-to-End Rate** indicates significant leakage across the pipeline
- **Completion Rate < 50%** suggests substantial policy intervention opportunities
- Compare rate across different time periods to identify trends

**SQL Source:**
```sql
SELECT 
  COUNT(DISTINCT ags) as districts,
  SUM(stage_1_students) as stage_1,
  SUM(stage_5_degree_completions) as stage_5,
  SUM(stage_5_degree_completions) / SUM(stage_1_students) as rate
FROM gold_stage_funnel
```

---

### 3. **Leakage Funnel (Split Bar + Line Chart)**

**Location:** Dashboard mode (second section)  
**Type:** Dual visualization - Bar chart + Line chart overlay

#### Part A: Flow Volume Bar Chart

**What it shows:**
- Stacked bar chart displaying student volume at each stage transition
- X-axis: Educational stages (Grade 7 → Grade 11 → Graduation → University → Degree)
- Y-axis: Number of students flowing through each stage
- Color-coding: Each bar represents flow TO that stage (4-color palette: ocean, teal, light blue, amber)

**Bars represent:**
1. **Stage 1 → 2**: Students continuing from Grade 7 to Grade 11
2. **Stage 2 → 3**: Students graduating from secondary school
3. **Stage 3 → 4**: Students entering university
4. **Stage 4 → 5**: Students completing degree

**Example Reading:**
```
If bar heights are: 100K → 75K → 50K → 30K → 20K
- 25K students left between Grade 7 and Grade 11
- 25K students left between Grade 11 and Graduation  
- 20K students left between Graduation and University
- 10K students left between University and Degree Completion
```

#### Part B: Drop-from-Previous Line Chart

**What it shows:**
- Dashed line graph overlay showing student attrition (drop-off) at each transition
- X-axis: Same stages as bar chart
- Y-axis: Number of students lost in previous stage
- Orange dashed line indicates where "leakage" happens

**Identifying Critical Drop Points:**
- Steepest line segment = highest attrition rate
- Policy should target the stage with largest drop
- Example: If Grade 7→11 drop is largest, focus interventions on secondary school retention

**Data Calculation:**
```python
drop_from_previous = [
  Stage 1 - Stage 2 cohort,  # Primary attrition
  Stage 2 - Stage 3 cohort,  # Secondary attrition
  Stage 3 - Stage 4 cohort,  # Graduation to university gap
  Stage 4 - Stage 5 cohort,  # University to completion gap
]
```

**Tooltip Information (hover to see):**
- Source stage name
- Target stage name
- Flow volume (formatted with thousands separator)
- Drop-from-previous value

---

### 4. **District Anomaly Map**

**Location:** Dashboard mode (third section)  
**Type:** Interactive geographic bubble map with Altair

**What it depicts:**
- Each bubble = 1 district (colored dot on pseudo-geographic map)
- Location: Deterministic coordinates derived from district AGS code via MD5 hashing
- Size: Bubble size proportional to anomaly score
- Color: Intensity of orange/red indicates risk level

**Why Pseudo-Coordinates?**
- Uses deterministic MD5-based mapping for CI/reproducibility (not real lat/lon)
- Provides stable positioning across pipeline runs
- When official GeoJSON is available, can be replaced with real coordinates

### Anomaly Score Calculation

```
anomaly_score = (1.0 - end_to_end_completion_rate) + |mean_leakage_differential|

Where:
- end_to_end_completion_rate = % of students completing degree in district
- mean_leakage_differential = avg deviation from national completion norm
```

**Interpretation:**
- **High anomaly score (large orange bubble)** = District significantly underperforming
- **Low anomaly score (small pale bubble)** = District performing in line with national average
- **Red zones** = Priority districts for policy intervention

**Tooltip Details (hover over bubble):**
- AGS code: District identifier
- Region: District name
- Anomaly Score: Numeric value (0.0 to ~2.0)
- End-to-End Completion Rate: % as decimal
- Mean Leakage Differential: Numeric value showing deviation from mean

**Example Use in Q&A:**
- Q: "Which districts need the most help?" 
- A: "Click on the largest orange bubbles to identify priority districts"

---

### 5. **SCD Boundary Timeline**

**Location:** Dashboard mode (fourth section)  
**Type:** Toggle switch + interactive data table

**What is SCD (Slowly Changing Dimension)?**
- Slowly Changing Dimension = way to track changes to district boundaries over time
- Critical for correct time-series interpretation when district boundaries change

#### Mode Selection

Two radio button options:

**A) Current Mode**
- Shows active/current district records only
- Table columns: `ags`, `region`, `latest_year`, `record_type: 'current'`
- Use to understand current district landscape
- ~400 rows (one per district)

**B) Historical Mode**
- Shows all historical versions of district records with validity dates
- Table columns: `ags`, `region`, `latest_year`, `dbt_valid_from`, `dbt_valid_to`, `record_type: 'historical'`
- Snapshot records track boundary changes
- Multiple rows per district (one per boundary change period)

#### Reading the Data

**Current Mode Table:**
```
| ags      | region                | latest_year | record_type |
|----------|----------------------|-------------|-------------|
| 08111000 | Stuttgart            | 2023        | current     |
| 08115000 | Böblingen            | 2023        | current     |
```

**Historical Mode Table:**
```
| ags      | region         | dbt_valid_from | dbt_valid_to   |
|----------|----------------|----------------|----------------|
| 08111000 | Stuttgart      | 2010-01-01     | 2015-12-31     |
| 08111000 | Stuttgart      | 2016-01-01     | NULL (current) |
```

**Key Interpretation:**
- If a district has multiple `dbt_valid_from`/`dbt_valid_to` rows, boundary changed during that period
- Helps explain sudden jumps or drops in metrics when boundaries were redrawn
- `NULL` as `dbt_valid_to` indicates current active version

---

### 6. **Subject-Level Talent Resilience**

**Location:** Dashboard mode (fifth section)  
**Type:** Grouped bar chart (Altair)

**What it shows:**
- Horizontal or vertical bar chart comparing completion rates across subject groups
- X-axis: Subject groups (e.g., "Math", "Language Arts", "STEM", "Humanities", etc.)
- Y-axis: Average subject completion share (0-100%)
- Bars grouped/colored by demographic group (e.g., "All Students", "First Generation", "Low Income")

**Data Behind Chart:**

```sql
SELECT
  hs_fg2_group,                        -- Subject group
  demographic_group,                  -- Population segment
  avg(subject_completion_share) as avg_subject_completion_share,
  sum(passed_exams) as passed_exams,
  sum(total_passed_exams) as total_passed_exams
FROM gold_subject_resilience
GROUP BY 1, 2
```

**Reading the Chart:**

1. **Bar Heights**: Taller bars = higher completion rates in that subject
2. **Color Differences**: Compare colors within subject to see demographic disparities
3. **Sorted by Performance**: Subjects sorted right-to-left by best completion rate

**Tooltip Information** (hover over bar):
- Subject group name (e.g., "Mathematics")
- Demographic group (e.g., "First Generation Students")
- Average completion share as percentage
- Total passed exams (count)
- Total possible exams (count)

**Interpretation Examples:**

**Scenario 1 - Subject Disparity:**
```
Math completion: 88% (All Students), 65% (Low Income), 72% (First Gen)
→ Intervention needed in tutoring/resources for low-income students
```

**Scenario 2 - Demographic Equity Gap:**
```
All subjects show 15-20% gap between All Students and First Generation
→ System-wide access/support issue, not subject-specific
```

**Scenario 3 - Specific Subject Weakness:**
```
Language Arts: 45% (all groups), Physics: 75% (all groups)
→ Subject-specific curriculum or assessment issue
```

---

### 7. **Evidence Appendix and Defense Readiness**

**Location:** Dashboard mode (sixth/final section)  
**Type:** Two-column panel with metadata tables and narrative

#### Left Column: Reproducibility Evidence

Displays metadata from upstream ML pipeline:
- `phase07_report_present`: Boolean - Whether clustering/forecast artifacts exist
- `phase07_cluster_count`: Integer - Number of districts clusters identified
- `phase07_forecast_method`: String - Which method used (prophet, linear_trend, naive_last_value)
- `phase08_report_present`: Boolean - Whether quality governance report exists
- `phase08_status`: String - Overall status (pass/warn/fail)
- `phase08_fail_count`: Integer - Number of quality checks that failed
- `phase08_warn_count`: Integer - Number of quality checks that warned

*Example output:*
```json
{
  "phase07_report_present": true,
  "phase07_cluster_count": 6,
  "phase07_forecast_method": "prophet",
  "phase08_report_present": true,
  "phase08_status": "pass",
  "phase08_fail_count": 0,
  "phase08_warn_count": 0
}
```

#### Right Column: Defense Narrative

Four key points about evidence chain:

1. **Data Lineage**: Raw multi-format sources → contract-validated → normalized → modeled through Bronze/Silver/Gold layers
2. **Reliability**: Guarded by dbt tests, quality checks, CI pipelines protecting each merge and scheduled review
3. **Intelligence**: Clustering and forecasts segmenting districts by risk profile and generating forward planning inputs
4. **Interpretation**: Dashboard views connecting leakage dynamics to district-level and subject-level outcomes

**Purpose**: Reviewers can verify that underlying data is reproducible and quality-assured before interpreting visuals

---

### 8. **Reviewer Walkthrough Mode** (Guided Defense Presentation)

**Location:** Sidebar toggle → "Reviewer Walkthrough" option  
**Purpose:** Step-by-step narrative guide for thesis defense presentation

#### Step 1: Context
**What to say to reviewers:**
1. Start with KPI strip: district count, stage-1 cohort, completions, end-to-end rate
2. State policy question: "Where and when does educational progression leak most strongly?"
3. Clarify scope: "This is district-level observational analytics, not causal claims"

#### Step 2: Funnel
**What to show:**
1. Display stage transitions Grade 7 → degree completion
2. Point out steepest attrition step using drop-from-previous line
3. Connect to policy intervention points (e.g., "If Grade 7→11 drop is largest, target secondary retention")

#### Step 3: Geography
**What to explore:**
1. Open anomaly map to prioritize districts by risk score
2. Explain score composition: "Combines weak completion rates + high leakage differential"
3. Use tooltips for district-level Q&A detail

#### Step 4: History
**What to clarify:**
1. Toggle boundary mode between current and historical snapshots
2. Show district changes are preserved via snapshot validity columns
3. Emphasize: "This protects time-series interpretation under boundary drift"

#### Step 5: Resilience + Evidence
**Final summary:**
1. Use subject resilience view to highlight demographic/subject heterogeneity
2. Close with reproducibility status and quality report summary
3. Direct reviewers to `docs/phase_10/THESIS_APPENDIX_EVIDENCE.md` and `docs/phase_10/DEFENSE_SCRIPT_AND_QA.md`
4. Display phase 07/08 report status

---

## ML Functionality

### Location

**Main ML Pipeline:** `src/ml/run_all.py`  
**Triggered by:** `make ml-run` (part of data pipeline)  
**Outputs saved to:** `warehouse/artifacts/`

### Two-Part ML System

The ML pipeline combines two complementary approaches:

#### Part 1: District Clustering (K-Means)

**Purpose:** Group districts into policy-relevant segments based on educational progression patterns

##### Input Features (9 metrics per district)
```python
features:
  - transition_rate_1_to_2     # Grade 7 → Grade 11 retention
  - transition_rate_2_to_3     # Grade 11 → Graduation 
  - transition_rate_3_to_4     # Graduation → University
  - transition_rate_4_to_5     # University → Degree
  - end_to_end_completion_rate # Overall completion rate
  - compounded_transition_rate # Product of all transitions
  - avg_leakage_differential   # Deviation from national avg
  - avg_international_share    # Immigration/diversity factor
  - avg_subject_completion_share # Academic resilience
```

##### Algorithm

1. **Data Preparation:**
   - Fetch feature frame from Gold tables
   - Impute missing values with median strategy
   - Standardize all features (mean=0, std=1) for fair weighting

2. **Optimal K Selection:**
   - Test cluster counts from 2 to 6
   - Use silhouette score to identify best separation
   - Avoid overfitting by capping at 6 clusters

   ```python
   # Pseudo-code
   for k in range(2, 7):
     run KMeans(k)
     score = silhouette_score(features, labels)
     if score > best: best_k = k
   ```

3. **Clustering Execution:**
   - Fit K-Means with selected K
   - Assign each district to cluster 0 through K-1

4. **Post-assignment Labeling:**
   - Compute cluster summaries (mean metrics per cluster)
   - Rank clusters by completion rate + university-to-degree transition
   - Assign human-readable names:
     - Cluster 0: "High Resilience" (districts performing best)
     - Cluster 1: "Stable Transition" (mid-tier performance)
     - Cluster 2: "Recovery Potential" (improvable performance)
     - Cluster 3: "High Leakage Risk" (intervention priority)
     - Cluster 4+: "Data Sparse Segment" / "Emerging Segment"

##### Output Files

| File | Content | Rows | Columns |
|------|---------|------|---------|
| `phase07_cluster_assignments.csv` | Each district + cluster ID + cluster label | ~400 (1 per district) | ags, region, cluster_id, cluster_label, ... |
| `phase07_cluster_summary.csv` | Summary statistics per cluster | K (usually 4-6) | cluster_id, district_count, mean_completion_rate, mean_leakage_differential, cluster_label |

##### Interpretation Example

```csv
# phase07_cluster_summary.csv
cluster_id,district_count,mean_end_to_end_completion_rate,cluster_label
0,45,0.82,High Resilience
1,120,0.65,Stable Transition
2,180,0.48,Recovery Potential
3,55,0.28,High Leakage Risk
```

**Reading:**
- 45 "High Resilience" districts with 82% completion rate
- 180 "Recovery Potential" districts (largest group) with 48% completion
- 55 districts in "High Leakage Risk" are priority for policy

---

#### Part 2: Stage 5 Forecasting (Time Series)

**Purpose:** Predict future degree completions to support multi-year planning

##### Data Source

```sql
SELECT 
  stage_5_year as year,
  sum(stage_5_degree_completions) as value
FROM gold_stage_funnel
WHERE stage_5_year IS NOT NULL
GROUP BY 1
```

Produces annual completion totals (typically 3-10 historical years)

##### Three-Tier Forecast Method

**Tier 1: Prophet (if 4+ historical years available)**
- Facebook's time-series forecasting library
- Handles seasonality, trend, and uncertainty
- Output: Point estimate (yhat) + confidence bands (yhat_lower, yhat_upper)

**Tier 2: Linear Trend (if 2+ years available)**
- Simple polynomial regression (degree 1)
- Slope = historical trend direction
- Residual std = confidence intervals
- Fallback when Prophet unavailable or fails

**Tier 3: Naive Last-Value (if <2 years)**
- Hold completion count flat (assume no growth/decline)
- ±5% confidence band for uncertainty
- Last-resort fallback

##### Forecast Output

```csv
year,yhat,yhat_lower,yhat_upper
2024,45000.0,42750.0,47250.0
2025,46200.0,43890.0,48510.0
2026,47400.0,45030.0,49770.0
2027,48600.0,46170.0,51030.0
2028,49800.0,47310.0,52290.0
```

**Reading:**
- `yhat`: Point forecast for year
- `yhat_lower`: Conservative estimate (95% lower bound)
- `yhat_upper`: Optimistic estimate (95% upper bound)
- Band width indicates forecast uncertainty (narrower = more confident)

##### Forecast Metadata

```json
{
  "method": "prophet",
  "source_metric": "stage_5_degree_completions",
  "train_points": 8,
  "fallback_reason": null
}
```

Tells you:
- Which method was actually used
- How many historical data points were available
- Whether fallback strategy was triggered (non-null fallback_reason)

---

### How ML Output Connects to Dashboard

```
ML Pipeline (src/ml/run_all.py)
    ↓ generates ↓
warehouse/artifacts/phase07_cluster_assignments.csv
warehouse/artifacts/phase07_forecast.csv
warehouse/artifacts/phase07_report.json
    ↓ loaded by ↓
app/main.py → load_evidence_metadata()
    ↓ displays in ↓
Evidence Appendix section
```

**Dashboard consumers of ML:**
- Evidence panel shows cluster count and forecast method used
- Subject resilience chart uses district clusters for filtering
- Phase 07 report presence/status affects defense readiness indicator

---

## How to Use the Dashboard

### Quick Start Workflow

#### For Policymakers (5-minute overview)

1. **Start here:** Dashboard mode, look at KPI metrics
   - "How many districts? What's our completion rate?"
   
2. **Identify problem:** Check funnel chart
   - "Where's the biggest drop?"

3. **Prioritize:** Review anomaly map
   - "Which 5-10 districts need intervention?"

4. **Allocate:** Click largest bubbles, note region names
   - Use tooltip info for budget/resource planning

#### For Researchers (20-minute deep dive)

1. **Context:** Read evidence panel (right side)
   - Verify phase 07/08 reports present and passing

2. **Understand data quality:** Check SCD timeline
   - Toggle historical mode to see if boundary changes affected metrics

3. **Subject analysis:** Examine resilience chart
   - Group by demographic to spot equity gaps
   - Identify subject-specific weaknesses

4. **Segment strategy:** Note cluster assignments from evidence
   - Different policy may apply to "High Resilience" vs "High Leakage Risk" districts

#### For Thesis Defense (Structured walk-through)

1. Switch to **Reviewer Walkthrough mode** (sidebar)
2. Follow 5-step tabs in order
3. Read prompts, show each section to committee
4. Use tooltips for Q&A responses
5. Reference DEFENSE_SCRIPT_AND_QA.md for answers

### Common Questions & How to Find Answers

| Question | Where to Look | How to Interpret |
|----------|---------------|-----------------|
| "Which districts are struggling most?" | Anomaly Map (large orange bubbles) | Size = severity, click for tooltip |
| "Is there a problem in early education or late?" | Funnel chart drop line | Steepest segment shows biggest issue |
| "Are some subjects worse than others?" | Subject Resilience chart | Shorter bars = lower completion |
| "Do demographics matter?" | Subject Resilience colors | Different colors = different groups |
| "Is the data reliable?" | Evidence panel + SCD Timeline | Green checkmarks = quality gates passed |
| "How many different district types are there?" | Evidence panel, "cluster_count" | From Phase 07 ML clustering |
| "What happens next year?" | Evidence panel, "forecast_method" | + forecast artifacts in warehouse/ |

---

## Interpretation Guide

### Key Concepts

#### 1. Leakage vs. Completion

**Leakage** = students who exit the pipeline without achieving final goal
**Completion** = students who successfully progress through all stages

```
If 100 Grade 7 students:
→ 75 reach Grade 11 = 25 leakage
→ 50 graduate = 25 more leakage
→ 30 enter university = 20 more leakage
→ 20 complete degree = 10 final leakage

Overall completion rate = 20/100 = 20%
Total leakage = 80 students
```

#### 2. Anomaly Score as Risk Indicator

**Formula:** `(1 - completion_rate) + |leakage_differential|`

**Components:**
- **(1 - completion_rate)**: Low completion adds risk (inverted%)
- **|leakage_differential|**: Deviation from national average adds risk

**Examples:**
- District with 60% completion, normal leakage: Score ≈ 0.40
- District with 40% completion, high leakage: Score ≈ 0.80 (HIGH RISK)
- District with 80% completion, low leakage: Score ≈ 0.20

#### 3. Reading Confidence Bands in Forecasts

**Forecast confidence:**
- **Narrow band** (yhat ± 2%): High confidence (lots of historical data, stable trend)
- **Wide band** (yhat ± 10%+): Low confidence (sparse data, volatile history)

**Example:**
```
Year 2025:
Narrow band: 45,000 ± 900 → confident trend will continue
Wide band:  45,000 ± 4,500 → could swing either way
```

#### 4. Cluster Labels as Policy Segments

Never treat clusters as fixed tiers. They're fluid analytical groupings:

- **High Resilience**: Model high performers → reverse-engineer best practices
- **Stable Transition**: Mid-tier → support incremental improvements
- **Recovery Potential**: Improvable but resource-intensive → targeted intervention
- **High Leakage Risk**: Crisis/priority → emergency support + deeper investigation
- **Data Sparse**: Few students → combine with neighbor for analysis

#### 5. Subject Resilience Across Demographics

Pay attention to **within-subject gaps**:

```
Math: All Students 85%, First Gen 62% → 23-point gap (systemic barrier)
Math: All Students 85%, Low Income 68% → 17-point gap (resource issue)
→ Suggests tutoring/support targeting first-generation + low-income specifically in math
```

---

### Common Pitfalls & How to Avoid

| Pitfall | Why It Happens | Fix |
|---------|----------------|-----|
| Comparing districts without context | Ignore cluster segments | Always segment by cluster first |
| Misinterpreting SCD boundary changes | Don't check historical mode | Toggle to historical before interpreting timeseries |
| Over-confident in narrow forecasts | Forget uncertainty bands | Always use (lower, upper) range, not point estimate |
| Conflating correlation with causation | Dashboard shows associations not causes | Explicitly note: "observational, not causal" |
| Missing demographic disparities | Only look at average | Disaggregate all charts by demographic group |

---

### Decision-Making Framework

**When you see concerning metric:**

1. **Verify with funnel chart**: Is it a broad systemic issue or isolated stage?
2. **Cross-check with anomaly map**: Is this district alone or part of a pattern?
3. **Review SCD timeline**: Did boundary changes create artificial jump/drop?
4. **Examine subject breakdown**: Is it subject-specific or universal?
5. **Check demographic split**: Does it affect all groups equally?
6. **Consult cluster assignment**: What segment is this district in?
7. **Review quality report**: Are data quality gates passing? (Evidence panel)

Example decision path:
```
Observe: Stage 5 completions dropped 30% year-over-year in District X
  → Check funnel: No spike (so not false artifact)
  → Check anomaly map: District now lit up in red (confirmed)
  → Check SCD timeline (historical): District merged with neighbor district
  → Decision: Likely boundary change effect, not actual decline
  → Next: Rebase comparison period post-merger
```

---

## Troubleshooting

### Common Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Dashboard won't load | "Connection failed / ModuleError" | Run `make install && make ingest && make dbt-run` first |
| Charts show "No data available" warning | Blank section in dashboard | Check that Gold tables have data: `duckdb warehouse/analytics.duckdb "SELECT COUNT(*) FROM gold_stage_funnel"` |
| Map shows dots far from expected geography | Anomaly map shows clusters outside Germany | Expected behavior (CI-safe pseudo-coordinates). Replace "ags_to_lat_lon()" in phase10.py with real GIS data if available |
| KPI metrics empty | Shows 0 for all four KPIs | Verify `gold_stage_funnel` has data rows and non-null count values |
| Reviewer Walkthrough tabs all blank | Tabs visible but no content | Rare rendering bug; refresh page or clear browser cache |
| Forecast shows exactly last value repeated | Forecast all yhat values identical | Likely fallback to naive_last_value method; check forecast method in Evidence panel |
| SCD Historical mode table empty | Historical tab shows no rows | First run (no snapshots created yet); run `make snapshot` to generate |

### Debug Commands

```bash
# Check if DuckDB is accessible
duckdb warehouse/analytics.duckdb "SELECT COUNT(*) FROM gold_stage_funnel"

# Verify Phase 07 & 08 artifacts exist
ls -lh warehouse/artifacts/phase07_*.json warehouse/artifacts/phase08_*.json

# Check Gold table row counts
duckdb warehouse/analytics.duckdb "SELECT COUNT(*) FROM gold_leakage_differential; SELECT COUNT(*) FROM gold_subject_resilience;"

# Run ML pipeline standalone
python -m src.ml.run_all

# Test dashboard data layer
python -c "from src.dashboard.phase10 import load_stage_funnel; print(load_stage_funnel())"

# Full pipeline reset (if needed)
make clean && make install && make ingest && make dbt-run && make ml-run
```

### Getting Help

**Error in charts (Altair):**
- Check `app/main.py` for encoding spec compatibility with Altair v4
- Review latest commit of `src/dashboard/phase10.py`

**Missing data in visuals:**
- Run `make quality-check` to verify data governance passed
- Review `warehouse/artifacts/phase08_quality_report.json`

**Forecast not updating:**
- Check if `stage_5_year` column in gold_stage_funnel is populated
- Verify time series has 2+ historical years: `SELECT DISTINCT stage_5_year FROM gold_stage_funnel`

**Performance issues (dashboard sluggish):**
- Check connection speed to DuckDB
- Reduce data volume: filter by recent years in phase10.py loaders
- Profile with: `streamlit run app/main.py --logger.level=debug`

---

## Appendix: Reference

### File Structure

```
/workspaces/educational-equity-flow/
├── app/
│   └── main.py                    # Dashboard UI (Streamlit)
├── src/
│   ├── dashboard/
│   │   └── phase10.py             # Data loaders for dashboard
│   └── ml/
│       └── run_all.py             # Clustering + forecasting
├── tests/
│   └── test_phase10_dashboard.py  # Unit tests for data layer
├── warehouse/
│   ├── analytics.duckdb           # DuckDB database (Gold + snapshots)
│   └── artifacts/
│       ├── phase07_cluster_assignments.csv
│       ├── phase07_forecast.csv
│       └── phase07_report.json
└── docs/
    └── phase_10/
        ├── DASHBOARD_USER_GUIDE.md      # This file
        ├── DEFENSE_SCRIPT_AND_QA.md     # Thesis defense talking points
        └── THESIS_APPENDIX_EVIDENCE.md  # Reproducibility details
```

### Key Make Targets

| Command | Purpose |
|---------|---------|
| `make app` | Launch dashboard |
| `make ml-run` | Execute clustering + forecasting |
| `make dbt-run` | Build Gold tables |
| `make test` | Unit tests including dashboard tests |
| `make quality-check` | Data governance validation |

### Glossary

| Term | Definition |
|------|-----------|
| **AGS** | Amtlicher Gemeindeschlüssel (official German municipality code) |
| **SCD** | Slowly Changing Dimension (track historical changes to dimensions) |
| **Gold** | Aggregated business fact tables optimized for analytics |
| **Silhouette Score** | Metric for cluster quality (higher = better separation) |
| **Leakage Differential** | How much a district deviates from national completion norm |
| **End-to-End Rate** | % of Grade 7 students who complete degree |
| **Compounded Rate** | Product of all stage-to-stage transition rates |

---

**Last Updated:** Phase 10  
**For Questions:** Refer to DEFENSE_SCRIPT_AND_QA.md or THESIS_APPENDIX_EVIDENCE.md

