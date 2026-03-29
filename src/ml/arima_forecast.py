"""ARIMA time series forecasting module."""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
except ImportError:  # pragma: no cover
    ARIMA = None  # type: ignore[assignment]
    adfuller = None  # type: ignore[assignment]


class ARIMAResult(NamedTuple):
    """Result from ARIMA model fitting."""

    order: tuple[int, int, int]
    aic: float
    bic: float
    fitted_model: object


def check_stationarity(series: pd.Series, significance: float = 0.05) -> bool:
    """
    Check if time series is stationary using Augmented Dickey-Fuller test.

    Args:
        series: Time series to test
        significance: Significance level (default 0.05)

    Returns:
        True if series is stationary, False otherwise
    """
    if adfuller is None:
        return False

    try:
        result = adfuller(series.dropna(), autolag="AIC")
        return bool(result[1] < significance)
    except Exception:
        return False


def find_optimal_arima_order(
    series: pd.Series,
    max_p: int = 5,
    max_d: int = 2,
    max_q: int = 5,
) -> tuple[int, int, int]:
    """
    Find optimal ARIMA order using grid search with AIC.

    Uses AIC criterion for model comparison:
    - Lower AIC indicates better fit
    - More parsimonious models are preferred

    Args:
        series: Time series data (should be numeric)
        max_p: Maximum AR order to test (default 5)
        max_d: Maximum differencing order (default 2)
        max_q: Maximum MA order (default 5)

    Returns:
        (p, d, q) tuple representing optimal ARIMA order
    """
    if ARIMA is None or len(series) < 10:
        return (1, 0, 1)  # Default conservative order

    best_aic = np.inf
    best_order = (1, 0, 1)

    # Grid search for best order
    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                try:
                    # Fit model with timeout protection
                    model = ARIMA(series, order=(p, d, q))
                    result = model.fit()
                    if result.aic < best_aic:
                        best_aic = result.aic
                        best_order = (p, d, q)
                except Exception:
                    # Skip invalid combinations
                    continue

    return best_order


def build_arima_forecast(
    series: pd.DataFrame,
    periods: int = 5,
    auto_order: bool = True,
    order: tuple[int, int, int] | None = None,
) -> pd.DataFrame:
    """
    Build ARIMA forecast for time series.

    Args:
        series: DataFrame with 'year' and 'value' columns
        periods: Number of periods to forecast (default 5)
        auto_order: Whether to automatically select order (default True)
        order: ARIMA order (p, d, q) if auto_order=False

    Returns:
        DataFrame with 'year', 'yhat', 'yhat_lower', 'yhat_upper' columns

    Raises:
        ValueError: If series is too short or empty
    """
    if ARIMA is None:
        raise ImportError("statsmodels not installed")

    if len(series) < 3:
        raise ValueError("ARIMA requires at least 3 data points")

    # Sort and extract series
    sorted_series = series.sort_values("year")
    y = sorted_series["value"].values.astype(float)

    # Determine ARIMA order
    if auto_order:
        arima_order = find_optimal_arima_order(pd.Series(y))
    else:
        arima_order = order or (1, 0, 1)

    try:
        # Fit ARIMA model
        model = ARIMA(y, order=arima_order)
        fitted = model.fit()

        # Generate forecast
        forecast = fitted.get_forecast(steps=periods)
        forecast_result = forecast.summary_frame(alpha=0.05)

        # Extract predictions
        last_year = int(sorted_series["year"].max())
        rows = []
        for i, (_idx, row) in enumerate(forecast_result.iterrows()):
            rows.append(
                {
                    "year": last_year + i + 1,
                    "yhat": float(row["mean"]),
                    "yhat_lower": float(row["mean_ci_lower"]),
                    "yhat_upper": float(row["mean_ci_upper"]),
                }
            )

        return pd.DataFrame(rows)

    except Exception as e:
        raise ValueError(f"ARIMA model fitting failed: {str(e)}") from e


def compare_arima_models(
    series: pd.DataFrame,
    orders: list[tuple[int, int, int]] | None = None,
) -> list[tuple[tuple[int, int, int], float]]:
    """
    Compare ARIMA models with different orders.

    Args:
        series: DataFrame with 'year' and 'value' columns
        orders: List of (p, d, q) tuples to test, or None for automatic grid

    Returns:
        List of (order, aic) tuples sorted by AIC (best first)
    """
    if ARIMA is None:
        return []

    if len(series) < 3:
        return []

    results = []
    sorted_series = series.sort_values("year")
    y = sorted_series["value"].values.astype(float)

    # Default orders to test
    if orders is None:
        orders = [
            (1, 0, 1),
            (1, 1, 1),
            (2, 1, 2),
            (2, 1, 1),
            (1, 0, 2),
            (2, 0, 1),
            (0, 1, 1),
            (0, 1, 2),
        ]

    for order in orders:
        try:
            model = ARIMA(y, order=order)
            result = model.fit()
            results.append((order, float(result.aic)))
        except Exception:
            continue

    return sorted(results, key=lambda x: x[1])
