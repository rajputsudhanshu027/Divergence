"""Expanding-window time-series backtesting with an untouched final holdout."""

import numpy as np
import pandas as pd

from retail_forecasting.baselines import METHODS, forecast


def origins_for_backtest(
    last_day: int, horizon: int = 28, folds: int = 3
) -> list[int]:
    """Return historical cutoff days; last horizon is reserved for final testing.

    M5 validation data ends d_1913: with 3 folds at 28 days, the
    origins are 1801, 1829, 1857; d_1886..d_1913 is never scored here.
    """
    if horizon < 1 or folds < 1:
        raise ValueError("horizon and folds must be positive")
    return [last_day - horizon * (folds + 1 - k) for k in range(folds)]


def evaluate_baselines(
    daily: pd.DataFrame, horizon: int = 28, folds: int = 3
) -> pd.DataFrame:
    needed = {"id", "item_id", "store_id", "day_index", "sales", "date"}
    if not needed.issubset(daily.columns):
        raise ValueError(f"daily table missing columns {sorted(needed - set(daily.columns))}")
    last_day = int(daily["day_index"].max())
    origins = origins_for_backtest(last_day, horizon=horizon, folds=folds)
    predictions = []
    for item_id, group in daily.groupby("id", sort=False):
        group = group.sort_values("day_index")
        if group["day_index"].duplicated().any():
            raise ValueError(f"Duplicate dates in series {item_id}")
        for fold_idx, origin in enumerate(origins, start=1):
            history = group.loc[group["day_index"] <= origin]
            actual = group.loc[
                group["day_index"].between(origin + 1, origin + horizon)
            ].sort_values("day_index")
            # Keep this strict: silently accepting missing days corrupts weekly repeats.
            if len(history) < 28 or len(actual) != horizon:
                raise ValueError(f"Incomplete history or validation for {item_id}")
            if not np.array_equal(
                history["day_index"].tail(28).to_numpy(),
                np.arange(origin - 27, origin + 1),
            ):
                raise ValueError(f"History has gaps for series {item_id}")
            if not np.array_equal(
                actual["day_index"].to_numpy(),
                np.arange(origin + 1, origin + horizon + 1),
            ):
                raise ValueError(f"Validation has gaps for series {item_id}")
            for method in METHODS:
                predicted = forecast(history["sales"].to_numpy(), horizon, method)
                for (_, row), pred in zip(actual.iterrows(), predicted):
                    predictions.append({
                        "id": item_id,
                        "item_id": row["item_id"],
                        "store_id": row["store_id"],
                        "fold": fold_idx,
                        "origin_day": origin,
                        "day_index": int(row["day_index"]),
                        "date": row["date"],
                        "method": method,
                        "actual": float(row["sales"]),
                        "predicted": float(pred),
                    })
    return pd.DataFrame(predictions)
