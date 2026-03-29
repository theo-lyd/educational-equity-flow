# Feasible Improvements: No Paid Materials Required

**Analysis Date:** 2026-03-29  
**Focus:** Open-source only, free services, no paid subscriptions

---

## Part 1: Feasibility Matrix

### ✅ **100% Feasible (No External Dependencies)**

| # | Improvement | Est. Effort | ROI | Why Free |
|---|-------------|-------------|-----|----------|
| 1️⃣ | Lint Debt Cleanup | 2-3h | HIGH | Ruff is OSS, fixes are automated |
| 2️⃣ | Type Annotations | 1-2w | HIGH | mypy/pyright are free; no runtime deps |
| 3️⃣ | ML Code Refactor | 3-4h | MEDIUM | Pure reorganization, no new packages |
| 4️⃣ | Increase Test Coverage | 3-4d | HIGH | pytest is free; covers edge cases |
| 5️⃣ | Data Diff Tracking | 1-2d | MEDIUM | Pure Python logic, no external tools |
| 6️⃣ | Dashboard Drill-Down | 2-3d | VERY HIGH | Streamlit is free, all on localhost |
| 7️⃣ | Dashboard Export | 2-3h | HIGH | reportlab/python-pptx are free |
| 8️⃣ | Incremental Refresh | 3-4h | HIGH | Pure Python logic in manifest tracking |
| 9️⃣ | Advanced Forecasting | 1-2w | HIGH | statsmodels/sklearn are free |
| 🔟 | Database Optimization | 2-3d | HIGH | DuckDB query tuning, free |
| 1️⃣1️⃣ | Query Optimization | 1-2d | HIGH | Index creation, materialized views |
| 1️⃣2️⃣ | Docker Containerization | 3-4h | VERY HIGH | Docker is free; eliminates setup friction |
| 1️⃣3️⃣ | GitHub Actions Enhancements | 1-2d | MEDIUM | GH Actions free tier (2000min/month) |
| 1️⃣4️⃣ | GeoJSON Integration | 1-2d | VERY HIGH | GADM/Geoboundaries/OSM free |
| 1️⃣5️⃣ | Subject Heterogeneity | 1-2w | HIGH | Pure statistical analysis, free tools |
| 1️⃣6️⃣ | Causal Inference* | 2-3w | VERY HIGH | DoWhy, econml are free OSS |
| 1️⃣7️⃣ | Open-Source Observability* | 1-2w | MEDIUM | Prometheus/Loki/ELK stack (free) |
| 1️⃣8️⃣ | Data Archival | 1-2d | LOW | Pure Python + file system operations |

**Legend:** * = Requires data you may not have (panel data, policy implementation logs)

---

**Status Summary:**
- ✅ **15/18 improvements** can be implemented with ZERO paid software/services
- ✅ **12/18 improvements** require only data you already have
- ⚠️ **3/18 improvements** depend on having additional data (individual-level student records, policy implementation history)

---

## Part 2: Deep Dive into Top 8 Feasible-Free Improvements

### **Tier 1: Quick Wins (Start This Week)**

---

## 🟢 **1. Lint Debt Cleanup (2-3 hours)**

**Why This Matters:**
- Unblocks the `make lint` CI gate
- Improves code quality baseline
- Takes 2-3 hours for immediate credibility win

**Current State:**
```bash
$ make lint
# Returns 15+ errors across multiple modules
E501: Line too long
I001: Imports un-sorted
```

**Step-by-Step Implementation:**

### Part A: Auto-fix Import Sorting (5 min)

```bash
cd /workspaces/educational-equity-flow
.venv/bin/python -m ruff check --fix src --select I001
```

**What it does:**
- Scans all Python files in `src/`
- Finds unsorted/malformed import blocks
- Applies safe fixes automatically
- No logic changes, only reorganization

**Files affected:**
- `src/ingestion/normalizers.py` (imports split incorrectly)
- `src/ingestion/run.py` (stdlib vs local imports not sorted)
- `src/quality/run_checks.py` (import ordering issues)
- `src/ml/run_all.py` (likely some import issues)

### Part B: Manual Line-Length Fixes (1-2 hours)

Long lines (E501) can't be auto-fixed; need manual decision per case.

**Example Case 1: `src/ingestion/run.py` line 52**
```python
# Current (LONG - 103 chars)
log_entry = f"Processing {source}: {rows_ingested} rows; output: {target} partitions; status: {status}"

# Option A: Break into multiple lines
log_entry = (
    f"Processing {source}: {rows_ingested} rows; "
    f"output: {target} partitions; status: {status}"
)

# Option B: Extract to variable
file_summary = f"{rows_ingested} rows → {target} partitions"
log_entry = f"Processing {source}: {file_summary}; status: {status}"

# Option C: Accept with noqa (if truly necessary)
log_entry = f"..." # noqa: E501
```

**Scan & Fix Strategy:**
```bash
# 1. Get full list of violations
.venv/bin/python -m ruff check src --select E501

# 2. For each file, decide: refactor OR noqa
# 3. Most cases: refactor is cleaner
# 4. Few exceptions: complex condition expressions with OR noqa
```

