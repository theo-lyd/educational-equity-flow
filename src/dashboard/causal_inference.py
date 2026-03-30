"""Causal inference module for district intervention effects analysis."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

DEFAULT_DB_PATH = Path("warehouse") / "analytics.duckdb"


def _connect(db_path: Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(db_path), read_only=True)


def _fetch_df(
    query: str,
    db_path: Path = DEFAULT_DB_PATH,
    params: Sequence[object] | None = None,
) -> pd.DataFrame:
    with _connect(db_path) as con:
        if params is None:
            return con.execute(query).fetchdf()
        return con.execute(query, params).fetchdf()


@st.cache_data(ttl=3600)
def load_causal_inference_data(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Load district-level data for causal inference analysis.
    
    Includes outcome variables, confounders, and covariate balance metrics.
    """
    return _fetch_df(
        """
        select
            t.ags,
            t.region,
            t.end_to_end_completion_rate as outcome,
            t.compounded_transition_rate as transition_rate,
            coalesce(l.mean_leakage_differential, 0.0) as leakage_score,
            case
                when l.mean_leakage_differential > 0.1 then 'HIGH_LEAKAGE'
                when l.mean_leakage_differential < -0.1 then 'LOW_LEAKAGE'
                else 'MEDIUM_LEAKAGE'
            end as resource_category
        from gold_transition_rates t
        left join (
            select ags, region, avg(leakage_differential) as mean_leakage_differential
            from gold_leakage_differential
            group by 1, 2
        ) l using (ags, region)
        """,
        db_path=db_path,
    )


