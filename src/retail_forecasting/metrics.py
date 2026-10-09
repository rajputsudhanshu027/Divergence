"""Simple unit-sales forecast metrics; not the official M5 WRMSSE."""

import numpy as np
import pandas as pd


def score(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (method, fold), group in predictions.groupby(["method", "fold"]):
        actual = group["actual"].to_numpy(dtype=float)
        predicted = group["predicted"].to_numpy(dtype=float)
        diff = actual - predicted
        denominator = np.abs(actual).sum()
        rows.append({
            "method": method,
            "fold": int(fold),
            "MAE": np.abs(diff).mean(),
            "RMSE": np.sqrt(np.square(diff).mean()),
            "WAPE_pct": 100 * np.abs(diff).sum() / denominator if denominator > 0 else np.nan,
        })
    return pd.DataFrame(rows).sort_values(["method", "fold"], ignore_index=True)


def average_folds(scores: pd.DataFrame) -> pd.DataFrame:
    return scores.groupby("method", as_index=False)[["MAE", "RMSE", "WAPE_pct"]].mean().sort_values("MAE")
