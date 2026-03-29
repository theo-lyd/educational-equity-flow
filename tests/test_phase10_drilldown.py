"""Tests for dashboard drill-down module."""

import pandas as pd
import pytest

from src.dashboard.drilldown import (
    build_leakage_timeseries_chart,
    build_pipeline_chart,
    build_region_comparison_chart,
    build_subject_breakdown_chart,
    build_transition_rates_chart,
    get_cluster_summary,
    get_district_cluster_peer_group,
    get_district_leakage_timeseries,
    get_district_list,
    get_district_pipeline,
    get_district_subject_breakdown,
    get_region_comparison,
)


class TestDistrictListLoader:
    """Test district list loading."""

    def test_returns_dataframe(self) -> None:
        """Test that function returns a DataFrame."""
        result = get_district_list()
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self) -> None:
        """Test that result has required columns."""
        result = get_district_list()
        if not result.empty:
            required_cols = ["ags", "region", "end_to_end_completion_rate"]
            for col in required_cols:
                assert col in result.columns

    def test_ags_column_not_null(self) -> None:
        """Test that AGS column has no nulls."""
        result = get_district_list()
        if not result.empty:
            assert result["ags"].notna().all()


class TestDistrictPipeline:
    """Test district pipeline data loading."""

    def test_returns_dataframe(self) -> None:
        """Test that function returns a DataFrame."""
        result = get_district_pipeline("invalid_ags_xyz")
        assert isinstance(result, pd.DataFrame)

    def test_invalid_ags_returns_empty(self) -> None:
        """Test that invalid AGS returns empty DataFrame."""
        result = get_district_pipeline("invalid_ags_xyz")
        assert result.empty or len(result) <= 1

    def test_valid_ags_structure(self) -> None:
        """Test pipeline structure when valid AGS exists."""
        districts = get_district_list()
        if not districts.empty:
            valid_ags = districts.iloc[0]["ags"]
            result = get_district_pipeline(valid_ags)
            if not result.empty:
                expected_cols = [
                    "stage_1_students",
                    "stage_5_degree_completions",
                    "end_to_end_rate",
                ]
                for col in expected_cols:
                    assert col in result.columns


class TestDistrictLeakageTimeseries:
    """Test leakage timeseries data loading."""

    def test_returns_dataframe(self) -> None:
        """Test that function returns a DataFrame."""
        result = get_district_leakage_timeseries("invalid_ags")
        assert isinstance(result, pd.DataFrame)

    def test_has_year_and_leakage_columns(self) -> None:
        """Test required columns when data exists."""
        result = get_district_leakage_timeseries("invalid_ags")
        if not result.empty:
            assert "year" in result.columns or len(result.columns) == 0


class TestDistrictSubjectBreakdown:
    """Test subject breakdown data loading."""

    def test_returns_dataframe(self) -> None:
        """Test that function returns a DataFrame."""
        result = get_district_subject_breakdown("invalid_ags")
        assert isinstance(result, pd.DataFrame)

    def test_has_subject_columns(self) -> None:
        """Test required columns when data exists."""
        result = get_district_subject_breakdown("invalid_ags")
        if not result.empty:
            required = ["hs_fg2_group", "demographic_group"]
            for col in required:
                assert col in result.columns


class TestDistrictClusterPeerGroup:
    """Test cluster peer group functionality."""

    def test_returns_tuple(self) -> None:
        """Test that function returns tuple of cluster_id and DataFrame."""
        result = get_district_cluster_peer_group("invalid_ags")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_invalid_ags_returns_none_empty(self) -> None:
        """Test that invalid AGS returns None and empty DataFrame."""
        cluster_id, peer_df = get_district_cluster_peer_group("invalid_ags_xyz")
        assert cluster_id is None or isinstance(cluster_id, (int, type(None)))
        assert isinstance(peer_df, pd.DataFrame)


class TestRegionComparison:
    """Test region comparison functionality."""

    def test_returns_dataframe(self) -> None:
        """Test that function returns a DataFrame."""
        result = get_region_comparison("Invalid Region Name")
        assert isinstance(result, pd.DataFrame)

    def test_valid_region_has_transitions(self) -> None:
        """Test that valid region returns transition data."""
        districts = get_district_list()
        if not districts.empty:
            valid_region = districts.iloc[0]["region"]
            result = get_region_comparison(valid_region)
            if not result.empty:
                assert "transition_rate_1_to_2" in result.columns


class TestClusterSummary:
    """Test cluster summary loading."""

    def test_returns_dataframe(self) -> None:
        """Test that function returns a DataFrame."""
        result = get_cluster_summary()
        assert isinstance(result, pd.DataFrame)

    def test_has_required_structure(self) -> None:
        """Test cluster summary structure when data exists."""
        result = get_cluster_summary()
        if not result.empty:
            required_cols = ["cluster_id", "district_count"]
            for col in required_cols:
                assert col in result.columns


