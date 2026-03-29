# Improvement and Advancement Roadmap

**Date:** 2026-03-29  
**Current Status:** Phase 10 Complete (Dashboard & Thesis Ready)  
**Scope:** Strategic opportunities across technical, analytical, and operational domains

---

## Executive Summary

The educational-equity-flow system has achieved core functionality through Phase 10: a production-grade data pipeline with dbt modeling, ML clustering/forecasting, and an interactive policy dashboard. This roadmap identifies **18 improvement areas** across four strategic dimensions:

1. **Technical Debt Remediation** (2-3 weeks): Code quality, linting, architecture cleanup
2. **Feature & Capability Enhancement** (3-4 weeks): Richer analytics, improved user experience
3. **Data & Intelligence Advancement** (4-6 weeks): Deeper models, causal analysis, predictive power
4. **Infrastructure & Scalability** (2-4 weeks): Performance, deployment, automation

**High-Impact, Low-Effort Starting Points:**
- Remediate lint debt with auto-fixes
- Integrate official GeoJSON for district mapping
- Add incremental refresh scheduling
- Implement advanced forecasting methods

---

## Part 1: Technical Debt Remediation

### 1.1 Lint Debt Cleanup (`make lint` FAIL → PASS)

**Current State:** 15+ style/import violations across non-Phase-10 modules  
**Impact:** Code quality gate broken; violates engineering best practices  
**Effort:** 2-3 hours (mostly automated fixes)

**Actionable Tasks:**

1. **Auto-fix import sorting** (safe):
   ```bash
   .venv/bin/python -m ruff check --fix src --select I001
   ```
   - Impacts: `src/ingestion/run.py`, `src/quality/run_checks.py`, etc.
   - No logic changes; purely organizational

2. **Line-length violations (manual review):**
   - E501 (line > 100 chars) flagged in:
     - `src/ingestion/run.py` (lines 52, 120)
     - `src/ml/run_all.py` (~5 occurrences)
     - `src/quality/run_checks.py` (~3 occurrences)
   - Options: Refactor long lines OR use `# noqa: E501` if genuinely needed

3. **Enforce post-remediation:**
   - Add `make lint` to CI pull-request checks (currently skipped)
   - Require PASS before merge to master

**Expected Outcome:** `make lint` → PASS (0 errors)  
**Prevention:** CI gate enforcement + pre-commit hook

---

### 1.2 Type Annotation Coverage

**Current State:** Partial type hints in Phase 10 code; legacy modules untyped  
**Gap:** No runtime type checking or IDE autocomplete support  
**Effort:** 1-2 weeks (incremental)

**Actionable Tasks:**

1. **Update legacy modules** (`src/ingestion/`, `src/ml/`, `src/quality/`):
   - Add function signatures with return type hints
   - Annotate DataFrame/Series types using pandas stubs
   - Example:
     ```python
     def run_clustering(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
     ```

2. **Enable Pylance type checking:**
   - Add `[tool.pyright]` section to `pyproject.toml`
   - Set verbosity level and enable strict mode for new code

3. **Optional: Add Pydantic models** for data contracts:
   - Define expected schemas for Bronze, Silver, Gold outputs
   - Validate at pipeline boundaries

**Expected Outcome:** Type hints + IDE support enable faster development  
**Prevention:** Pre-commit type-check hook using mypy/pyright

---

### 1.3 Refactor Phase 07 ML Code for Maintainability

**Current State:** `src/ml/run_all.py` is monolithic (300+ lines)  
**Issue:** Hard to test individual components; unclear separation of concerns  
**Effort:** 3-4 hours

**Proposed Structure:**
```
src/ml/
├── __init__.py
├── clustering/
│   ├── __init__.py
│   ├── feature_engineering.py   # load_feature_frame, imputation
│   ├── kmeans_model.py          # run_clustering, _choose_k, _cluster_labels
│   └── evaluation.py            # silhouette scoring
├── forecasting/
│   ├── __init__.py
│   ├── timeseries.py            # load_stage5_timeseries
│   ├── methods.py               # build_naive_forecast, build_linear_forecast
│   └── prophet_wrapper.py       # Prophet integration + fallback logic
├── artifacts/
│   ├── __init__.py
│   └── save.py                  # Unified artifact export (CSV, JSON, metadata)
└── run_all.py                   # Orchestration (unchanged external behavior)
```

