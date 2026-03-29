"""Subject heterogeneity analysis module with statistical testing."""

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
def load_subject_heterogeneity_raw(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Load raw subject resilience data for heterogeneity calculation.
    
    Includes school type and demographic breakdowns for statistical testing.
    """
    return _fetch_df(
        """
        select
            ags,
            hs_fg2_group,
            demographic_group,
            subject_completion_share,
            passed_exams,
            total_passed_exams
        from gold_subject_resilience
        where hs_fg2_group is not null
            and demographic_group is not null
        """,
        db_path=db_path,
    )


def compute_heterogeneity_metrics(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Compute heterogeneity metrics and statistical significance per subject group.
    
    For each subject (hs_fg2_group), test if completion rates differ significantly
    across demographic groups using chi-square test (for binary outcomes) or
    Kruskal-Wallis test (for continuous completion share).
    
    Returns DataFrame with columns:
    - hs_fg2_group: Subject group name
    - n_demographic_groups: Number of demographic groups in subject
    - mean_completion: Mean completion rate across all demographics
    - std_completion: Std dev of completion rates
    - variance_completion: Variance of completion rates
    - chi2_stat: Chi-square test statistic (if applicable)
    - chi2_pvalue: P-value for chi-square test
    - is_significant_alpha05: Boolean if p-value < 0.05
    - effect_size: Cramér's V (effect size for chi-square)
    """
    if data.empty:
        return pd.DataFrame(
            columns=[
                "hs_fg2_group",
                "n_demographic_groups",
                "mean_completion",
                "std_completion",
                "variance_completion",
                "chi2_stat",
                "chi2_pvalue",
                "is_significant_alpha05",
                "effect_size",
            ]
        )

    results: list[dict[str, object]] = []

    for subject_group in data["hs_fg2_group"].unique():
        subject_data = data[data["hs_fg2_group"] == subject_group]

        # Extract per-demographic completion rates
        demographic_groups = subject_data["demographic_group"].unique()
        completion_rates: list[float] = []
        contingency_data: list[list[int | float]] = []

        for demo_group in demographic_groups:
            demo_data = subject_data[subject_data["demographic_group"] == demo_group]
            total_passed = demo_data["passed_exams"].sum()
            total_exams = demo_data["total_passed_exams"].sum()

            if total_exams > 0:
                rate = total_passed / total_exams
                completion_rates.append(rate)
                contingency_data.append([int(total_passed), int(total_exams - total_passed)])
            else:
                completion_rates.append(0.0)
                contingency_data.append([0, 0])

        mean_completion = float(np.mean(completion_rates))
        std_completion = float(np.std(completion_rates))
        variance_completion = float(np.var(completion_rates))

        # Chi-square test on contingency table
        chi2_stat = np.nan
        chi2_pvalue = np.nan
        effect_size = np.nan

        if len(contingency_data) > 1 and sum(sum(row) for row in contingency_data) > 0:
            try:
                contingency_array = np.array(contingency_data)
                chi2_stat, chi2_pvalue, _, _ = stats.chi2_contingency(contingency_array)
                chi2_stat = float(chi2_stat)
                chi2_pvalue = float(chi2_pvalue)

                # Cramér's V effect size
                n = contingency_array.sum()
                min_dim = min(contingency_array.shape) - 1
                effect_size = float(np.sqrt(chi2_stat / (n * min_dim))) if min_dim > 0 else np.nan
            except (ValueError, ZeroDivisionError):
                chi2_stat = np.nan
                chi2_pvalue = np.nan
                effect_size = np.nan

        is_significant = (
            not np.isnan(chi2_pvalue) and chi2_pvalue < 0.05
        ) if chi2_pvalue is not None else False

        results.append(
            {
                "hs_fg2_group": subject_group,
                "n_demographic_groups": len(demographic_groups),
                "mean_completion": mean_completion,
                "std_completion": std_completion,
                "variance_completion": variance_completion,
                "chi2_stat": chi2_stat,
                "chi2_pvalue": chi2_pvalue,
                "is_significant_alpha05": is_significant,
                "effect_size": effect_size,
            }
        )

    return pd.DataFrame(results).sort_values("chi2_pvalue", na_position="last")


@st.cache_data(ttl=3600)
def load_subject_heterogeneity_summary(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Load pre-computed heterogeneity summary for all subjects."""
    raw_data = load_subject_heterogeneity_raw(db_path=db_path)
    return compute_heterogeneity_metrics(raw_data)


@st.cache_data(ttl=3600)
def load_demographic_group_comparison(
    subject_group: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    """Load detailed demographic comparison for a specific subject group.
    
    Returns completion rates and sample sizes per demographic group.
    """
    raw_data = load_subject_heterogeneity_raw(db_path=db_path)
    subject_data = raw_data[raw_data["hs_fg2_group"] == subject_group]

    if subject_data.empty:
        return pd.DataFrame(
            columns=[
                "demographic_group",
                "completion_rate",
                "passed_exams",
                "total_exams",
                "n_districts",
            ]
        )

    results: list[dict[str, object]] = []

    for demo_group in subject_data["demographic_group"].unique():
        demo_data = subject_data[subject_data["demographic_group"] == demo_group]
        total_passed = demo_data["passed_exams"].sum()
        total_exams = demo_data["total_passed_exams"].sum()

        completion_rate = (total_passed / total_exams) if total_exams > 0 else 0.0

        results.append(
            {
                "demographic_group": demo_group,
                "completion_rate": completion_rate,
                "passed_exams": int(total_passed),
                "total_exams": int(total_exams),
                "n_districts": len(demo_data),
            }
        )

    return pd.DataFrame(results).sort_values("completion_rate", ascending=False)


def format_pvalue(pval: float | None) -> str:
    """Format p-value for display with significance stars."""
    if pval is None or np.isnan(pval):
        return "N/A"
    if pval < 0.001:
        return f"{pval:.4f}***"
    if pval < 0.01:
        return f"{pval:.4f}**"
    if pval < 0.05:
        return f"{pval:.4f}*"
    return f"{pval:.4f}"


def format_effect_size(es: float | None) -> str:
    """Format effect size (Cramér's V) with interpretation."""
    if es is None or np.isnan(es):
        return "N/A"
    if es < 0.1:
        return f"{es:.3f} (negligible)"
    if es < 0.3:
        return f"{es:.3f} (small)"
    if es < 0.5:
        return f"{es:.3f} (medium)"
    return f"{es:.3f} (large)"
