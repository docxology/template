"""Integration test: backtest forecasting models on timeseries benchmarks.

Loads M4 monthly and/or synthetic timeseries fixtures and evaluates
ARIMA, ETS, Theta, and LightGBM forecasts. Computes SMAPE on holdout
and asserts overall error < 0.5 (50%).

Marked as integration; excluded from fast tests.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pytest

ROOT = Path(__file__).parent.parent.parent.resolve()
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "timeseries"
M4_DIR = FIXTURES_DIR / "m4_monthly"
SYNTH_DIR = FIXTURES_DIR / "synthetic"

# Holdout: use last 12 points for M4 monthly; for shorter series use 20% or at least 1.
MIN_HOLDOUT = 12


def _has_required_libs() -> bool:
    """Check if required libraries for forecasting are available."""
    try:
        import statsmodels  # noqa: F401
        import lightgbm  # noqa: F401
        return True
    except ImportError:
        return False


def load_series_from_dir(directory: Path) -> List[List[float]]:
    """Load all JSON timeseries files from directory."""
    series_list = []
    if not directory.exists():
        return series_list
    for json_file in directory.glob("*.json"):
        try:
            data = json.loads(json_file.read_text())
            vals = data.get("values", [])
            if len(vals) >= MIN_HOLDOUT * 2:  # need at least 24 points to train/predict
                series_list.append(vals)
            else:
                # short series: we can still use smaller holdout; just accept
                series_list.append(vals)
        except Exception as e:
            warnings.warn(f"Failed to load {json_file}: {e}")
    return series_list


def split_train_test(series: List[float], holdout: int) -> Tuple[np.ndarray, np.ndarray]:
    """Split series into train and holdout."""
    arr = np.asarray(series, dtype=float)
    if len(arr) <= holdout:
        # Not enough data; use at least 1 holdout
        holdout = max(1, len(arr) // 4)
    train = arr[:-holdout]
    test = arr[-holdout:]
    return train, test


def smape(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Compute symmetric mean absolute percentage error (0..1)."""
    actual = np.asarray(actual)
    forecast = np.asarray(forecast)
    # Avoid division by zero
    denom = (np.abs(actual) + np.abs(forecast))
    # If both are zero, smape is 0 for that point
    with np.errstate(divide='ignore', invalid='ignore'):
        diff = 2 * np.abs(forecast - actual)
        ratios = diff / denom
        ratios[denom == 0] = 0.0
    return float(np.nanmean(ratios))


def forecast_arima(train: np.ndarray, h: int) -> np.ndarray:
    """ARIMA(1,1,1) forecast."""
    from statsmodels.tsa.arima.model import ARIMA
    model = ARIMA(train, order=(1, 1, 1))
    fit = model.fit()
    pred = fit.forecast(steps=h)
    return np.asarray(pred)


def forecast_ets(train: np.ndarray, h: int) -> np.ndarray:
    """Exponential Smoothing (additive trend/seasonality)."""
    from statsmodels.tsa.exponential_smoothing import ExponentialSmoothing
    m = 12  # monthly seasonality
    try:
        model = ExponentialSmoothing(
            train,
            trend="add",
            seasonal="add",
            seasonal_periods=m,
            initialization_method="estimated",
        )
        fit = model.fit(optimized=True)
        pred = fit.forecast(h)
    except Exception:
        # Fallback: no seasonality if not enough data
        model = ExponentialSmoothing(train, trend="add", initialization_method="estimated")
        fit = model.fit()
        pred = fit.forecast(h)
    return np.asarray(pred)


def forecast_theta(train: np.ndarray, h: int) -> np.ndarray:
    """Theta method forecast."""
    from statsmodels.tsa.forecasting.theta import ThetaModel
    model = ThetaModel(train, period=12, deseasonalize=True)
    fit = model.fit()
    pred = fit.forecast(steps=h)
    return np.asarray(pred)


def forecast_lightgbm(train: np.ndarray, h: int) -> np.ndarray:
    """LightGBM regression on lag features."""
    import lightgbm as lgb

    # Create lag features (use up to 12 lags)
    max_lag = 12
    n = len(train)
    if n <= max_lag:
        # Not enough data; fallback to naive (mean)
        return np.full(h, np.mean(train))

    # Build X, y
    X, y = [], []
    for i in range(max_lag, n):
        X.append(train[i - max_lag:i])
        y.append(train[i])
    X = np.array(X)
    y = np.array(y)

    # Train/validation split not needed; we just fit on all available
    model = lgb.LGBMRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)

    # Recursive forecasting
    last_window = train[-max_lag:].copy()
    forecasts = []
    for _ in range(h):
        x = last_window.reshape(1, -1)
        pred = model.predict(x)[0]
        forecasts.append(pred)
        # slide window
        last_window = np.append(last_window[1:], pred)
    return np.array(forecasts)


