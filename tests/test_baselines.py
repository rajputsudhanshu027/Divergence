import numpy as np
import pytest

from retail_forecasting.baselines import forecast


def test_weekly_forecast_repeats_only_last_seven_observed_values():
    history = np.arange(1, 36, dtype=float)
    expected = np.resize(history[-7:], 28)
    np.testing.assert_allclose(forecast(history, 28, "seasonal_7"), expected)


def test_last_value_and_mean_28():
    history = np.arange(1, 36, dtype=float)
    np.testing.assert_allclose(forecast(history, 28, "last_value"), 35)
    np.testing.assert_allclose(forecast(history, 28, "mean_28"), history[-28:].mean())


def test_refuses_short_history():
    with pytest.raises(ValueError):
        forecast(np.arange(20), 28, "seasonal_7")
