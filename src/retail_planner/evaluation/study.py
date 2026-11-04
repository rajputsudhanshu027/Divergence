"""Rolling-origin model selection, untouched holdout, and a stated inventory scenario."""

from __future__ import annotations

from datetime import date, timedelta
from math import ceil
from pathlib import Path
from statistics import mean

from ..data.m5 import Dataset
from ..forecasting.baselines import METHODS, forecast
from ..forecasting.lightgbm import ModelConfig, predict_lightgbm, save_model, train_lightgbm
from .diagnostics import holdout_monitoring, profile_dataset
from .inventory import evaluate_inventory
from .metrics import quantile, score_hierarchy

HORIZON = 28


def _predictions(dataset: Dataset, origin: int, method: str) -> dict[str, list[float]]:
    return {item.id: forecast(item.sales[:origin], HORIZON, method) for item in dataset.series}


def _scaled_residuals(dataset: Dataset, origin: int, predictions: dict[str, list[float]]) -> list[float]:
    values = []
    for item in dataset.series:
        scale = max(1.0, mean(item.sales[origin - 28:origin]))
        values.extend(abs(item.sales[origin + day] - predictions[item.id][day]) / scale
                      for day in range(HORIZON))
    return values


def _total_residuals(dataset: Dataset, origin: int, predictions: dict[str, list[float]]) -> list[float]:
    values = []
    for item in dataset.series:
        scale = max(1.0, mean(item.sales[origin - 28:origin]))
        actual = sum(item.sales[origin:origin + HORIZON])
        values.append((actual - sum(predictions[item.id])) / scale)
    return values


def _coverage(dataset: Dataset, origin: int, predictions: dict[str, list[float]], radius: float) -> float:
    covered = 0
    total = 0
    for item in dataset.series:
        scale = max(1.0, mean(item.sales[origin - 28:origin]))
        for day, point in enumerate(predictions[item.id]):
            actual = item.sales[origin + day]
            covered += max(0.0, point - radius * scale) <= actual <= point + radius * scale
            total += 1
    return covered / total


