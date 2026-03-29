"""Tests for ARIMA forecasting module."""

import pandas as pd
import pytest

from src.ml.arima_forecast import (
    build_arima_forecast,
    check_stationarity,
    compare_arima_models,
    find_optimal_arima_order,
)


class TestStationarityCheck:
    """Test stationarity checking functionality."""

    def test_stationary_series(self) -> None:
        """Test detection of stationary series."""
        # White noise series (stationary)
        import numpy as np

        np.random.seed(42)
        series = pd.Series(np.random.normal(0, 1, 50))
        result = check_stationarity(series)
        # Stationary series should return True
        assert isinstance(result, bool)

    def test_non_stationary_series(self) -> None:
        """Test detection of non-stationary series."""
        # Trending series (non-stationary)
        series = pd.Series(range(50), dtype=float)
        result = check_stationarity(series)
        assert isinstance(result, bool)

    def test_empty_series(self) -> None:
        """Test handling of empty series."""
        series = pd.Series([], dtype=float)
        result = check_stationarity(series)
        assert result is False

    def test_single_value_series(self) -> None:
        """Test handling of single-value series."""
        series = pd.Series([1.0])
        result = check_stationarity(series)
        assert result is False


class TestOptimalARIMAOrder:
    """Test optimal ARIMA order finding."""

    def test_default_order_short_series(self) -> None:
        """Test default order for very short series."""
        series = pd.Series([1.0, 2.0])
        order = find_optimal_arima_order(series)
        assert order == (1, 0, 1)

    def test_finds_order_for_valid_series(self) -> None:
        """Test order selection for valid time series."""
        import numpy as np

        np.random.seed(42)
        # Generate AR(1) process
        series = pd.Series(np.random.normal(0, 1, 30))
        order = find_optimal_arima_order(series)
        assert isinstance(order, tuple)
        assert len(order) == 3
        assert all(isinstance(x, int) for x in order)

    def test_order_components_within_bounds(self) -> None:
        """Test that found order respects bounds."""
        import numpy as np

        np.random.seed(42)
        series = pd.Series(np.random.normal(0, 1, 30))
        order = find_optimal_arima_order(series, max_p=3, max_d=1, max_q=3)
        p, d, q = order
        assert 0 <= p <= 3
        assert 0 <= d <= 1
        assert 0 <= q <= 3

    def test_respects_max_parameters(self) -> None:
        """Test that function respects maximum parameter constraints."""
        import numpy as np

        np.random.seed(42)
        series = pd.Series(np.random.normal(0, 1, 30))
        order = find_optimal_arima_order(series, max_p=2, max_d=1, max_q=2)
        p, d, q = order
        assert p <= 2 and d <= 1 and q <= 2


class TestBuildARIMAForecast:
    """Test ARIMA forecast building."""

    @pytest.fixture
    def sample_series(self) -> pd.DataFrame:
        """Create sample time series data."""
        return pd.DataFrame(
            {
                "year": [2018, 2019, 2020, 2021, 2022],
                "value": [100.0, 110.0, 105.0, 115.0, 120.0],
            }
        )

    def test_forecast_dataframe_structure(self, sample_series: pd.DataFrame) -> None:
        """Test that forecast output has correct structure."""
        forecast = build_arima_forecast(sample_series, periods=3)
        assert isinstance(forecast, pd.DataFrame)
        assert list(forecast.columns) == ["year", "yhat", "yhat_lower", "yhat_upper"]

    def test_forecast_row_count(self, sample_series: pd.DataFrame) -> None:
        """Test that forecast has correct number of rows."""
        periods = 3
        forecast = build_arima_forecast(sample_series, periods=periods)
        assert len(forecast) == periods

    def test_forecast_years_sequential(self, sample_series: pd.DataFrame) -> None:
        """Test that forecast years are sequential."""
        forecast = build_arima_forecast(sample_series, periods=3)
        years = forecast["year"].values
        expected_years = [2023, 2024, 2025]
        assert list(years) == expected_years

    def test_forecast_bounds_correct(self, sample_series: pd.DataFrame) -> None:
        """Test that lower bound < mean < upper bound."""
        forecast = build_arima_forecast(sample_series, periods=3)
        for _idx, row in forecast.iterrows():
            assert row["yhat_lower"] < row["yhat"] < row["yhat_upper"]

    def test_all_values_numeric(self, sample_series: pd.DataFrame) -> None:
        """Test that all forecast values are numeric."""
        forecast = build_arima_forecast(sample_series, periods=3)
        for col in ["yhat", "yhat_lower", "yhat_upper"]:
            assert forecast[col].dtype in [float, "float64"]

    def test_insufficient_data_raises(self) -> None:
        """Test that insufficient data raises ValueError."""
        short_series = pd.DataFrame({"year": [2020, 2021], "value": [100.0, 110.0]})
        with pytest.raises(ValueError, match="ARIMA requires at least 3 data points"):
            build_arima_forecast(short_series, periods=2)

    def test_empty_series_raises(self) -> None:
        """Test that empty series raises ValueError."""
        empty_series = pd.DataFrame({"year": [], "value": []})
        with pytest.raises(ValueError):
            build_arima_forecast(empty_series, periods=2)

    def test_custom_order(self, sample_series: pd.DataFrame) -> None:
        """Test forecast with custom ARIMA order."""
        forecast = build_arima_forecast(sample_series, periods=2, auto_order=False, order=(1, 0, 1))
        assert len(forecast) == 2
        assert list(forecast.columns) == ["year", "yhat", "yhat_lower", "yhat_upper"]

    def test_different_periods(self, sample_series: pd.DataFrame) -> None:
        """Test forecast with different period lengths."""
        for periods in [1, 3, 5, 10]:
            forecast = build_arima_forecast(sample_series, periods=periods)
            assert len(forecast) == periods


