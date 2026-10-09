"""Three simple, honest 28-day forecasts.

All three baselines have access to history ending at the forecast origin ONLY.
They do not peek at sales during the forecast horizon.
"""
import numpy as np

METHODS = ("last_value", "seasonal_7", "mean_28")


def forecast(history: np.ndarray, horizon: int, method: str) -> np.ndarray:
    values = np.asarray(history, dtype=float)
    if horizon < 1 or len(values) < 28:
        raise ValueError("Need horizon >= 1 and at least 28 observed days")
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("History must contain nonnegative finite unit sales")
    if method == "last_value":
        return np.full(horizon, values[-1], dtype=float)
    if method == "seasonal_7":
        # Repeats the most recent complete Mon...Sun-like week.
        return np.resize(values[-7:], horizon).astype(float)
    if method == "mean_28":
        return np.full(horizon, values[-28:].mean(), dtype=float)
    raise ValueError(f"Unknown method {method!r}; choose from {METHODS}")