def run_study(dataset: Dataset, folds: int = 3, include_ml: bool = False,
              model_config: ModelConfig | None = None,
              artifact_dir: Path | None = None) -> dict:
    if folds < 2:
        raise ValueError("Use at least two validation folds")
    holdout_origin = len(dataset.dates) - HORIZON
    origins = [holdout_origin - HORIZON * (folds - fold) for fold in range(folds)]
    if origins[0] < 56:
        raise ValueError("Not enough history for the requested folds")

    methods = (*METHODS, "lightgbm") if include_ml else METHODS
    config = model_config or ModelConfig()

    def predict(origin: int, method: str, save: bool = False) -> dict[str, list[float]]:
        if method != "lightgbm":
            return _predictions(dataset, origin, method)
        booster, codes, rows = train_lightgbm(dataset, origin, config)
        if save and artifact_dir:
            save_model(booster, codes, config, dataset.dates[origin - 1], artifact_dir, rows)
        return predict_lightgbm(dataset, origin, booster, codes)

    fold_results: dict[str, list[dict]] = {method: [] for method in methods}
    residuals: dict[str, list[float]] = {method: [] for method in methods}
    total_residuals: dict[str, list[float]] = {method: [] for method in methods}
    for origin in origins:
        for method in methods:
            predicted = predict(origin, method)
            fold_results[method].append({"start": dataset.dates[origin],
                                         **score_hierarchy(dataset, origin, predicted)})
            residuals[method].extend(_scaled_residuals(dataset, origin, predicted))
            total_residuals[method].extend(_total_residuals(dataset, origin, predicted))

    ranking = sorted(methods, key=lambda name: mean(
        fold["subset_wrmsse"] for fold in fold_results[name]))
    winner = ranking[0]
    holdout_by_method = {method: predict(holdout_origin, method) for method in methods}
    holdout_predictions = holdout_by_method[winner]
    baseline_predictions = holdout_by_method["seasonal_28"]
    radius_80 = quantile(residuals[winner], 0.8)
    radius_90 = quantile(residuals[winner], 0.9)
    cushions = {method: {str(level): quantile(total_residuals[method], level)
                         for level in (0.8, 0.9, 0.95)} for method in methods}
    winner_cushion = cushions[winner]["0.9"]
    baseline_cushion = cushions["seasonal_28"]["0.9"]

    future_origin = len(dataset.dates)
    future_by_method = {method: predict(future_origin, method, save=method == "lightgbm")
                        for method in methods}
    future = future_by_method[winner]
    last_day = date.fromisoformat(dataset.dates[-1])
    future_dates = [(last_day + timedelta(days=step + 1)).isoformat() for step in range(HORIZON)]
    series_rows = []
    for item in dataset.series:
        scale = max(1.0, mean(item.sales[-28:]))
        holdout_scale = max(1.0, mean(item.sales[holdout_origin - 28:holdout_origin]))
        series_rows.append({
            "id": item.id, "store": item.store_id, "category": item.cat_id,
            "item": item.item_id,
            "history": list(item.sales[-56:]),
            "holdout_actual": list(item.sales[holdout_origin:]),
            "holdout_predicted": holdout_predictions[item.id],
            "holdout_baseline": baseline_predictions[item.id],
            "holdout_scale": holdout_scale,
            "holdout_on_hand": ceil(7 * mean(item.sales[holdout_origin - 28:holdout_origin])),
            "forecast": future[item.id],
            "future_baseline": future_by_method["seasonal_28"][item.id],
            "future_scale": scale,
            "future_on_hand": ceil(7 * mean(item.sales[-28:])),
            "lower_80": [max(0.0, value - radius_80 * scale) for value in future[item.id]],
            "upper_80": [value + radius_80 * scale for value in future[item.id]],
            "mae": mean(abs(actual - predicted) for actual, predicted in zip(
                item.sales[holdout_origin:], holdout_predictions[item.id])),
        })
    series_rows.sort(key=lambda row: row["id"])

    return {
        "source": dataset.source,
        "series_count": len(dataset.series),
        "date_range": [dataset.dates[0], dataset.dates[-1]],
        "validation_starts": [dataset.dates[origin] for origin in origins],
        "holdout_start": dataset.dates[holdout_origin],
        "forecast_dates": future_dates,
        "selected_method": winner,
        "candidate_methods": list(methods),
        "profile": profile_dataset(dataset),
        "monitoring": holdout_monitoring(dataset, holdout_origin, holdout_predictions, radius_80),
        "validation": {method: {
            "mean_subset_wrmsse": mean(fold["subset_wrmsse"] for fold in fold_results[method]),
            "folds": fold_results[method],
        } for method in methods},
        "holdout": {
            "selected": score_hierarchy(dataset, holdout_origin, holdout_predictions),
            "seasonal_28": score_hierarchy(dataset, holdout_origin, baseline_predictions),
            "by_method": {method: score_hierarchy(dataset, holdout_origin, holdout_by_method[method])
                          for method in methods},
            "coverage_80": _coverage(dataset, holdout_origin, holdout_predictions, radius_80),
            "coverage_90": _coverage(dataset, holdout_origin, holdout_predictions, radius_90),
        },
        "inventory": {
            "selected": evaluate_inventory(dataset, holdout_origin, holdout_predictions, winner_cushion),
            "seasonal_28": evaluate_inventory(dataset, holdout_origin, baseline_predictions, baseline_cushion),
            "cushions": {"selected": cushions[winner], "seasonal_28": cushions["seasonal_28"]},
            "assumptions": {"horizon_days": HORIZON, "starting_stock_days": 7,
                            "shortage_cost_per_unit": 5, "excess_cost_per_unit": 1,
                            "cushion_percentile": 0.9},
        },
        "series": series_rows,
    }