**Benefits:**
- Each module testable independently
- Easier to swap/upgrade individual algorithms (e.g., replace KMeans with HDBSCAN)
- Clearer dependencies and data flow

---

### 1.4 Increase Test Coverage (Currently ~60% estimated)

**Current State:** Basic unit tests for dashboard + ingestion components  
**Gaps:** ML module lacks thorough testing; edge cases not covered  
**Effort:** 1-2 weeks

**Target Coverage:**

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| `src/dashboard/phase10.py` | 90% | 95% | Medium |
| `src/ml/run_all.py` | 30% | 80% | HIGH |
| `src/ingestion/` | 70% | 85% | Medium |
| `src/quality/` | 40% | 75% | Medium |

**Specific Gaps to Address:**
- ML clustering edge cases: k=1 (single cluster), empty features, all-NaN columns
- Forecast fallback logic: Prophet failure → linear → naive chains
- Ingestion schema mismatches: Missing columns, type coercion errors
- Quality check thresholds: Boundary conditions (fail_count=0 vs >0)

**Implementation:**
```bash
pytest --cov=src --cov-report=term-missing
```

---

## Part 2: Feature & Capability Enhancement

### 2.1 Integrate Official GeoJSON for District Mapping

**Current State:** Deterministic AGS-based pseudo-coordinates (CI-safe but geographically inaccurate)  
**Limitation:** Can't interpret actual spatial patterns; no real district boundaries  
**Effort:** 2-3 days

**Solution:**