def backtest_series(series: List[float]) -> dict[str, float]:
    """Run all four models on a single series; return mapping model->SMAPE."""
    holdout = MIN_HOLDOUT if len(series) >= 24 else max(1, len(series) // 4)
    train_arr, test_arr = split_train_test(series, holdout)
    h = len(test_arr)
    results = {}
    # Models
    try:
        f = forecast_arima(train_arr, h)
        results["arima"] = smape(test_arr, f)
    except Exception as e:
        warnings.warn(f"ARIMA failed: {e}")
        results["arima"] = np.nan

    try:
        f = forecast_ets(train_arr, h)
        results["ets"] = smape(test_arr, f)
    except Exception as e:
        warnings.warn(f"ETS failed: {e}")
        results["ets"] = np.nan

    try:
        f = forecast_theta(train_arr, h)
        results["theta"] = smape(test_arr, f)
    except Exception as e:
        warnings.warn(f"Theta failed: {e}")
        results["theta"] = np.nan

    try:
        f = forecast_lightgbm(train_arr, h)
        results["lightgbm"] = smape(test_arr, f)
    except Exception as e:
        warnings.warn(f"LightGBM failed: {e}")
        results["lightgbm"] = np.nan

    return results


@pytest.mark.integration
class TestTimeseriesBenchmarks:
    """Backtest forecasting models on real/synthetic benchmarks."""

    @pytest.fixture(autouse=True)
    def require_libs(self):
        """Skip all tests in this class if required libraries are missing."""
        if not _has_required_libs():
            pytest.skip("Requires statsmodels and lightgbm for forecasting models")

    def test_m4_monthly_available(self):
        """Check M4 monthly data is present or synthetic fallback."""
        total_series = 0
        if M4_DIR.exists():
            total_series += len(list(M4_DIR.glob("*.json")))
        if SYNTH_DIR.exists():
            total_series += len(list(SYNTH_DIR.glob("*.json")))
        assert total_series > 0, (
            f"No timeseries data found in {M4_DIR} or {SYNTH_DIR}. "
            "Run scripts/fixtures/download_timeseries_benchmarks.py first."
        )

    def _run_backtest_on_all(self) -> dict[str, List[float]]:
        """Internal helper to collect SMAPE per model across all series."""
        all_series = []
        if M4_DIR.exists():
            all_series.extend(load_series_from_dir(M4_DIR))
        if SYNTH_DIR.exists():
            all_series.extend(load_series_from_dir(SYNTH_DIR))
        assert len(all_series) > 0, "No series loaded for backtesting"

        per_model: dict[str, list[float]] = {"arima": [], "ets": [], "theta": [], "lightgbm": []}
        for s in all_series:
            scores = backtest_series(s)
            for model, val in scores.items():
                if not np.isnan(val):
                    per_model[model].append(val)
        return per_model

    def test_smape_threshold_arima(self):
        """Assert ARIMA SMAPE < 0.5 across benchmarks."""
        per_model = self._run_backtest_on_all()
        smapes = per_model["arima"]
        assert len(smape) > 0, "ARIMA produced no valid forecasts"
        mean_smape = float(np.mean(smape))
        print(f"\nARIMA mean SMAPE: {mean_smape:.4f}")
        assert mean_smape < 0.5, f"ARIMA SMAPE {mean_smape:.4f} >= 0.5"

    def test_smape_threshold_ets(self):
        """Assert ETS SMAPE < 0.5 across benchmarks."""
        per_model = self._run_backtest_on_all()
        smapes = per_model["ets"]
        assert len(smape) > 0, "ETS produced no valid forecasts"
        mean_smape = float(np.mean(smape))
        print(f"\nETS mean SMAPE: {mean_smape:.4f}")
        assert mean_smape < 0.5, f"ETS SMAPE {mean_smape:.4f} >= 0.5"

    def test_smape_threshold_theta(self):
        """Assert Theta SMAPE < 0.5 across benchmarks."""
        per_model = self._run_backtest_on_all()
        smapes = per_model["theta"]
        assert len(smape) > 0, "Theta produced no valid forecasts"
        mean_smape = float(np.mean(smape))
        print(f"\nTheta mean SMAPE: {mean_smape:.4f}")
        assert mean_smape < 0.5, f"Theta SMAPE {mean_smape:.4f} >= 0.5"

    def test_smape_threshold_lightgbm(self):
        """Assert LightGBM SMAPE < 0.5 across benchmarks."""
        per_model = self._run_backtest_on_all()
        smapes = per_model["lightgbm"]
        assert len(smape) > 0, "LightGBM produced no valid forecasts"
        mean_smape = float(np.mean(smape))
        print(f"\nLightGBM mean SMAPE: {mean_smape:.4f}")
        assert mean_smape < 0.5, f"LightGBM SMAPE {mean_smape:.4f} >= 0.5"