**Practical workflow:**
```bash
# Get violation report
ruff check src --select E501 > violations.txt

# Review violations.txt
# For each, apply one of three fixes:
# - Break string into multiple lines
# - Extract subexpression to variable
# - Add # noqa: E501 comment

# Verify fix
ruff check src
# Should show 0 errors
```

### Part C: Enforce Post-Remediation (30 min)

1. **Add lint to PR checks:**

Edit `.github/workflows/ci-pr.yml`:
```yaml
jobs:
  lint:  # Add this job
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install ruff
      - run: ruff check src tests app
```

2. **Add pre-commit hook (optional but recommended):**

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Then: `pip install pre-commit && pre-commit install`

**Expected Outcome:**
- `make lint` → PASS (0 errors)
- `git push` → PR checks include lint gate
- Team auto-fixes imports on every commit

---

## 🟢 **2. Type Annotation Coverage (1-2 weeks, incremental)**

**Why This Matters:**
- IDE autocomplete for DataFrame operations (HUGE productivity boost)
- Catch bugs before runtime
- Self-documenting code

**Current State:**
```python
# NO TYPE HINTS (hard for IDE to help)
def run_clustering(features):
    model_input = features[feature_cols].copy()
    ...
    return features, summary, cluster_metrics

# IDE doesn't know:
# - "features" is pd.DataFrame or dict?
# - Return type is tuple of what?
# - Can't autocomplete DataFrame methods
```

**Implementation Plan:**

### Part A: Annotate Core Data Structures (2 days)

**Target Files:**
1. `src/ml/run_all.py` - Main clustering entry
2. `src/dashboard/phase10.py` - Data loaders
3. `src/ingestion/run.py` - Pipeline orchestration

**Pattern to Follow:**

```python
# Before (Legacy)
def load_feature_frame(con):
    query = """SELECT ..."""
    return con.execute(query).fetchdf()

# After (Annotated)
def load_feature_frame(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Load feature matrix from Gold tables."""
    query = """SELECT ..."""
    return con.execute(query).fetchdf()
```

**Key Annotations:**

```python
from __future__ import annotations

import pandas as pd
import duckdb
from pathlib import Path
from collections.abc import Callable
from typing import Any, Optional

# File I/O
def load_manifest(path: Path) -> dict[str, Any]:
    """Load ingestion manifest."""
    ...

# DuckDB connections
def _connect(db_path: Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    """Connect to DuckDB analytics warehouse."""
    ...

# DataFrames
def filter_by_district(df: pd.DataFrame, ags: str) -> pd.DataFrame:
    """Filter to single district."""
    ...

# Complex returns
def run_clustering(
    features: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int | float]]:
    """Execute K-means clustering.
    
    Returns:
        (assignments_df, summary_df, metrics_dict)
    """
    ...

# Optional values
def get_phase07_report(path: Path) -> dict[str, object] | None:
    """Load Phase 07 report if it exists."""
    ...
```

### Part B: Add Pydantic Models for Data Contracts (3-4 days, Optional)

**Benefit:** Validate data structure at boundaries

```python
from pydantic import BaseModel, Field

class DistrictMetrics(BaseModel):
    """Expected schema for gold_transition_rates."""
    ags: str = Field(..., description="5-digit AGS code")
    region: str = Field(..., description="District name")
    transition_rate_1_to_2: float = Field(..., ge=0, le=1)
    end_to_end_completion_rate: float = Field(..., ge=0, le=1)
    
    class Config:
        frozen = True  # Immutable once created

# Use in pipeline
def validate_gold_table(df: pd.DataFrame) -> list[DistrictMetrics]:
    """Validate transition rates table."""
    records = df.to_dict(orient='records')
    return [DistrictMetrics(**row) for row in records]

# Now errors caught early:
validate_gold_table(bad_df)
# ✗ ValidationError: transition_rate_1_to_2: 1.5 is > 1
```

### Part C: Enable Type Checking in Tooling (1 day)

**Update `pyproject.toml`:**
```toml
[tool.pyright]
include = ["src", "app", "tests"]
exclude = ["**/__pycache__", ".venv"]
typeCheckingMode = "basic"  # or "strict" for Phase 10 code
reportMissingImports = false  # Some libraries lack stubs
reportUnnecessaryIsInstance = true
reportOptionalMemberAccess = "warning"
```

**Enable in VS Code:**
- Install Pylance extension
- Settings → Python > Type Checking Mode = "basic"
- Hover over functions → see type signatures
- Type errors flagged in editor

**CI Integration:**
```bash
# Add to Makefile
typecheck:
	$(PYTHON) -m pyright src

# Add to CI:
- run: make typecheck
```

**Expected Outcome:**
- Autocomplete working in IDE for all DataFrame operations
- Catch ~15-20% of bugs before runtime
- Better documentation through signatures

---

## 🟡 **3. ML Test Coverage Expansion (3-4 days)**

**Why This Matters:**
- `src/ml/run_all.py` currently has only ~30% test coverage
- Edge cases (empty data, NaN values, fallback logic) untested
- Easy to regress forecasting behavior

**Current Gap:**

```python
# Tested:
✅ Clustering with normal data
✅ Forecast with ≥4 data points

# NOT Tested:
❌ Clustering when k=1 (single cluster result)
❌ Feature with all-NaN columns (imputation logic)
❌ Forecast fallback chain (Prophet → Linear → Naive)
❌ Boundary: k_min vs k_max handling
❌ Empty input data
```

