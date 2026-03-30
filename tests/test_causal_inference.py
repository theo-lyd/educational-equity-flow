"""Tests for causal inference module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.dashboard.causal_inference import (
    estimate_ate,
    estimate_propensity_score,
    format_confidence_interval,
    perform_matching,
    run_causal_analysis_pipeline,
    simulate_counterfactual_scenario,
)


class TestPropensityScoreEstimation:
    """Test propensity score estimation."""

    def test_empty_dataframe(self) -> None:
        """Empty data returns empty propensity scores."""
        result = estimate_propensity_score(pd.DataFrame())
        assert result.empty

    def test_propensity_scores_in_range(self) -> None:
        """Propensity scores are between 0 and 1."""
        data = pd.DataFrame(
            {
                "ags": ["001", "002", "003", "004"],
                "region": ["A", "B", "A", "B"],
                "transition_rate": [0.5, 0.6, 0.7, 0.8],
                "leakage_score": [-0.1, 0.0, 0.1, 0.2],
            }
        )
        result = estimate_propensity_score(data)

        assert (result["propensity_score"] >= 0).all()
        assert (result["propensity_score"] <= 1).all()

    def test_treatment_assignment_binary(self) -> None:
        """Treatment assignment is binary (0 or 1)."""
        data = pd.DataFrame(
            {
                "ags": ["001", "002", "003", "004"],
                "region": ["A", "B", "A", "B"],
                "transition_rate": [0.5, 0.6, 0.7, 0.8],
                "leakage_score": [-0.1, 0.0, 0.1, 0.2],
            }
        )
        result = estimate_propensity_score(data)

        assert result["treatment_simulated"].dtype == "int64"
        assert set(result["treatment_simulated"].unique()) <= {0, 1}

    def test_custom_confounders(self) -> None:
        """Custom confounder columns are used."""
        data = pd.DataFrame(
            {
                "ags": ["001", "002", "003", "004"],
                "region": ["A", "B", "A", "B"],
                "transition_rate": [0.5, 0.6, 0.7, 0.8],
                "leakage_score": [-0.1, 0.0, 0.1, 0.2],
                "custom_var": [1, 2, 3, 4],
            }
        )
        result = estimate_propensity_score(data, confounder_cols=["custom_var"])

        assert "custom_var" in result.columns


class TestMatching:
    """Test propensity score matching."""

    def test_empty_dataframe(self) -> None:
        """Empty data returns empty matches."""
        result, metrics = perform_matching(pd.DataFrame())
        assert result.empty
        assert metrics["n_matched"] == 0

    def test_matching_quality_metrics(self) -> None:
        """Matching returns quality metrics."""
        data = pd.DataFrame(
            {
                "propensity_score": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
                "treatment_simulated": [1, 1, 1, 1, 0, 0, 0, 0],
            }
        )
        result, metrics = perform_matching(data, caliper=0.15)

        assert "n_treated" in metrics
        assert "n_matched" in metrics
        assert "match_rate" in metrics
        assert 0 <= metrics["match_rate"] <= 1

    def test_caliper_reduces_matches(self) -> None:
        """Smaller caliper results in fewer matches."""
        data = pd.DataFrame(
            {
                "propensity_score": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
                "treatment_simulated": [1, 1, 1, 1, 0, 0, 0, 0],
            }
        )

        _, metrics_large = perform_matching(data, caliper=0.5)
        _, metrics_small = perform_matching(data, caliper=0.05)

        assert metrics_large["n_matched"] >= metrics_small["n_matched"]


class TestATE:
    """Test Average Treatment Effect estimation."""

    def test_ate_zero_when_equal_groups(self) -> None:
        """ATE is zero when treatment and control have equal outcomes."""
        data = pd.DataFrame(
            {
                "treatment_simulated": [1, 1, 0, 0],
                "outcome": [0.5, 0.5, 0.5, 0.5],
            }
        )
        ate, se, ci = estimate_ate(data)

        assert ate == pytest.approx(0.0, abs=0.0001)

    def test_ate_positive_when_treatment_higher(self) -> None:
        """ATE is positive when treatment group has higher outcomes."""
        data = pd.DataFrame(
            {
                "treatment_simulated": [1] * 10 + [0] * 10,
                "outcome": [0.8] * 10 + [0.5] * 10,
            }
        )
        ate, se, ci = estimate_ate(data)

        assert ate > 0
        assert ate == pytest.approx(0.3, abs=0.01)

    def test_confidence_interval_incorporates_uncertainty(self) -> None:
        """Confidence interval is wider with more noise."""
        # Low variance data
        data_low = pd.DataFrame(
            {
                "treatment_simulated": [1] * 100 + [0] * 100,
                "outcome": [0.8] * 100 + [0.5] * 100,
            }
        )
        _, _, ci_low = estimate_ate(data_low)

        # High variance data (same mean but more noise)
        np.random.seed(42)
        outcome_high = np.concatenate([
            np.random.normal(0.8, 0.1, 100),
            np.random.normal(0.5, 0.1, 100),
        ])
        data_high = pd.DataFrame(
            {
                "treatment_simulated": [1] * 100 + [0] * 100,
                "outcome": outcome_high,
            }
        )
        _, _, ci_high = estimate_ate(data_high)

        ci_low_width = ci_low[1] - ci_low[0]
        ci_high_width = ci_high[1] - ci_high[0]

        assert ci_high_width > ci_low_width

    def test_empty_dataframe(self) -> None:
        """Empty data returns zero effect."""
        ate, se, ci = estimate_ate(pd.DataFrame())
        assert ate == 0.0
        assert se == 0.0

    def test_small_groups_return_point_ci(self) -> None:
        """Very small groups return deterministic CI at point estimate."""
        data = pd.DataFrame(
            {
                "treatment_simulated": [1, 0],
                "outcome": [0.7, 0.5],
            }
        )
        ate, se, ci = estimate_ate(data)

        assert ate == pytest.approx(0.2, abs=0.0001)
        assert se == 0.0
        assert ci[0] == pytest.approx(ate, abs=0.0001)
        assert ci[1] == pytest.approx(ate, abs=0.0001)


class TestCausalPipelineDiagnostics:
    """Test diagnostics produced by the causal pipeline."""

    def test_pipeline_includes_covariate_balance_smd(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Pipeline returns covariate SMD diagnostics before/after matching."""
        mock_data = pd.DataFrame(
            {
                "ags": ["001", "002", "003", "004", "005", "006"],
                "region": ["A", "A", "B", "B", "C", "C"],
                "outcome": [0.58, 0.62, 0.49, 0.52, 0.66, 0.70],
                "transition_rate": [0.55, 0.60, 0.45, 0.48, 0.63, 0.68],
                "leakage_score": [-0.10, -0.06, 0.12, 0.09, -0.02, -0.01],
                "resource_category": [
                    "LOW_LEAKAGE",
                    "LOW_LEAKAGE",
                    "HIGH_LEAKAGE",
                    "HIGH_LEAKAGE",
                    "MEDIUM_LEAKAGE",
                    "MEDIUM_LEAKAGE",
                ],
            }
        )

        monkeypatch.setattr(
            "src.dashboard.causal_inference.load_causal_inference_data",
            lambda db_path=None: mock_data,
        )
        run_causal_analysis_pipeline.clear()
        result = run_causal_analysis_pipeline(caliper=1.0)

        assert result["success"] is True
        assert "covariate_balance" in result
        assert isinstance(result["covariate_balance"], list)
        assert len(result["covariate_balance"]) == 2

        covariates = {entry["covariate"] for entry in result["covariate_balance"]}
        assert covariates == {"transition_rate", "leakage_score"}

        for entry in result["covariate_balance"]:
            assert "smd_before" in entry
            assert "smd_after" in entry
            assert isinstance(entry["smd_before"], float)
            assert isinstance(entry["smd_after"], float)


