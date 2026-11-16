"""Forecasts use observations available at the origin and no future covariates."""

from __future__ import annotations

from statistics import mean

METHODS = ("last", "seasonal_7", "seasonal_28", "moving_average_28", "croston", "weekday_blend")


def _croston(history: tuple[float, ...] | list[float], alpha: float = 0.1) -> float:
    """Return the bias-corrected Croston/SBA rate for intermittent demand."""
    nonzero = [(index, value) for index, value in enumerate(history) if value > 0]
    if not nonzero:
        return 0.0
    demand = float(nonzero[0][1])
    interval = float(nonzero[0][0] + 1)
    previous_index = nonzero[0][0]
    for index, value in nonzero[1:]:
        demand += alpha * (float(value) - demand)
        gap = float(index - previous_index)
        interval += alpha * (gap - interval)
        previous_index = index
    return max(0.0, (1.0 - alpha / 2.0) * demand / max(1.0, interval))


def forecast(history: tuple[float, ...] | list[float], horizon: int, method: str) -> list[float]:
    if not history or horizon < 1:
        raise ValueError("Forecast needs history and a positive horizon")
    if method not in METHODS:
        raise ValueError(f"Unknown method: {method}")
    if method == "last":
        return [history[-1]] * horizon
    if method == "moving_average_28":
        if len(history) < 28:
            raise ValueError("moving_average_28 needs 28 observations")
        return [mean(history[-28:])] * horizon
    if method == "croston":
        return [_croston(history)] * horizon
    if method.startswith("seasonal_"):
        period = int(method.split("_")[1])
        if len(history) < period:
            raise ValueError(f"{method} needs {period} observations")
        tail = history[-period:]
        return [tail[step % period] for step in range(horizon)]

    if len(history) < 56:
        raise ValueError("weekday_blend needs 56 observations")
    recent = history[-28:]
    older = history[-56:-28]
    current_level = mean(recent)
    older_level = mean(older)
    trend = max(0.8, min(1.2, current_level / older_level)) if older_level else 1.0
    result = []
    for step in range(horizon):
        weekday = step % 7
        # Same weekday in the four most recent weeks. The current week has the most weight.
        values = [recent[weekday + 7 * week] for week in range(4)]
        weekday_level = sum(value * weight for value, weight in zip(values, (1, 2, 3, 4))) / 10
        result.append(max(0.0, (0.75 * weekday_level + 0.25 * current_level) * trend))
    return result