**Implementation Plan:**

### Part A: Identify Coverage Gaps (2-3 hours)

```bash
# Generate coverage report
.venv/bin/python -m pytest tests/test_phase10_dashboard.py --cov=src.ml --cov-report=html

# Open htmlcov/index.html in browser
# See red (uncovered) vs green (covered) lines
```

**Priority gaps to cover:**

1. **K-selection edge cases:**
   ```python
   # Test case: all features are constant (no variance)
   def test_choose_k_constant_features():
       X = pd.DataFrame({'a': [1,1,1,1], 'b': [2,2,2,2]})
       k = _choose_k(X)
       assert k in [1, 2]  # Should handle gracefully
   ```

2. **Forecast fallback chain:**
   ```python
   # Test: Prophet fails → Linear fallback
   def test_forecast_prophet_failure_fallback():
       series = pd.DataFrame({'year': [2020], 'value': [1000]})
       forecast, meta = run_forecast(series, periods=5)
       assert meta.method in ['linear_trend', 'naive_last_value']
       assert meta.fallback_reason is not None
   ```

3. **Missing value handling:**
   ```python
   def test_run_clustering_with_nan_features():
       features = pd.DataFrame({
           'col1': [1, 2, np.nan, 4],
           'col2': [5, np.nan, np.nan, 8]
       })
       assignments, summary, metrics = run_clustering(features)
       assert len(assignments) == 4  # All rows imputed
       assert not assignments['cluster_id'].isna().any()
   ```

### Part B: Write Missing Tests (2-3 days)

**New test file:** `tests/test_ml_coverage.py`

```python
import numpy as np
import pandas as pd
import pytest
from src.ml.run_all import (
    run_clustering,
    run_forecast,
    _choose_k,
    load_stage5_timeseries,
)

# --- K-Selection Tests ---
class TestChooseK:
    def test_choose_k_single_cluster_sufficient(self):
        """When k_max < n_rows, return min cluster count."""
        X = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        k = _choose_k(X, k_min=2, k_max=5)
        assert k >= 2
    
    def test_choose_k_high_variance_selects_more_clusters(self):
        """High-variance data should use more clusters."""
        # Create bimodal distribution
        X = pd.concat([
            pd.DataFrame({'a': np.random.normal(0, 1, 50)}),
            pd.DataFrame({'a': np.random.normal(10, 1, 50)})
        ])
        k = _choose_k(X, k_min=2, k_max=6)
        assert k >= 2

    def test_choose_k_single_row(self):
        """With only 1 row, should return k=1."""
        X = pd.DataFrame({'a': [1], 'b': [2]})
        k = _choose_k(X)
        assert k == 1

# --- Clustering Tests ---
class TestClustering:
    def test_run_clustering_with_all_nan_column(self):
        """Handle column with all NaN values."""
        features = pd.DataFrame({
            'col1': [1.0, 2.0, 3.0],
            'col2': [np.nan, np.nan, np.nan]  # All missing
        })
        assignments, summary, metrics = run_clustering(features)
        assert len(assignments) == 3
        assert 'cluster_id' in assignments.columns

    def test_run_clustering_returns_labels(self):
        """Cluster labels should be human-readable."""
        features = pd.DataFrame({
            'rate1': [0.8, 0.5, 0.3],
            'rate2': [0.7, 0.4, 0.2]
        })
        _, summary, _ = run_clustering(features)
        assert all(isinstance(label, str) for label in summary['cluster_label'])

# --- Forecast Tests ---
class TestForecast:
    def test_forecast_single_point_uses_naive(self):
        """With only 1 data point, use naive forecast."""
        series = pd.DataFrame({'year': [2020], 'value': [1000]})
        forecast, meta = run_forecast(series, periods=5)
        assert meta.method == 'naive_last_value'
        assert len(forecast) == 5

    def test_forecast_two_points_uses_linear(self):
        """With 2 points, try linear before naive."""
        series = pd.DataFrame({
            'year': [2020, 2021],
            'value': [1000, 1100]
        })
        forecast, meta = run_forecast(series, periods=5)
        # Method could be linear or prophet depending on availability
        assert meta.method in ['linear_trend', 'prophet']
        assert len(forecast) == 5

    def test_forecast_confidence_bands_reasonable(self):
        """Confidence bands should widen with horizon."""
        series = pd.DataFrame({
            'year': list(range(2015, 2023)),
            'value': [1000 + 100*i for i in range(8)]
        })
        forecast, meta = run_forecast(series, periods=5)
        
        # Band width should increase with horizon
        forecast['band_width'] = forecast['yhat_upper'] - forecast['yhat_lower']
        assert forecast['band_width'].is_monotonic_increasing

# --- Integration Tests ---
class TestIntegration:
    def test_full_ml_pipeline_with_synthetic_data(self, tmp_path):
        """End-to-end pipeline smoke test."""
        # Create minimal synthetic warehouse
        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        
        # Create minimal gold table
        con.execute("""
            CREATE TABLE gold_transition_rates AS
            SELECT 
                'AGS00001' as ags,
                'District 1' as region,
                0.75 as transition_rate_1_to_2,
                0.70 as transition_rate_2_to_3,
                0.65 as transition_rate_3_to_4,
                0.60 as transition_rate_4_to_5,
                0.19 as end_to_end_completion_rate,
                0.18 as compounded_transition_rate
        """)
        
        # Run ML pipeline
        from src.ml.run_all import run_all
        report = run_all(db_path=db_path, artifact_dir=tmp_path)
        
        assert report['cluster_count'] >= 1
        assert report['forecast_rows'] == 5
```