class TestCounterfactualScenarios:
    """Test counterfactual scenario simulation."""

    def test_empty_dataframe(self) -> None:
        """Empty data returns empty results."""
        result = simulate_counterfactual_scenario(pd.DataFrame(), "tutoring_boost")
        assert result == {}

    def test_tutoring_boost_increases_outcome(self) -> None:
        """Tutoring boost scenario increases completion."""
        data = pd.DataFrame(
            {
                "outcome": [0.5, 0.6, 0.7, 0.8],
            }
        )
        result = simulate_counterfactual_scenario(data, "tutoring_boost", 0.1)

        assert result["aggregate_effect"] > 0
        assert result["counterfactual_mean"] > result["baseline_mean"]

    def test_delayed_entry_adds_points(self) -> None:
        """Delayed entry scenario adds fixed points to completion."""
        data = pd.DataFrame(
            {
                "outcome": [0.5, 0.6, 0.7, 0.8],
            }
        )
        result = simulate_counterfactual_scenario(data, "delayed_entry", 0.05)

        assert result["aggregate_effect"] == pytest.approx(0.05, abs=0.001)

    def test_remediation_effect_proportional(self) -> None:
        """Remediation effect scales with parameter."""
        data = pd.DataFrame(
            {
                "outcome": [0.5, 0.6, 0.7, 0.8],
            }
        )
        result1 = simulate_counterfactual_scenario(data, "remediation", 0.1)
        result2 = simulate_counterfactual_scenario(data, "remediation", 0.2)

        assert result2["aggregate_effect"] > result1["aggregate_effect"]

    def test_scenario_includes_description(self) -> None:
        """Scenario result includes human-readable description."""
        data = pd.DataFrame({"outcome": [0.5]})
        result = simulate_counterfactual_scenario(data, "tutoring_boost")

        assert "description" in result
        assert len(result["description"]) > 0


class TestFormatConfidenceInterval:
    """Test confidence interval formatting."""

    def test_format_ci_positive_range(self) -> None:
        """Format positive confidence interval."""
        result = format_confidence_interval(0.1, 0.5)
        assert "[" in result
        assert "]" in result
        assert "0.1" in result
        assert "0.5" in result

    def test_format_ci_negative_range(self) -> None:
        """Format negative confidence interval."""
        result = format_confidence_interval(-0.2, 0.1)
        assert "[" in result
        assert "]" in result

    def test_format_ci_zero_bounds(self) -> None:
        """Format confidence interval at zero."""
        result = format_confidence_interval(-0.05, 0.05)
        assert "[" in result
        assert "]" in result