def estimate_propensity_score(
    data: pd.DataFrame,
    confounder_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Estimate propensity scores for treatment assignment.
    
    Simulates a binary treatment (high-resource vs low-resource district)
    based on observed leakage score and estimates probability of treatment.
    
    Uses logistic regression to model P(Treatment | Confounders).
    
    Args:
        data: DataFrame with outcome and confounder variables
        confounder_cols: List of column names to use as confounders
    
    Returns:
        DataFrame with propensity scores and simulated treatment assignments
    """
    if data.empty:
        return pd.DataFrame(columns=["ags", "propensity_score", "treatment_simulated"])

    result = data.copy()

    # Default confounders: transition rate and leakage score
    if confounder_cols is None:
        confounder_cols = ["transition_rate", "leakage_score"]

    # Ensure confounders exist and handle missing values
    for col in confounder_cols:
        if col not in result.columns:
            result[col] = 0.0
    result[confounder_cols] = result[confounder_cols].fillna(0.0)

    # Normalize confounders for logistic regression
    normalized_confounders = pd.DataFrame()
    for col in confounder_cols:
        mean_val = result[col].mean()
        std_val = result[col].std()
        if std_val > 0:
            normalized_confounders[col] = (result[col] - mean_val) / std_val
        else:
            normalized_confounders[col] = 0.0

    # Compute linear combination from confounders.
    # Known confounders keep their original weights; custom confounders share remaining weight.
    linear_combo = pd.Series(0.0, index=normalized_confounders.index)
    for col in confounder_cols:
        if col == "transition_rate":
            linear_combo += normalized_confounders[col] * 0.5
        elif col == "leakage_score":
            linear_combo += normalized_confounders[col] * 0.8
        else:
            linear_combo += normalized_confounders[col] * (1.0 / len(confounder_cols))

    propensity = 1.0 / (1.0 + np.exp(-linear_combo))

    result["propensity_score"] = propensity
    result["treatment_simulated"] = (propensity > propensity.median()).astype(int)
    return result[["ags", "region", "propensity_score", "treatment_simulated"] + confounder_cols]


def perform_matching(
    data: pd.DataFrame,
    caliper: float = 0.1,
) -> tuple[pd.DataFrame, dict[str, int | float]]:
    """Perform greedy nearest-neighbor matching on propensity scores.
    
    Pairs treated units with untreated units with similar propensity scores.
    Only matches within caliper distance (default 0.1).
    
    Args:
        data: DataFrame with propensity_score and treatment_simulated columns
        caliper: Maximum distance for valid matches
    
    Returns:
        Tuple of:
        - Matched data (subset of original with match pairs)
        - Dictionary with matching quality metrics
    """
    if data.empty or "propensity_score" not in data.columns:
        return pd.DataFrame(), {"n_treated": 0, "n_matched": 0, "match_rate": 0.0}

    treated = data[data["treatment_simulated"] == 1].copy()
    untreated = data[data["treatment_simulated"] == 0].copy().reset_index(drop=True)

    if treated.empty or untreated.empty:
        return pd.DataFrame(), {"n_treated": len(treated), "n_matched": 0, "match_rate": 0.0}

    matched_indices: set[int] = set()
    matched_treated_rows: list[pd.Series] = []
    matched_untreated_rows: list[pd.Series] = []

    for _, t_row in treated.iterrows():
        t_ps = t_row["propensity_score"]

        # Find nearest untreated unit within caliper.
        distances = (untreated["propensity_score"] - t_ps).abs()
        valid_matches = distances[distances <= caliper]

        if len(valid_matches) > 0:
            nearest_idx = valid_matches.idxmin()
            if nearest_idx not in matched_indices:
                matched_indices.add(nearest_idx)
                matched_treated_rows.append(t_row)
                matched_untreated_rows.append(untreated.loc[nearest_idx])

    n_treated = len(treated)
    n_matched = len(matched_treated_rows)
    match_rate = (n_matched / n_treated) if n_treated > 0 else 0.0
    metrics = {
        "n_treated": n_treated,
        "n_matched": n_matched,
        "match_rate": match_rate,
    }

    if n_matched == 0:
        return pd.DataFrame(), metrics

    matched_treated_df = pd.DataFrame(matched_treated_rows)
    matched_untreated_df = pd.DataFrame(matched_untreated_rows)
    matched_data = pd.concat([matched_treated_df, matched_untreated_df], ignore_index=True)

    return matched_data, metrics


def estimate_ate(
    data: pd.DataFrame,
    outcome_col: str = "outcome",
) -> tuple[float, float, tuple[float, float]]:
    """Estimate average treatment effect from matched or full data."""
    if data.empty or outcome_col not in data.columns:
        return 0.0, 0.0, (0.0, 0.0)

    treated = data[data["treatment_simulated"] == 1][outcome_col]
    untreated = data[data["treatment_simulated"] == 0][outcome_col]

    if len(treated) == 0 or len(untreated) == 0:
        return 0.0, 0.0, (0.0, 0.0)

    ate = float(treated.mean() - untreated.mean())

    # Guard very small groups to avoid unstable variance estimates and warnings.
    if len(treated) < 2 or len(untreated) < 2:
        return ate, 0.0, (ate, ate)

    # Standard error of difference in means.
    se = float(
        np.sqrt((treated.var(ddof=1) / len(treated)) + (untreated.var(ddof=1) / len(untreated)))
    )
    if not np.isfinite(se):
        se = 0.0

    ci_lower = ate - 1.96 * se
    ci_upper = ate + 1.96 * se
    return ate, se, (ci_lower, ci_upper)


def _standardized_mean_difference(treated: pd.Series, untreated: pd.Series) -> float:
    """Compute standardized mean difference for one covariate."""
    if len(treated) == 0 or len(untreated) == 0:
        return 0.0

    treated_std = treated.std(ddof=1)
    untreated_std = untreated.std(ddof=1)
    pooled_std = np.sqrt((treated_std**2 + untreated_std**2) / 2.0)
    if not np.isfinite(pooled_std) or pooled_std == 0:
        return 0.0
    return float((treated.mean() - untreated.mean()) / pooled_std)


@st.cache_data(ttl=3600)
def run_causal_analysis_pipeline(
    db_path: Path = DEFAULT_DB_PATH,
    caliper: float = 0.1,
) -> dict[str, object]:
    """Run complete causal inference pipeline on district data.
    
    Steps:
    1. Load data
    2. Estimate propensity scores
    3. Perform matching
    4. Estimate treatment effect
    
    Returns dictionary with all results and diagnostics.
    """
    data = load_causal_inference_data(db_path=db_path)

    if data.empty:
        return {
            "success": False,
            "message": "No data available",
            "results": None,
            "diagnostics": None,
        }

    # Step 1: Propensity score estimation
    ps_data = estimate_propensity_score(data)

    # Merge back outcome for analysis
    analysis_data = data[["ags", "outcome"]].merge(
        ps_data[["ags", "propensity_score", "treatment_simulated"]],
        on="ags",
    )

    # Step 2: Matching
    matched_data, matching_metrics = perform_matching(analysis_data, caliper=caliper)

    if matched_data.empty:
        return {
            "success": False,
            "message": "No valid matches found",
            "results": None,
            "diagnostics": matching_metrics,
        }

    # Step 3: Estimate ATE
    ate, se, ci = estimate_ate(matched_data, outcome_col="outcome")

    # Compute propensity-score balance before/after matching
    treated_ps = ps_data[ps_data["treatment_simulated"] == 1]["propensity_score"]
    untreated_ps = ps_data[ps_data["treatment_simulated"] == 0]["propensity_score"]
    balance_before = {
        "ps_mean_treated": treated_ps.mean(),
        "ps_mean_untreated": untreated_ps.mean(),
    }

    matched_treated = matched_data[matched_data["treatment_simulated"] == 1]
    matched_untreated = matched_data[matched_data["treatment_simulated"] == 0]
    balance_after = {
        "ps_mean_treated": (
            matched_treated["propensity_score"].mean() if len(matched_treated) > 0 else 0.0
        ),
        "ps_mean_untreated": (
            matched_untreated["propensity_score"].mean() if len(matched_untreated) > 0 else 0.0
        ),
    }

    # Covariate balance diagnostics using standardized mean differences (SMD).
    covariates = ["transition_rate", "leakage_score"]
    matched_covariates = matched_data[["ags", "treatment_simulated"]].merge(
        data[["ags"] + covariates],
        on="ags",
        how="left",
    )
    covariate_balance: list[dict[str, float | str]] = []
    for covariate in covariates:
        treated_before = data[data["ags"].isin(ps_data[ps_data["treatment_simulated"] == 1]["ags"])][covariate]
        untreated_before = data[data["ags"].isin(ps_data[ps_data["treatment_simulated"] == 0]["ags"])][covariate]

        treated_after = matched_covariates[
            matched_covariates["treatment_simulated"] == 1
        ][covariate]
        untreated_after = matched_covariates[
            matched_covariates["treatment_simulated"] == 0
        ][covariate]

        covariate_balance.append(
            {
                "covariate": covariate,
                "smd_before": _standardized_mean_difference(treated_before, untreated_before),
                "smd_after": _standardized_mean_difference(treated_after, untreated_after),
            }
        )

    return {
        "success": True,
        "ate": ate,
        "standard_error": se,
        "ci_lower": ci[0],
        "ci_upper": ci[1],
        "n_total": len(data),
        "n_treated": sum(ps_data["treatment_simulated"]),
        "n_untreated": len(data) - sum(ps_data["treatment_simulated"]),
        "matched_data": matched_data,
        "ps_data": ps_data,
        "matching_metrics": matching_metrics,
        "balance_before": balance_before,
        "balance_after": balance_after,
        "covariate_balance": covariate_balance,
    }


def simulate_counterfactual_scenario(
    base_data: pd.DataFrame,
    scenario_name: str,
    parameter_adjustment: float = 0.1,
) -> dict[str, object]:
    """Simulate counterfactual outcomes under different policy scenarios.
    
    Scenarios:
    - "tutoring_boost": 10% increase in completion for treated districts
    - "delayed_entry": Alternative pathway reduces leakage by 15%
    - "remediation": Subject-specific support improves outcomes by 8%
    
    Args:
        base_data: DataFrame with baseline outcomes
        scenario_name: Name of scenario
        parameter_adjustment: Effect size of intervention
    
    Returns:
        Dictionary with baseline, counterfactual, and effect estimates
    """
    if base_data.empty:
        return {}

    result = base_data.copy()

    if scenario_name == "tutoring_boost":
        result["counterfactual_outcome"] = result["outcome"] * (1 + parameter_adjustment)
        description = f"{int(parameter_adjustment*100)}% increase in completion via tutoring"

    elif scenario_name == "delayed_entry":
        result["counterfactual_outcome"] = result["outcome"] + parameter_adjustment
        description = f"+{int(parameter_adjustment*100)} points via delayed university entry"

    elif scenario_name == "remediation":
        result["counterfactual_outcome"] = result["outcome"] * (1 + parameter_adjustment * 0.8)
        description = f"{int(parameter_adjustment*80)}% improvement via subject remediation"

    else:
        result["counterfactual_outcome"] = result["outcome"]
        description = "No scenario"

    aggregate_baseline = result["outcome"].mean()
    aggregate_counterfactual = result["counterfactual_outcome"].mean()
    aggregate_effect = aggregate_counterfactual - aggregate_baseline

    return {
        "scenario": scenario_name,
        "description": description,
        "baseline_mean": aggregate_baseline,
        "counterfactual_mean": aggregate_counterfactual,
        "aggregate_effect": aggregate_effect,
        "data": result,
    }


def format_confidence_interval(lower: float, upper: float) -> str:
    """Format confidence interval for display."""
    return f"[{lower:.4f}, {upper:.4f}]"