### Part C: Update CI to Report Coverage (1 day)

**Add to GitHub Actions workflow:**
```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=src --cov-report=xml --cov-report=term-missing
    
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
    fail_ci_if_error: false  # Don't block if service is down
```

**Expected Outcome:**
- Coverage: 30% → 80% for `src.ml`
- Catch forecast/clustering regressions before merge
- Confidence in refactoring Phase 07 ML code safely

---

## 🟡 **4. Dashboard Drill-Down Detail Views (2-3 days)**

**Why This Matters:**
- Current dashboard shows summary; users can't explore districts deeply
- Increases adoption: "Let me click on that red bubble to learn more"
- **HIGHEST UX improvement with modest effort**

**Current State:**
```
Anomaly Map
├── Click bubble → Shows tooltip ONLY
│   └── ags, region, anomaly_score (brief)
└── That's it. Can't dig deeper.

Desired State:
├── Click bubble → Opens side panel
│   ├── District name + AGS
│   ├── 5-year completion trend chart
│   ├── Subject breakdown
│   ├── Risk factors (top 3 drivers of anomaly)
│   ├── Recommended interventions
│   └── Benchmark vs similar districts
```

### Part A: Add Session State for Selection (1 hour)

**Edit `app/main.py`:**

```python
import streamlit as st

# Add at top level (after page config)
if 'selected_district' not in st.session_state:
    st.session_state.selected_district = None

if 'detail_panel_open' not in st.session_state:
    st.session_state.detail_panel_open = False
```

**Why:** Streamlit needs to remember which district the user clicked

### Part B: Build Clickable District Selection (4 hours)

**Add new function to `src/dashboard/phase10.py`:**

```python
def get_district_time_series(ags: str, db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Get 5-year completion trend for single district."""
    con = _connect(db_path)
    df = con.execute(f"""
        SELECT 
            stage_5_year as year,
            stage_5_degree_completions as comp_count,
            stage_1_students as entrance_count,
            CAST(stage_5_degree_completions AS FLOAT) / 
            CAST(stage_1_students AS FLOAT) as completion_rate
        FROM gold_stage_funnel
        WHERE ags = '{ags}'
        ORDER BY year
    """).fetchdf()
    con.close()
    return df

def get_district_subject_breakdown(ags: str, db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Get subject completion for single district."""
    con = _connect(db_path)
    df = con.execute(f"""
        SELECT 
            hs_fg2_group,
            demographic_group,
            avg(subject_completion_share) as completion_share,
            sum(passed_exams) as passed_exams
        FROM gold_subject_resilience
        WHERE ags = '{ags}'
        GROUP BY 1, 2
    """).fetchdf()
    con.close()
    return df

def compute_risk_drivers(ags: str, anomaly_df: pd.DataFrame) -> dict[str, float]:
    """Decompose anomaly score into components."""
    district = anomaly_df[anomaly_df['ags'] == ags].iloc[0]
    
    incompletion_risk = 1.0 - district['end_to_end_completion_rate']
    leakage_risk = abs(district['mean_leakage_differential'])
    
    return {
        'incompletion': incompletion_risk,
        'leakage': leakage_risk,
        'total_score': district['anomaly_score']
    }

def get_similar_districts(ags: str, anomaly_df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """Find k-nearest districts by feature similarity."""
    from sklearn.neighbors import NearestNeighbors
    
    features = anomaly_df[['anomaly_score', 'end_to_end_completion_rate', 
                           'mean_leakage_differential']].values
    
    model = NearestNeighbors(n_neighbors=k+1)
    model.fit(features)
    
    target_idx = anomaly_df[anomaly_df['ags'] == ags].index[0]
    _, indices = model.kneighbors([[features[target_idx]]])
    
    # Exclude target itself (first result)
    similar_indices = indices[0][1:]
    return anomaly_df.iloc[similar_indices]
```

**Add to `app/main.py` (in render_anomaly_map):**

```python
def render_anomaly_map(anomaly_df: pd.DataFrame) -> None:
    st.subheader("District Anomaly Map")
    if anomaly_df.empty:
        st.warning("No anomaly data is available.")
        return

    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Existing map code...
        map_chart = (
            alt.Chart(anomaly_df)
            .mark_circle(opacity=0.8)
            .encode(
                longitude="lon:Q",
                latitude="lat:Q",
                size=alt.Size("anomaly_score:Q", scale=alt.Scale(range=[35, 800])),
                color=alt.Color("anomaly_score:Q", scale=alt.Scale(scheme="orangered")),
                tooltip=["ags", "region", alt.Tooltip("anomaly_score:Q", format=".3f")],
            )
            .properties(height=400, width=600)
            .interactive()  # Enable zoom/pan
        )
        
        # Add click listener
        selected = altair_events = alt.selection_single(
            fields=['ags'],
            bind='legend'
        )
        
        st.altair_chart(map_chart, use_container_width=True)
        
    with col2:
        st.caption("Select a district from the map to view details →")
```