class TestCompareARIMAModels:
    """Test ARIMA model comparison."""

    @pytest.fixture
    def sample_series(self) -> pd.DataFrame:
        """Create sample time series data."""
        return pd.DataFrame(
            {
                "year": list(range(2015, 2023)),
                "value": [100.0, 105.0, 103.0, 110.0, 112.0, 108.0, 115.0, 120.0],
            }
        )

    def test_compare_returns_sorted_list(self, sample_series: pd.DataFrame) -> None:
        """Test that comparison returns sorted results."""
        results = compare_arima_models(sample_series)
        assert isinstance(results, list)
        # Results should be sorted by AIC (ascending)
        if len(results) > 1:
            aics = [aic for _, aic in results]
            assert aics == sorted(aics)

    def test_compare_returns_tuples(self, sample_series: pd.DataFrame) -> None:
        """Test that each result is (order, aic) tuple."""
        results = compare_arima_models(sample_series)
        for result in results:
            assert isinstance(result, tuple)
            assert len(result) == 2
            order, aic = result
            assert isinstance(order, tuple)
            assert len(order) == 3
            assert isinstance(aic, float)

    def test_compare_with_custom_orders(self, sample_series: pd.DataFrame) -> None:
        """Test model comparison with custom orders."""
        custom_orders = [(1, 0, 1), (1, 1, 1), (2, 0, 1)]
        results = compare_arima_models(sample_series, orders=custom_orders)
        assert len(results) > 0

    def test_compare_insufficient_data(self) -> None:
        """Test comparison with insufficient data."""
        short_series = pd.DataFrame({"year": [2020, 2021], "value": [100.0, 110.0]})
        results = compare_arima_models(short_series)
        assert results == []


class TestARIMAIntegration:
    """Integration tests for ARIMA forecasting workflow."""

    def test_end_to_end_forecast_workflow(self) -> None:
        """Test complete forecasting workflow."""
        import numpy as np

        np.random.seed(42)
        # Create synthetic sales data
        series = pd.DataFrame(
            {
                "year": list(range(2015, 2023)),
                "value": np.cumsum(np.random.normal(10, 5, 8)).astype(float),
            }
        )

        # Find optimal order
        optimal_order = find_optimal_arima_order(series)
        assert isinstance(optimal_order, tuple)

        # Compare multiple models
        comparisons = compare_arima_models(series)
        assert len(comparisons) > 0

        # Build forecast with optimal order
        forecast = build_arima_forecast(
            series, periods=3, auto_order=False, order=optimal_order
        )
        assert len(forecast) == 3
        assert all(forecast["year"] > series["year"].max())

    def test_forecast_with_trend(self) -> None:
        """Test ARIMA on trending data."""
        series = pd.DataFrame(
            {
                "year": list(range(2015, 2023)),
                "value": [100 * (1.05**i) for i in range(8)],
            }
        )
        forecast = build_arima_forecast(series, periods=2)
        assert len(forecast) == 2
        # Forecast should be increasing (roughly)
        assert forecast.loc[0, "yhat"] > 0

    def test_forecast_with_seasonal_pattern(self) -> None:
        """Test ARIMA on data with seasonal-like pattern."""
        import numpy as np

        np.random.seed(42)
        years = list(range(2015, 2023))
        values = [100 + 10 * np.sin(2 * np.pi * i / 4) + np.random.normal(0, 2) for i in range(8)]
        series = pd.DataFrame({"year": years, "value": values})
        forecast = build_arima_forecast(series, periods=2)
        assert len(forecast) == 2