1. **Acquire GeoJSON:**
   - German administrative boundaries: [GADM](https://gadm.org/), [Geoboundaries](https://www.geoboundaries.org/), or [Bundesamt für Kartographie](https://www.bkg.bund.de/)
   - Filter to district level (AGS-keyed)
   - ~400 districts × 100+ coordinate points ≈ 2-5 MB JSON

2. **Integrate into dashboard** (`src/dashboard/phase10.py`):
   ```python
   def load_geojson_boundaries(geojson_path: Path) -> dict:
       """Load official district geometries."""
       with open(geojson_path) as f:
           return json.load(f)
   
   def plot_choropleth_map(anomaly_df, geojson) -> alt.Chart:
       """Replace bubble map with official choropleth."""
       return alt.Chart(alt.Data(values=geojson['features']))...
   ```

3. **Update dashboard visualization:**
   - Replace `mark_circle()` bubble map with `mark_geoshape()` choropleth
   - Color intensity by anomaly score
   - Hover tooltip with district details

4. **Storage options:**
   - Commit GeoJSON to repo (if <5 MB)
   - OR serve from external source/S3 bucket (if >20 MB)
   - OR generate dynamically from shapefile

**Expected Outcome:** Accurate geographic visualization for policy targeting  
**Non-Impact:** Doesn't change underlying analytics, only visualization

---

### 2.2 Add Incremental Refresh & Scheduling

**Current State:** `make ingest` processes all files every time (full refresh)  
**Limitation:** Slow for large datasets; wasteful; hard to detect new/changed files  
**Effort:** 3-4 hours

**Proposed Enhancement:**

1. **Implement incremental logic** in `src/ingestion/manifest.py`:
   ```python
   def should_process(filename: str, manifest: dict, source_dir: Path) -> bool:
       """Check if file has changed since last successful ingest."""
       current_hash = compute_file_hash(source_dir / filename)
       stored_entry = manifest.get(filename, {})
       return current_hash != stored_entry.get('file_hash')
   ```

2. **Add scheduling support** in `Makefile`:
   ```makefile
   ingest-incremental:
       $(PYTHON) -m src.ingestion.run --incremental --manifest data/bronze/ingestion_manifest.json
   
   schedule-daily-refresh:
       # Cron job or GitHub Actions scheduled workflow
       0 2 * * * cd /path && make ingest-incremental && make dbt-run && make ml-run
   ```

3. **Add to CI workflows** (`.github/workflows/`):
   - Scheduled daily refresh on master
   - Detect new files automatically
   - Fail gracefully if source becomes unavailable

**Expected Outcome:** Faster dev cycles; automated production refresh  
**Prevention:** Manifest validation before merge

---

### 2.3 Enhanced Dashboard Features

**Current State:** 6 main visualizations + 5-step walkthrough  
**Enhancement Opportunities:**

#### A) Drill-Down / Detail Views (HIGH IMPACT)

**Add district detail cards clickable from anomaly map:**
```
Click bubble → Side panel shows:
- District name + AGS
- 5-year completion trend chart
- Subject breakdown (bar chart)
- Risk factors (top 3 drivers of anomaly score)
- Recommended policy levers (from cluster segment)
- Benchmark against similar districts
```

**Effort:** 2-3 days  
**Streamlit method:** `st.sidebar` detail panel + `st.session_state` to track selection

#### B) Demographic Deep Dives (MEDIUM IMPACT)

**Extend Subject Resilience to show:**
- Completion rate curves by demographic (line chart, year-over-year trend)
- Equity gap analysis (biggest disparities highlighted)
- Intersectionality: Subject × Demographics × District

**Effort:** 1-2 days  
**Data requirement:** Extend `gold_subject_resilience` with year/demographic breakdowns

#### C) Forecast Confidence Visualization (MEDIUM IMPACT)

**Make forecast more interactive:**
- Show historical data + fitted trend + confidence band
- Allow user to adjust forecast horizon (3yr, 5yr, 10yr)
- Compare actual vs. forecasted from prior year

**Effort:** 1 day  
**Requires:** Exposure of Prophet/linear model outputs in dashboard

#### D) Export & Report Generation (LOW EFFORT, HIGH VALUE)

**Add export button to dashboard:**
```python
def export_report(district_name: str, artifacts_dir: Path):
    """Generate PDF/markdown report for single district."""
    return {
        'metrics_table': funnel_df[funnel_df['region'] == district_name],
        'charts': [funnel_chart, anomaly_score, subject_chart],
        'narrative': polished_text_insights
    }
```

**Effort:** 2-3 hours  
**Dependency:** `reportlab` or `python-pptx` for PDF/slide generation

---

### 2.4 Implement Data Diff & Change Tracking

**Current State:** No visibility into what changed between runs  
**Gap:** Can't easily debug data quality regressions or source changes  
**Effort:** 1-2 days

**Solution:**

1. **Track row count deltas:**
   ```python
   def compare_bronze_snapshots(run1_manifest, run2_manifest):
       """Show row count changes between two ingestion runs."""
       deltas = {}
       for dataset in run1_manifest:
           rows_before = run1_manifest[dataset]['row_count']
           rows_after = run2_manifest[dataset]['row_count']
           deltas[dataset] = rows_after - rows_before
       return deltas
   ```

2. **Add to CI artifacts:**
   - Save comparison report to `warehouse/artifacts/ingest_delta_<run_date>.json`
   - Display in GitHub Actions job summary

3. **Integration with quality checks:**
   - Flag sudden drops/spikes in row counts
   - Alert if delta exceeds threshold (e.g., ±10%)

---

## Part 3: Data & Intelligence Advancement

### 3.1 Advanced Forecasting Methods

**Current State:** Prophet (primary), Linear trend, Naive fallback  
**Limitations:** No external regressors; assumes smooth trends; limited uncertainty  
**Effort:** 1-2 weeks

**Enhancement Options:**

#### A) ARIMA / SARIMA Models
```python
from statsmodels.tsa.arima.model import ARIMA

def run_arima_forecast(series: pd.DataFrame) -> pd.DataFrame:
    """Seasonal ARIMA for educational data."""
    model = ARIMA(series['value'], order=(1,1,1))
    fitted = model.fit()
    forecast = fitted.get_forecast(steps=5)
    return forecast.conf_int()
```
- **Pros:** Handles seasonality (academic year cycles)
- **Cons:** Requires stationary data, longer training
- **When to use:** If degree completions show strong annual patterns

#### B) XGBoost / Gradient Boosting
```python
from xgboost import XGBRegressor

def run_xgboost_forecast(historical_df: pd.DataFrame, features_df: pd.DataFrame):
    """Use district features to predict completion trends."""
    X = features_df[['transition_rate_1_to_2', 'leakage_differential', ...]]
    y = historical_df['stage_5_degree_completions']
    model = XGBRegressor(n_estimators=100)
    model.fit(X, y)
    return model.predict(X_future)
```
- **Pros:** Captures non-linear relationships; incorporates district features
- **Cons:** Risk of overfitting with limited data
- **When to use:** If district characteristics predict completion trends

#### C) Ensemble Methods
```python
def ensemble_forecast(series, features) -> pd.DataFrame:
    """Combine Prophet + ARIMA + XGBoost."""
    forecast_prophet = run_prophet_forecast(series)
    forecast_arima = run_arima_forecast(series)
    forecast_xgb = run_xgboost_forecast(...features...)
    
    # Weight by historical accuracy
    weights = [0.5, 0.3, 0.2]
    ensemble = (weights[0] * forecast_prophet + 
                weights[1] * forecast_arima + 
                weights[2] * forecast_xgb)
    return ensemble
```
- **Pros:** Robustness; captures different aspects
- **Cons:** Complexity; harder to interpret

**Implementation Priority:**
1. Add ARIMA if academic year seasonality detected
2. Try XGBoost only after adding more features
3. Use ensemble as final production method

---

### 3.2 Causal Inference & Intervention Effects

**Current State:** Observational analytics only (no causal claims)  
**Gap:** Can't answer "what if we implement policy X?"  
**Effort:** 2-3 weeks (requires new data collection)

**Conceptual Path:**

1. **Define counterfactural scenarios:**
   - Scenario A: 10% increase in tutoring resources → effect on completion?
   - Scenario B: Delayed university entry → effect on degree completion?
   - Scenario C: Subject-specific remediation → effect on equitable outcomes?

2. **Implement Causal Inference techniques:**
   - **Propensity Score Matching**: Match treated (high-resource) vs. untreated (low-resource) districts
   - **Difference-in-Differences**: Exploit policy changes across districts over time
   - **Instrumental Variables**: If natural experiment exists (e.g., policy rolled out in cohorts)

3. **Example using DoWhy library:**
   ```python
   from dowhy import CausalModel
   
   # Define causal graph
   gml_graph = """
   digraph {
       treatment [label="Policy Intervention"];
       policy -> completion;
       demographics -> completion;
       demographics -> policy;
   }
   """
   
   model = CausalModel(data, treatment='policy_present', outcome='completion',
                       gml_graph=gml_graph)
   estimate = model.estimate_causal_effect()
   ```

4. **Data requirements:**
   - Panel data (same districts tracked over time)
   - Policy implementation dates/cohorts
   - District characteristics (to control for confounders)

**Current Data Gap:** Would need to expand Gold marts to include temporal policy data

---

### 3.3 Subject-Level Heterogeneity Analysis

**Current State:** Subject completion rates by demographic group  
**Enhancement:** Decompose disparities into policy-actionable factors  
**Effort:** 1-2 weeks

**New Analyses:**

1. **Disparity Decomposition (Oaxaca-Blinder):**
   ```
   Gap = Explained (X differences) + Unexplained (coefficient differences)
   
   Example:
   Math gap: First-Gen 65% vs All Students 85% (20-point gap)
   → Explained: 8 pts (lower resource access)
   → Unexplained: 12 pts (possibly cultural/motivation factors)
   ```

2. **School Fixed Effects:**
   - School quality (teacher qualifications) as driver of equity gaps
   - Separate district-level from school-level effects

3. **Time-to-Event Analysis (Survival Analysis):**
   ```
   "What fraction of students drop out by stage N?"
   "How does this vary by demographics?"
   "What's the hazard ratio for at-risk groups?"
   ```

4. **Subject Interaction Effects:**
   ```
   Does tutoring in Math help Language Arts?
   Are STEM subjects correlated?
   ```

---

### 3.4 Add Price Sensitivity / Policy Lever Modeling

**Current State:** No quantitative model of policy impact  
**Gap:** Can't rank interventions by ROI  
**Effort:** 3-4 weeks (includes hypothesis validation)

**Proposed Framework:**

1. **Identify policy levers:**
   - Tutoring hours (cost/student)
   - Class size reduction (cost/teacher salary)
   - Counseling/mentoring (cost/student)
   - Prior-year remediation (cost/student)

2. **Estimate effect sizes (from literature + data):**
   ```python
   # Prior research or A/B test results
   lever_effects = {
       'tutoring_hours': {'coefficient': 0.02, 'cost_per_student': 500},  # 2% gain per hour
       'class_reduction': {'coefficient': 0.05, 'cost_per_student': 1000},
       'mentoring': {'coefficient': 0.03, 'cost_per_student': 300},
   }
   ```

3. **Build ROI optimization model:**
   ```python
   def optimize_budget_allocation(total_budget: float, levers: dict):
       """Find optimal policy mix to maximize completion rate."""
       from scipy.optimize import minimize
       
       def objective(allocation):
           return -sum(allocation[lever] * levers[lever]['coefficient']) 
       
       constraints = [sum(allocation) <= total_budget]
       result = minimize(objective, x0=[...], constraints=constraints)
       return result.x  # Optimal allocation
   ```

4. **Sensitivity Analysis:**
   - How much does effect size need to change to flip ROI ranking?
   - Which assumptions are most critical?

**Data Requirement:** Historical policy implementations + outcomes to calibrate effects

---

### 3.5 Add Predictive Risk Scoring for Early Intervention

**Current State:** Clustering identifies high-risk districts; no individual student prediction  
**Gap:** Can't target support to students most likely to drop out  
**Effort:** 2-3 weeks (if data available)

**Proposed Model:**

1. **Construct training data:**
   - Input features: Past grades, attendance, demographics, family background
   - Target: Did-not-complete (binary outcome)

2. **Build classification model:**
   ```python
   from sklearn.ensemble import RandomForestClassifier
   
   def build_dropout_risk_model(historical_student_data: pd.DataFrame):
       """Predict which students will drop out."""
       X = historical_student_data[['prior_gpa', 'attendance_rate', 'income_percentile', ...]]
       y = historical_student_data['completed']  # 0/1
       
       model = RandomForestClassifier(n_estimators=100)
       model.fit(X, y)
       
       # Feature importance
       importances = pd.DataFrame({
           'feature': X.columns,
           'importance': model.feature_importances_
       }).sort_values('importance', ascending=False)
       
       return model, importances
   ```

3. **Generate risk scores for current cohort:**
   ```
   For each student entering Stage N:
   - Compute risk_score = P(does not complete from current stage)
   - Flag if risk > 40%
   - Recommend intervention level based on risk tier
   ```

4. **Integration:**
   - Add risk_score column to gold_subject_resilience table
   - Filter dashboard by risk tier
   - Export intervention list for school counselors

**Data Requirement:** Individual student-level data (currently aggregated by district)

---

## Part 4: Infrastructure & Scalability

### 4.1 Containerization & Docker Deployment

**Current State:** Local development only; no container image  
**Limitation:** Deployment varies across environments; hard to scale  
**Effort:** 2-3 hours

**Solution:**

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY pyproject.toml requirements-dev.txt ./
   RUN pip install --no-cache-dir -e ".[dev]"
   
   COPY . .
   
   # For dashboard
   EXPOSE 8501
   CMD ["streamlit", "run", "app/main.py", "--server.port=8501"]
   ```

2. **Create docker-compose.yml:**
   ```yaml
   version: '3.8'
   services:
     dashboard:
       build: .
       ports:
         - "8501:8501"
       volumes:
         - ./warehouse:/app/warehouse
         - ./data:/app/data
     duckdb:  # Optional: separate service for persistent DB
       image: duckdb/duckdb
       volumes:
         - warehouse_data:/data
   volumes:
     warehouse_data:
   ```

3. **Build and push to registry:**
   ```bash
   docker build -t theo-lyd/educational-equity-flow:v1.0 .
   docker push theo-lyd/educational-equity-flow:v1.0
   ```

4. **Update CI workflows:**
   - Push image to Docker Hub on master branch
   - Use image in scheduled workflows (no need to reinstall deps)

**Benefits:**
- Consistent environments (local = staging = production)
- Faster CI/CD (pre-built image)
- Scalable to Kubernetes/cloud

---

### 4.2 Database Optimization & Query Performance

**Current State:** Single-threaded DuckDB; queries work but not optimized  
**Limitation:** Large datasets or concurrent queries may be slow  
**Effort:** 2-3 days

**Optimization Tasks:**

1. **Add indexes to Gold tables:**
   ```sql
   CREATE INDEX idx_gold_transition_rates_ags ON gold_transition_rates(ags);
   CREATE INDEX idx_gold_leakage_differential_ags ON gold_leakage_differential(ags);
   CREATE INDEX idx_gold_subject_resilience_subject ON gold_subject_resilience(hs_fg2_group);
   ```

2. **Aggregate at ingest time (materialized views):**
   - Pre-compute district-level summaries
   - Pre-compute demographic aggregates
   - Reduces dashboard query time significantly

3. **Query optimization in phase10.py:**
   ```python
   # Before: Full table scan + filtering in Python
   district_data = con.execute("SELECT * FROM gold_large_table").fetchdf()
   filtered = district_data[district_data['ags'] == ags]
   
   # After: Filter at database level
   filtered = con.execute(f"SELECT * FROM gold_large_table WHERE ags = '{ags}'").fetchdf()
   ```

4. **Profile queries:**
   ```bash
   EXPLAIN <query> -- Shows execution plan
   EXPLAIN ANALYZE <query> -- Shows actual timing
   ```

5. **Monitor connection pooling:**
   - Currently 1 connection per query
   - Can batch multiple queries into single connection

---

### 4.3 GitHub Actions Workflow Enhancements

**Current State:** Three workflows (PR, master, scheduled)  
**Enhancement Opportunities:**

#### A) Parallel Job Execution (EASY)
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
  lint:
    runs-on: ubuntu-latest
  profile:
    runs-on: ubuntu-latest
  # Run in parallel instead of sequentially
```

#### B) Artifact Retention & Reporting (MEDIUM)
```yaml
- name: Upload quality report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: quality-reports
    path: warehouse/artifacts/phase08_quality_report.json
    
- name: Report to PR
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v6
  with:
    script: |
      // Post summary table to PR comment
      github.rest.issues.createComment({...})
```

#### C) Cost Attribution & Optimization (ADVANCED)
```yaml
- name: Report job duration
  run: |
    echo "Job took $(date -d @$(($(date +%s) - ${{ job.start_time }})) +%M:%S)" >> $GITHUB_STEP_SUMMARY
```

**Effort:** 1-2 days  
**ROI:** Faster feedback loop, easier debugging, cost visibility

---

### 4.4 Add Observability & Monitoring

**Current State:** No structured logging or metrics collection  
**Gap:** Hard to debug failures in production  
**Effort:** 1-2 weeks

**Solutions:**

1. **Structured Logging:**
   ```python
   import logging
   import json
   
   logger = logging.getLogger(__name__)
   
   # Instead of print()
   logger.info("Ingest started", extra={
       'source_file': 'data/raw/21111.csv',
       'rows_expected': 50000,
       'timestamp': datetime.now().isoformat()
   })
   ```

2. **Metrics Collection:**
   - Row counts at each stage (ingestion, modeling, export)
   - Query latencies (Gold table access times)
   - Forecast accuracy (compare prediction vs actual)
   - Data quality score (% passing checks)

3. **Logging Infrastructure (for production):**
   - Datadog / New Relic: Cloud logging + alerting
   - OR ELK Stack: Elasticsearch + Logstash + Kibana
   - OR CloudWatch: AWS-native solution

4. **Example metric export:**
   ```python
   def export_metrics(run_metadata: dict):
       """Save structured metrics for monitoring."""
       metrics = {
           'phase': 'ingest',
           'duration_seconds': 45.2,
           'rows_processed': 214977,
           'errors': 0,
           'timestamp': datetime.utcnow().isoformat()
       }
       with open('warehouse/artifacts/metrics.jsonl', 'a') as f:
           f.write(json.dumps(metrics) + '\n')
   ```

---

### 4.5 Implement Data Archival & Retention Policy

**Current State:** All data kept indefinitely  
**Gap:** Disk space grows unbounded; GDPR concerns  
**Effort:** 2-3 hours

**Policy:**

1. **Retention Tiers:**
   ```
   - Current year Gold tables: Keep live in DuckDB
   - Prior 2 years: Archive to Parquet (read-only)
   - Older than 3 years: Compress to gzip + store in object storage
   - PII/sensitive: Redact after 5 years (compliance)
   ```

2. **Implementation:**
   ```python
   def archive_old_partitions(days_old: int = 365*2):
       """Move old Bronze partitions to archive storage."""
       import shutil
       for partition_dir in Path('data/bronze').glob('*'):
           if (datetime.now() - datetime.fromtimestamp(partition_dir.stat().st_mtime)).days > days_old:
               shutil.move(str(partition_dir), f'archive/{partition_dir.name}')
   ```

3. **Add to CI:**
   - Run monthly archival job
   - Report freed space

---

## Part 5: Operational Excellence

### 5.1 Documentation Automation

**Current State:** Manual markdown docs in `docs/phases/`  
**Enhancement:** Auto-generate architecture diagrams, data dictionaries, lineage  
**Effort:** 2-3 days

**Tools & Techniques:**

1. **Data Dictionary Generation:**
   ```python
   def generate_data_dictionary(gold_table: str, con: duckdb.Connection):
       """Export schema as markdown table."""
       schema = con.execute(f"DESCRIBE {gold_table}").fetchdf()
       return schema.to_markdown()
   ```

2. **SQL Lineage Extraction:**
   Use `sqlparse` + `pygraphviz` to auto-generate data lineage diagrams

3. **Test Report Generation:**
   ```bash
   dbt test --fail-fast --output-json | python -c "parse_json_to_markdown"
   ```

4. **Dashboard Docs from Docstrings:**
   ```python
   def render_funnel(sankey_df: pd.DataFrame) -> None:
       """
       **Leakage Funnel Visualization**
       
       Shows student flow through 5 educational stages with drop-off trend.
       - X-axis: Stages (Grade 7 → Completion)
       - Y-axis: Student count
       - Color: Target stage
       
       **Interpretation:** Steeper drop line = higher attrition risk
       """
   ```

5. **Implementation:**
   Add to CI: Extract docstrings → generate markdown → commit to `docs/auto-generated/`

---

### 5.2 Create Runbooks & Troubleshooting Guides

**Current State:** EXECUTION_GUIDE.md exists; limited operational docs  
**Gap:** Team members need step-by-step guidance for common tasks  
**Effort:** 1 week to document; 30 min to add each new runbook

**Runbooks to Create:**

1. **Debugging Failed Ingestion:**
   - Check manifest for error logs
   - Validate source file schema
   - Compare row counts to prior run

2. **Investigating Data Quality Failures:**
   - Query phase08_quality_report.json
   - Drill down to failing check
   - Verify source data manually

3. **Reprocessing Specific Date Range:**
   - Delete manifest entry for date
   - Clear corresponding Bronze partition
   - Re-run ingest

4. **Emergency Rollback:**
   - Restore prior Git commit if code issue
   - Restore database backup if data issue

5. **Performance Investigation:**
   - Profile slow queries: `EXPLAIN ANALYZE`
   - Check for missing indexes
   - Validate dbt resource graph

---

### 5.3 Add Formal Change Log & Release Notes

**Current State:** Commits show changes; no structured release cadence  
**Gap:** Users don't know what's new; no SemVer versioning  
**Effort:** 2-3 hours (one-time setup) + 15 min per release

**Solution:**

1. **Adopt Semantic Versioning:**
   - v0.1.0 → v0.2.0 (feature) → v0.2.1 (bugfix) → v1.0.0 (major)

2. **Maintain CHANGELOG.md:**
   ```markdown
   # Changelog
   
   ## [0.2.0] - 2026-04-15
   
   ### Added
   - GeoJSON district mapping
   - Incremental refresh scheduling
   
   ### Fixed
   - Lint violations in ingestion module
   - Dashboard Altair v4 compatibility
   
   ### Changed
   - Phase 07 ML refactored to submodules
   ```

3. **Tag releases in Git:**
   ```bash
   git tag -a v0.2.0 -m "Add GeoJSON mapping and incremental refresh"
   git push origin v0.2.0
   ```

4. **Auto-generate from Git:**
   Use `git-cliff` tool to auto-generate changelog from conventional commits

---

### 5.4 Performance Benchmarking & SLA Definitions

**Current State:** No defined performance targets  
**Gap:** Can't measure system health objectively  
**Effort:** 3-4 hours

**SLA Framework:**

| Operation | Current (Observed) | Target SLA | Alert Threshold |
|-----------|-------------------|-----------|-----------------|
| `make ingest` (full) | 2-3 min | < 2 min | > 4 min |
| `make dbt-run` (7 models) | 0.94 sec | < 1 sec | > 2 sec |
| Dashboard page load | ~2 sec | < 1.5 sec | > 3 sec |
| `make ml-run` | ~5 sec | < 10 sec | > 20 sec |
| Monthly forecast prediction | (daily cronjob) | Complete by 03:00 UTC | N/A |

**Implementation:**

1. **Add benchmarks to CI:**
   ```python
   import time
   start = time.time()
   result = func()
   duration = time.time() - start
   
   assert duration < SLA_TARGET, f"Slow: {duration}s > {SLA_TARGET}s"
   ```

2. **Track over time:**
   Save benchmark results to `warehouse/artifacts/benchmarks.csv`
   Plot trend to detect regressions

3. **GitHub Actions reporting:**
   - Fail if SLA exceeded
   - Post benchmark timings to PR comment

---

## Summary: Prioritization Matrix

| Area | Impact | Effort | Timing | Why |
|------|--------|--------|--------|-----|
| **Lint Debt** | Medium | 2h | Week 1 | Quick win; unblocks CI gates |
| **GeoJSON Mapping** | High | 0.5d | Week 1-2 | Vastly improves visualization; straightforward |
| **Test Coverage (ML)** | High | 1w | Week 2-3 | Reduces debugging time; prevents regressions |
| **Advanced Forecasting** | Medium | 1-2w | Month 2 | Better planning; ARIMA lowest-hanging |
| **Dashboard Drill-Down** | High | 2-3d | Week 3-4 | Huge UX improvement; increases adoption |
| **Containerization** | High | 3h | Month 2 | Enables production deployment; CI benefit |
| **Data Archival** | Low | 3h | Month 3 | Compliance + cost; not blocking |
| **Causal Inference** | High | 2-3w | Month 3-4 | Transforms to impact analysis; requires data |
| **Risk Scoring** | High | 2-3w | Month 3-4 | Enables early intervention; data-dependent |
| **Observability** | Medium | 1-2w | Month 2 | Better ops; medium ROI |

---

## Phase 11: Recommended Sequence

**Week 1-2: Foundation Hardening**
- [ ] Remediate lint debt (2-3h)
- [ ] Increase ML test coverage (3-4d)
- [ ] Integrate GeoJSON (1d)

**Week 3-4: UX & Analytics**
- [ ] Add dashboard drill-down detail views (2-3d)
- [ ] Add incremental refresh scheduling (1d)
- [ ] Implement advanced forecasting (ARIMA) (3-4d)

**Month 2: Infrastructure & Operations**
- [ ] Containerization + Docker Compose (3h)
- [ ] Add observability (logging + metrics) (4-5d)
- [ ] Performance benchmarking SLAs (4h)
- [ ] Create runbooks (3-4d)

**Month 3-4: Intelligence Advancement (Data Permitting)**
- [ ] Causal inference + policy leverage modeling (2-3w)
- [ ] Predictive risk scoring (2-3w)
- [ ] Subject heterogeneity decomposition (1-2w)

---

## Appendix: Quick Reference

### Dependencies to Add (if implementing features)

```bash
# Advanced forecasting
pip install statsmodels  # ARIMA
pip install shap  # Model explainability

# Causal inference
pip install dowhy  # Causal models
pip install econml  # Heterogeneous effects

# Geospatial
pip install geopandas  # Shapefile/GeoJSON
pip install shapely  # Geometry operations

# Operations
pip install structlog  # Structured logging
pip install git-cliff  # Auto-changelog generation

# Containerization
# Docker (install binary separately)
```

### Resources & References

- **Forecasting**: Hyndman & Athanasopoulos, "Forecasting: Principles and Practice"
- **ML for Policy**: Mullainathan & Spiess, "Machine Learning: An Applied Econometric Approach"
- **Causal Inference**: Pearl, "The Book of Why"
- **Analytics Engineering**: "dbt Best Practices"
- **Dashboards**: "Storytelling with Data" (Cole Nussbaumer Knaflic)

---

**Last Updated:** Phase 10 Completion (2026-03-29)  
**Next Review:** After Phase 11 Sprint Planning