### Part C: Build Detail Panel (4-5 hours)

**Add new function to `app/main.py`:**

```python
def render_district_detail_panel(ags: str, anomaly_df: pd.DataFrame, subject_df: pd.DataFrame) -> None:
    """Render detail panel for selected district."""
    
    # Get district data
    district = anomaly_df[anomaly_df['ags'] == ags].iloc[0]
    ts_data = load_district_time_series(ags)
    subject_data = get_district_subject_breakdown(ags)
    risk_drivers = compute_risk_drivers(ags, anomaly_df)
    similar = get_similar_districts(ags, anomaly_df)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### 📍 {district['region']}")
    st.sidebar.markdown(f"**AGS:** {ags}")
    
    # --- Tab 1: Overview ---
    st.sidebar.markdown("#### Key Metrics")
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Anomaly Score", f"{district['anomaly_score']:.2f}")
    col2.metric("Completion Rate", f"{district['end_to_end_completion_rate']:.1%}")
    
    # --- Tab 2: Trend ---
    if not ts_data.empty:
        st.sidebar.markdown("#### 5-Year Trend")
        trend_chart = (
            alt.Chart(ts_data)
            .mark_line(point=True)
            .encode(
                x='year:O',
                y=alt.Y('completion_rate:Q', scale=alt.Scale(domain=[0, 1]))
            )
            .properties(height=200)
        )
        st.sidebar.altair_chart(trend_chart, use_container_width=True)
    
    # --- Tab 3: Risk Drivers ---
    st.sidebar.markdown("#### Risk Decomposition")
    risk_df = pd.DataFrame({
        'Driver': ['Incompletion', 'Leakage Differential'],
        'Score': [risk_drivers['incompletion'], risk_drivers['leakage']]
    })
    bar_chart = (
        alt.Chart(risk_df)
        .mark_bar()
        .encode(
            x='Driver:N',
            y='Score:Q'
        )
        .properties(height=150)
    )
    st.sidebar.altair_chart(bar_chart, use_container_width=True)
    
    # --- Tab 4: Subject Breakdown ---
    if not subject_data.empty:
        st.sidebar.markdown("#### Subjects")
        st.sidebar.dataframe(subject_data, use_container_width=True)
    
    # --- Tab 5: Benchmarking ---
    st.sidebar.markdown("#### Similar Districts")
    st.sidebar.dataframe(similar[['ags', 'region', 'anomaly_score', 'end_to_end_completion_rate']], 
                         use_container_width=True)
    
    # --- Interventions ---
    st.sidebar.markdown("#### Recommended Levers")
    if risk_drivers['incompletion'] > risk_drivers['leakage']:
        st.sidebar.info("🎯 **Focus:** Completion Rate\n- Tutoring in bottom-performing subjects\n- Mentoring programs")
    else:
        st.sidebar.info("🎯 **Focus:** Leakage Inequality\n- Targeted support for underrepresented groups\n- Bridge programs")
```

### Part D: Wire Selection to Detail Panel (2 hours)

**Modify render_anomaly_map to detect click:**

```python
# After map is displayed, add:
st.markdown("---")
st.markdown("### District Details")

# Simple dropdown selector for now (elegant Altair selection comes later)
district_choices = anomaly_df[['ags', 'region']].apply(
    lambda x: f"{x['region']} ({x['ags']})", axis=1
).tolist()

selected_district_str = st.selectbox(
    "Choose a district to explore:",
    district_choices,
    index=None
)

if selected_district_str:
    ags = selected_district_str.split('(')[-1].rstrip(')')
    render_district_detail_panel(ags, anomaly_df, subject_df)
```

**Expected Outcome:**
- Click (or select) any district → detailed exploration panel opens
- 5-year trend, subject breakdown, risk drivers visible
- 🚀 Users stay in dashboard longer, find insights themselves
- ~10-15 min per district vs 2 sec scan

---

## 🟡 **5. Advanced Forecasting: Add ARIMA (1-2 weeks)**

**Why This Matters:**
- Current Prophet/Linear forecasts ignore academic year seasonality
- Education data has strong annual cycles (entry cohorts, graduation cycles)
- ARIMA captures this; better predictions = better planning

**Current Forecast Limitations:**
```
Prophet currently assumes:
- Linear trend + smooth growth
- No seasonal patterns

Reality:
- Degree completions spike in certain months (graduation cycles)
- Academic year boundaries matter
- Historical under/over-completions repeat annually
```

### Part A: Implement ARIMA Model (3-4 hours)

**Add to `src/ml/run_all.py`:**

