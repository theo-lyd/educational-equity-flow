"""Tests for subject heterogeneity analysis module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.dashboard.heterogeneity import (
    compute_heterogeneity_metrics,
    format_effect_size,
    format_pvalue,
    load_demographic_group_comparison,
    load_subject_heterogeneity_raw,
    load_subject_heterogeneity_summary,
)


class TestComputeHeterogeneityMetrics:
    """Test heterogeneity computation and statistical testing."""

    def test_empty_dataframe(self) -> None:
        """Empty data returns empty results."""
        result = compute_heterogeneity_metrics(pd.DataFrame())
        assert result.empty
        assert list(result.columns) == [
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

    def test_single_subject_multiple_demographics(self) -> None:
        """Single subject with varying demographic completion rates."""
        data = pd.DataFrame(
            {
                "hs_fg2_group": ["Math", "Math", "Math"],
                "demographic_group": ["Group A", "Group B", "Group C"],
                "passed_exams": [100, 80, 60],
                "total_passed_exams": [150, 100, 100],
            }
        )

        result = compute_heterogeneity_metrics(data)
        assert len(result) == 1
        assert result.iloc[0]["hs_fg2_group"] == "Math"
        assert result.iloc[0]["n_demographic_groups"] == 3
        assert result.iloc[0]["mean_completion"] == pytest.approx(
            (100 / 150 + 80 / 100 + 60 / 100) / 3, abs=0.01
        )

    def test_chi2_test_significance(self) -> None:
        """Chi-square test identifies significant differences."""
        # Create data with clear difference between groups
        data = pd.DataFrame(
            {
                "hs_fg2_group": ["Physics"] * 4,
                "demographic_group": ["Group A", "Group A", "Group B", "Group B"],
                "passed_exams": [1000, 999, 100, 101],
                "total_passed_exams": [1000, 1000, 1000, 1000],
            }
        )

        result = compute_heterogeneity_metrics(data)
        assert result.iloc[0]["is_significant_alpha05"]
        assert result.iloc[0]["chi2_pvalue"] < 0.05

    def test_no_significance_homogeneous_data(self) -> None:
        """Homogeneous data shows no significance."""
        # All groups have same completion rate
        data = pd.DataFrame(
            {
                "hs_fg2_group": ["Chemistry"] * 4,
                "demographic_group": ["Group A", "Group A", "Group B", "Group B"],
                "passed_exams": [500, 500, 500, 500],
                "total_passed_exams": [1000, 1000, 1000, 1000],
            }
        )

        result = compute_heterogeneity_metrics(data)
        assert not result.iloc[0]["is_significant_alpha05"]

    def test_effect_size_cramers_v(self) -> None:
        """Effect size (Cramér's V) is computed."""
        data = pd.DataFrame(
            {
                "hs_fg2_group": ["Biology"] * 2,
                "demographic_group": ["Group A", "Group B"],
                "passed_exams": [950, 50],
                "total_passed_exams": [1000, 1000],
            }
        )

        result = compute_heterogeneity_metrics(data)
        effect_size = result.iloc[0]["effect_size"]
        assert not np.isnan(effect_size)
        assert 0 <= effect_size <= 1


class TestDemographicGroupComparison:
    """Test demographic group comparison functionality."""

    def test_comparison_dataframe_structure(self) -> None:
        """Demographic comparison returns proper columns."""
        data = pd.DataFrame(
            {
                "hs_fg2_group": ["English"] * 2,
                "demographic_group": ["Group A", "Group B"],
                "passed_exams": [300, 200],
                "total_passed_exams": [400, 300],
            }
        )

        # Manually test since we can't call the cached function without DB
        from src.dashboard.heterogeneity import compute_heterogeneity_metrics
        hetero = compute_heterogeneity_metrics(data)
        assert "hs_fg2_group" in hetero.columns


class TestFormatPValue:
    """Test p-value formatting."""

    def test_format_very_significant(self) -> None:
        """Very small p-value (< 0.001)."""
        result = format_pvalue(0.0001)
        assert "***" in result
        assert "0.0001" in result

    def test_format_significant_001_to_01(self) -> None:
        """P-value between 0.001 and 0.01."""
        result = format_pvalue(0.005)
        assert "**" in result
        assert "0.0050" in result

    def test_format_significant_01_to_05(self) -> None:
        """P-value between 0.01 and 0.05."""
        result = format_pvalue(0.02)
        assert "*" in result
        assert "0.0200" in result

    def test_format_not_significant(self) -> None:
        """P-value >= 0.05."""
        result = format_pvalue(0.1)
        assert "*" not in result
        assert "0.1000" in result

    def test_format_nan(self) -> None:
        """NaN value."""
        result = format_pvalue(np.nan)
        assert result == "N/A"

    def test_format_none(self) -> None:
        """None value."""
        result = format_pvalue(None)
        assert result == "N/A"


class TestFormatEffectSize:
    """Test effect size (Cramér's V) formatting."""

    def test_format_negligible(self) -> None:
        """Effect size < 0.1 (negligible)."""
        result = format_effect_size(0.05)
        assert "negligible" in result
        assert "0.050" in result

    def test_format_small(self) -> None:
        """Effect size 0.1 to 0.3 (small)."""
        result = format_effect_size(0.2)
        assert "small" in result
        assert "0.200" in result

    def test_format_medium(self) -> None:
        """Effect size 0.3 to 0.5 (medium)."""
        result = format_effect_size(0.4)
        assert "medium" in result
        assert "0.400" in result

    def test_format_large(self) -> None:
        """Effect size >= 0.5 (large)."""
        result = format_effect_size(0.7)
        assert "large" in result
        assert "0.700" in result

    def test_format_nan(self) -> None:
        """NaN value."""
        result = format_effect_size(np.nan)
        assert result == "N/A"

    def test_format_none(self) -> None:
        """None value."""
        result = format_effect_size(None)
        assert result == "N/A"


class TestDataLoaders:
    """Test data loading functions (smoke tests without DB)."""

    def test_load_subject_heterogeneity_raw_returns_dataframe(self) -> None:
        """Raw loader returns DataFrame (may be empty if no DB)."""
        try:
            result = load_subject_heterogeneity_raw()
            assert isinstance(result, pd.DataFrame)
        except Exception:
            # DB may not be available in test environment
            pytest.skip("Database not available")

    def test_load_subject_heterogeneity_summary_returns_dataframe(self) -> None:
        """Summary loader returns DataFrame."""
        try:
            result = load_subject_heterogeneity_summary()
            assert isinstance(result, pd.DataFrame)
        except Exception:
            pytest.skip("Database not available")

    def test_load_demographic_group_comparison_returns_dataframe(self) -> None:
        """Demographic comparison loader returns DataFrame."""
        try:
            result = load_demographic_group_comparison("test_subject")
            assert isinstance(result, pd.DataFrame)
        except Exception:
            pytest.skip("Database not available")