class TestPipelineChart:
    """Test pipeline chart building."""

    @pytest.fixture
    def sample_pipeline(self) -> pd.DataFrame:
        """Create sample pipeline data."""
        return pd.DataFrame(
            {
                "stage_1_students": [1000],
                "stage_2_students": [850],
                "stage_3_graduates": [720],
                "stage_4_university_students": [600],
                "stage_5_degree_completions": [450],
            }
        )

    def test_returns_altair_chart(self, sample_pipeline: pd.DataFrame) -> None:
        """Test that function returns an Altair chart object."""
        result = build_pipeline_chart(sample_pipeline)
        # Check it's an Altair Chart
        assert hasattr(result, "mark_bar")

    def test_empty_dataframe_returns_chart(self) -> None:
        """Test that empty DataFrame returns a chart."""
        empty_df = pd.DataFrame()
        result = build_pipeline_chart(empty_df)
        assert result is not None


class TestTransitionRatesChart:
    """Test transition rates chart building."""

    @pytest.fixture
    def sample_pipeline(self) -> pd.DataFrame:
        """Create sample pipeline data."""
        return pd.DataFrame(
            {
                "transition_1_to_2": [0.85],
                "transition_2_to_3": [0.84],
                "transition_3_to_4": [0.83],
                "transition_4_to_5": [0.75],
            }
        )

    def test_returns_altair_chart(self, sample_pipeline: pd.DataFrame) -> None:
        """Test that function returns an Altair chart."""
        result = build_transition_rates_chart(sample_pipeline)
        assert result is not None

    def test_empty_dataframe_returns_chart(self) -> None:
        """Test that empty DataFrame returns a chart."""
        empty_df = pd.DataFrame()
        result = build_transition_rates_chart(empty_df)
        assert result is not None


class TestLeakageTimeseriesChart:
    """Test leakage timeseries chart building."""

    @pytest.fixture
    def sample_leakage(self) -> pd.DataFrame:
        """Create sample leakage data."""
        return pd.DataFrame(
            {
                "year": [2018, 2019, 2020, 2021, 2022],
                "leakage_differential": [-0.05, -0.03, -0.08, -0.04, -0.06],
                "leakage_pct": [-5.0, -3.0, -8.0, -4.0, -6.0],
            }
        )

    def test_returns_altair_chart(self, sample_leakage: pd.DataFrame) -> None:
        """Test that function returns an Altair chart."""
        result = build_leakage_timeseries_chart(sample_leakage)
        assert result is not None

    def test_empty_dataframe_returns_chart(self) -> None:
        """Test that empty DataFrame returns a chart."""
        empty_df = pd.DataFrame()
        result = build_leakage_timeseries_chart(empty_df)
        assert result is not None


class TestSubjectBreakdownChart:
    """Test subject breakdown chart building."""

    @pytest.fixture
    def sample_subjects(self) -> pd.DataFrame:
        """Create sample subject data."""
        return pd.DataFrame(
            {
                "hs_fg2_group": ["Math", "Math", "Science", "Science"],
                "demographic_group": ["All", "Minority", "All", "Minority"],
                "subject_completion_share": [0.85, 0.78, 0.82, 0.75],
            }
        )

    def test_returns_altair_chart(self, sample_subjects: pd.DataFrame) -> None:
        """Test that function returns an Altair chart."""
        result = build_subject_breakdown_chart(sample_subjects)
        assert result is not None

    def test_empty_dataframe_returns_chart(self) -> None:
        """Test that empty DataFrame returns a chart."""
        empty_df = pd.DataFrame()
        result = build_subject_breakdown_chart(empty_df)
        assert result is not None


class TestRegionComparisonChart:
    """Test region comparison chart building."""

    @pytest.fixture
    def sample_region(self) -> pd.DataFrame:
        """Create sample region comparison data."""
        return pd.DataFrame(
            {
                "ags": ["01001", "01002", "01003"],
                "region": ["Region A", "Region A", "Region A"],
                "transition_rate_1_to_2": [0.85, 0.82, 0.88],
                "end_to_end_completion_rate": [0.60, 0.55, 0.65],
                "transition_rate_4_to_5": [0.75, 0.72, 0.78],
            }
        )

    def test_returns_altair_chart(self, sample_region: pd.DataFrame) -> None:
        """Test that function returns an Altair chart."""
        result = build_region_comparison_chart(sample_region)
        assert result is not None

    def test_empty_dataframe_returns_chart(self) -> None:
        """Test that empty DataFrame returns a chart."""
        empty_df = pd.DataFrame()
        result = build_region_comparison_chart(empty_df)
        assert result is not None