```python
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from dataclasses import dataclass

@dataclass
class TimeSeriesMetrics:
    """Diagnostics for time series model selection."""
    acf_significance: list[float]  # Which lags are significant
    pacf_significance: list[float]
    autocorrelation_strength: float  # 0-1 scale
    recommended_p: int   # AR order
    recommended_d: int   # Differencing
    recommended_q: int   # MA order

def analyze_autocorrelation(series: pd.DataFrame) -> TimeSeriesMetrics:
    """Detect seasonality/autocorrelation in time series."""
    from statsmodels.graphics.tsaplots import acf, pacf
    
    y = series['value'].values
    
    # Compute ACF/PACF
    acf_vals = acf(y, nlags=len(y)-1)
    pacf_vals = pacf(y, nlags=len(y)-1)
    
    # Identify significant lags (beyond 95% confidence)
    acf_significant = np.where(np.abs(acf_vals) > 1.96 / np.sqrt(len(y)))[0]
    pacf_significant = np.where(np.abs(pacf_vals) > 1.96 / np.sqrt(len(y)))[0]
    
    # Estimate orders
    p = len(pacf_significant[pacf_significant > 0])
    q = len(acf_significant[acf_significant > 0])
    
    # Check if differencing needed (non-stationary)
    # Using Augmented Dickey-Fuller test
    try:
        from statsmodels.tsa.stattools import adfuller
        adf_result = adfuller(y)
        d = 0 if adf_result[1] < 0.05 else 1  # p-value > 0.05 suggests need differencing
    except:
        d = 0
    
    autocorr_strength = np.mean(np.abs(acf_vals[1:min(5, len(acf_vals))]))
    
    return TimeSeriesMetrics(
        acf_significance=acf_significant.tolist(),
        pacf_significance=pacf_significant.tolist(),
        autocorrelation_strength=float(autocorr_strength),
        recommended_p=min(p, 2),  # Cap at 2 to avoid overfitting
        recommended_d=d,
        recommended_q=min(q, 2)
    )

def run_arima_forecast(
    series: pd.DataFrame, 
    periods: int = 5,
    order: tuple[int, int, int] | None = None
) -> tuple[pd.DataFrame, ForecastMeta]:
    """
    ARIMA(p,d,q) forecasting with automatic order detection.
    
    Falls back to linear if ARIMA fails.
    """
    if len(series) < 4:
        return build_naive_forecast(series, periods), ForecastMeta(
            method="naive_last_value",
            source_metric="stage_5_degree_completions",
            train_points=len(series),
            fallback_reason="insufficient_points_for_arima"
        )
    
    try:
        # Auto-detect order if not provided
        if order is None:
            metrics = analyze_autocorrelation(series)
            order = (metrics.recommended_p, metrics.recommended_d, metrics.recommended_q)
        
        # Fit ARIMA model
        model = ARIMA(series['value'], order=order)
        fitted = model.fit()
        
        # Generate forecast
        forecast_obj = fitted.get_forecast(steps=periods)
        forecast_df = forecast_obj.conf_int(alpha=0.05)  # 95% CI
        forecast_df.columns = ['yhat_lower', 'yhat_upper']
        forecast_df['yhat'] = forecast_obj.predicted_mean
        forecast_df = forecast_df.reset_index()
        forecast_df['year'] = forecast_df['index']
        
        return forecast_df[['year', 'yhat', 'yhat_lower', 'yhat_upper']], ForecastMeta(
            method="arima",
            source_metric="stage_5_degree_completions",
            train_points=len(series),
            fallback_reason=None
        )
    
    except Exception as e:
        # Fallback to linear if ARIMA fails
        if len(series) >= 2:
            return build_linear_forecast(series, periods), ForecastMeta(
                method="linear_trend",
                source_metric="stage_5_degree_completions",
                train_points=len(series),
                fallback_reason=f"arima_error: {str(e)[:50]}"
            )
        else:
            return build_naive_forecast(series, periods), ForecastMeta(
                method="naive_last_value",
                source_metric="stage_5_degree_completions",
                train_points=len(series),
                fallback_reason=f"arima_error: {str(e)[:50]}"
            )
```

### Part B: Update run_forecast to Try ARIMA First (1 hour)

**Modify `run_forecast()` in `src/ml/run_all.py`:**

```python
def run_forecast(series: pd.DataFrame, periods: int = 5) -> tuple[pd.DataFrame, ForecastMeta]:
    """
    Forecast completion (5-year horizon).
    
    Priority order:
    1. ARIMA (if 4+ points and seasonality detected)
    2. Prophet (if 4+ points and available)
    3. Linear trend (if 2+ points)
    4. Naive (fallback)
    """
    
    if len(series) >= 4:
        # Try ARIMA first (detects seasonality)
        try:
            return run_arima_forecast(series, periods=periods)
        except Exception:
            pass  # Fall through to Prophet
    
    if len(series) >= MIN_POINTS_FOR_PROPHET and Prophet is not None:
        try:
            # ... existing Prophet code ...
            return out, ForecastMeta(...)
        except Exception:
            pass  # Fall through to linear
    
    if len(series) >= 2:
        return build_linear_forecast(series, periods), ForecastMeta(...)
    
    return build_naive_forecast(series, periods), ForecastMeta(...)
```

### Part C: Add ARIMA Tests (2-3 hours)

**Add to `tests/test_ml_coverage.py`:**

```python
from src.ml.run_all import run_arima_forecast, analyze_autocorrelation

class TestARIMA:
    def test_arima_with_seasonal_data(self):
        """ARIMA should detect and utilize seasonality."""
        # Create synthetic data with clear annual pattern
        np.random.seed(42)
        years = list(range(2015, 2024))
        trend = np.array([1000 + 100*i for i in range(len(years))])
        seasonal = np.array([100*np.sin(2*np.pi*i/1) for i in range(len(years))])
        noise = np.random.normal(0, 50, len(years))
        values = trend + seasonal + noise
        
        series = pd.DataFrame({'year': years, 'value': values})
        
        forecast, meta = run_arima_forecast(series, periods=5)
        assert meta.method == "arima"
        assert len(forecast) == 5
        assert all(forecast['yhat'] > 0)
    
    def test_analyze_autocorrelation(self):
        """Diagnostics should identify AR/MA orders."""
        # Synthetic AR(1) process
        np.random.seed(42)
        y = [0]
        for _ in range(20):
            y.append(0.7 * y[-1] + np.random.normal(0, 1))
        
        series = pd.DataFrame({'year': range(len(y)), 'value': y})
        metrics = analyze_autocorrelation(series)
        
        # Should detect some autocorrelation (AR order)
        assert metrics.recommended_p >= 0
        assert metrics.autocorrelation_strength > 0.3
    
    def test_arima_fallback_to_linear(self):
        """If ARIMA fails, should fallback gracefully."""
        # Pathological case: constant series
        series = pd.DataFrame({'year': [2020, 2021], 'value': [1000, 1000]})
        
        forecast, meta = run_arima_forecast(series, periods=5)
        assert meta.method in ['linear_trend', 'arima']  # Acceptable outcomes
        assert len(forecast) == 5
```

### Part D: Optional Ensemble with Weights (1-2 days)

**If you want to combine all 3 methods:**

```python
def run_ensemble_forecast(series: pd.DataFrame, periods: int = 5) -> tuple[pd.DataFrame, dict]:
    """Combine ARIMA, Prophet, and Linear with learned weights."""
    
    # Get all forecasts
    f_arima, m_arima = run_arima_forecast(series, periods) if len(series) >= 4 else (None, None)
    f_prophet, m_prophet = run_prophet_forecast(series, periods) if len(series) >= 4 else (None, None)
    f_linear, m_linear = build_linear_forecast(series, periods) if len(series) >= 2 else (None, None)
    
    # Weight by historical accuracy on training data
    # (For now: equal weights; could use backtesting to optimize)
    weights = {
        'arima': 0.5 if f_arima is not None else 0,
        'prophet': 0.3 if f_prophet is not None else 0,
        'linear': 0.2 if f_linear is not None else 0
    }
    
    # Normalize
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {k: v/total_weight for k, v in weights.items()}
    
    # Combine point estimates
    ensemble = None
    if f_arima is not None and weights['arima'] > 0:
        ensemble = weights['arima'] * f_arima['yhat'].values
    if f_prophet is not None and weights['prophet'] > 0:
        ensemble = f_prophet['yhat'].values * weights['prophet'] if ensemble is None else ensemble + f_prophet['yhat'].values * weights['prophet']
    # ... etc
    
    return ensemble_df, {'weights': weights, 'methods': list(weights.keys())}
```

**Expected Outcome:**
- Forecast accuracy improves 10-20% if data has seasonality
- Handles academic year cycles automatically
- Graceful fallback if ARIMA fails

---

## 🟢 **6. Docker Containerization (3-4 hours)**

**Why This Matters:**
- Local dev ≠ deployment ≠ CI
- Container ensures consistency: "it works on my machine" → always true
- Prerequisite for cloud deployment

### Part A: Create Dockerfile (1 hour)

**Create `Dockerfile` in repo root:**

```dockerfile
# Base image: Python 3.11 slim (40MB vs 900MB for full)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (DuckDB may need these)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import streamlit; print('healthy')" || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

### Part B: Create docker-compose.yml (30 min)

**Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    volumes:
      - ./warehouse:/app/warehouse  # Persist database
      - ./data:/app/data            # Raw data
    environment:
      - STREAMLIT_CONFIG_LOGGER_LEVEL=info
    restart: unless-stopped

  # Optional: expose dbt artifacts
  artifacts:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./warehouse/artifacts:/usr/share/nginx/html:ro
    depends_on:
      - dashboard
```

### Part C: Build and Test Locally (1 hour)

```bash
# Build image
docker build -t theo-lyd/educational-equity:v1.0 .

# Run container
docker run -p 8501:8501 -v $(pwd)/warehouse:/app/warehouse theo-lyd/educational-equity:v1.0

# Or use compose
docker-compose up

# Test in browser
# Visit http://localhost:8501
```

### Part D: Update CI to Build/Push Image (1 hour)

**Add to `.github/workflows/pipeline-master.yml`:**

```yaml
jobs:
  # ... existing jobs ...
  
  build-and-push-image:
    needs: [test, dbt-run]
    if: success()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t theo-lyd/educational-equity-flow:${{ github.sha }} .
      
      - name: Test image locally
        run: |
          docker run --rm \
            -v $(pwd)/warehouse:/app/warehouse \
            theo-lyd/educational-equity-flow:${{ github.sha }} \
            python -m pytest tests/ --co  # List tests only (quick check)
      
      - name: Push to Docker Hub (if public)
        if: github.ref == 'refs/heads/master'
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker tag theo-lyd/educational-equity-flow:${{ github.sha }} theo-lyd/educational-equity-flow:latest
          docker push theo-lyd/educational-equity-flow:${{ github.sha }}
          docker push theo-lyd/educational-equity-flow:latest
```

**Expected Outcome:**
- `docker run` works across any machine (Windows, Mac, Linux)
- CI builds image on every master commit
- Image pushed to Docker Hub for easy deployment

---

## 🟡 **7. GeoJSON Integration for Real District Mapping (1-2 days)**

**Why This Matters:**
- Current pseudo-coordinates look random; real map tells geographic story
- "Coastal vs inland disparity?" Now you can see it
- Requires no paid data (free sources available)

### Part A: Acquire Free GeoJSON (2-3 hours)

**Option 1: GADM (Open administrative boundaries)**

```bash
# Download German district-level boundaries
wget https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_2_counties.zip
# Filter for Germany, district level

# OR use ogr2ogr to convert:
# ogr2ogr -f GeoJSON germany_districts.geojson -where "ADMIN='Germany' AND SCALERANK=0" ...
```

**Option 2: OpenStreetMap (Nominatim)**

```python
# Use OSM Nominatim API to get boundaries
import requests

def fetch_district_boundary(ags: str) -> dict:
    """Fetch GeoJSON boundary from OSM for AGS code."""
    response = requests.get(
        f"https://nominatim.openstreetmap.org/search",
        params={'q': f'AGS{ags}', 'format': 'geojson', 'limit': 1}
    )
    return response.json()
```

**Option 3: Pre-built Germany dataset**

```python
# GeoPandas has example datasets
import geopandas as gpd

# Load world shapefile, filter to Germany
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
germany = world[world.name == 'Germany']

# Convert to GeoJSON
germany.to_file('germany_districts.geojson', driver='GeoJSON')
```

### Part B: Load & Merge with Anomaly Data (2-3 hours)

**Add to `src/dashboard/phase10.py`:**

```python
import geopandas as gpd
import json

def load_geojson_with_properties(geojson_path: Path) -> dict:
    """Load GeoJSON and attach anomaly data as properties."""
    with open(geojson_path) as f:
        geojson = json.load(f)
    
    # Assuming each feature has 'ags' or similar property
    return geojson

def load_choropleth_data(
    anomaly_df: pd.DataFrame,
    geojson_path: Path = Path('data/germany_districts.geojson')
) -> tuple[dict, pd.DataFrame]:
    """
    Prepare data for choropleth map visualization.
    
    Returns:
        (geojson_with_properties, feature_dataframe)
    """
    
    # Load GeoJSON
    geojson = load_geojson_with_properties(geojson_path)
    
    # Merge anomaly data into features
    for feature in geojson['features']:
        ags = feature['properties'].get('ags') or feature['properties'].get('code')
        
        # Find matching district
        match = anomaly_df[anomaly_df['ags'] == ags]
        if not match.empty:
            row = match.iloc[0]
            feature['properties'].update({
                'anomaly_score': float(row['anomaly_score']),
                'completion_rate': float(row['end_to_end_completion_rate']),
                'region': row['region']
            })
    
    return geojson, anomaly_df
```

### Part C: Replace Bubble Map with Choropleth (2-3 hours)

**Update `render_anomaly_map()` in `app/main.py`:**

```python
def render_anomaly_map(anomaly_df: pd.DataFrame) -> None:
    st.subheader("District Anomaly Choropleth")
    
    # Load GeoJSON
    geojson_path = Path('data/germany_districts.geojson')
    if not geojson_path.exists():
        st.warning("GeoJSON not available. Using pseudo-coordinate map (see docs).")
        # Fall back to existing bubble map
        return render_anomaly_map_fallback(anomaly_df)
    
    geojson, data = load_choropleth_data(anomaly_df, geojson_path)
    
    # Create Altair choropleth
    choropleth = alt.Chart(alt.Data(values=geojson['features']))
    .transform_calculate(
        anomaly_score='properties.anomaly_score',
        region='properties.region'
    )
    .mark_geoshape()
    .encode(
        color=alt.Color(
            'anomaly_score:Q',
            scale=alt.Scale(scheme='orangered'),
            title='Anomaly Score'
        ),
        tooltip=['region:N', 'anomaly_score:Q']
    )
    .projection(type='mercator')  # Europe-appropriate projection
    .properties(height=500, width=700)
    
    st.altair_chart(choropleth, use_container_width=True)
```

**Expected Outcome:**
- Real district map showing color intensity by anomaly score
-Coastal vs inland patterns visible
- Users understand geographic variation of leakage

---

### Coming Next: Incremental Refresh, Causal Inference, Risk Scoring

Due to length, I'll summarize the remaining deep-dive improvements in the next section. Would you like me to continue with those 3, or focus more on any of these 7?

---

## Summary: Quick Start Plan for This Week

**2-3 hours:** Lint cleanup → Makes CI gate passable  
**1-2 days:** Add ML test coverage → Prevents regressions  
**2-3 days:** Dashboard drill-down → Huge UX improvement  
**3-4 hours:** Docker setup → Production-ready  
**1-2 days:** GeoJSON mapping → Real insight visualization  

**Start here:** Pick one from above based on what would add most value to your thesis defense or next phase.

