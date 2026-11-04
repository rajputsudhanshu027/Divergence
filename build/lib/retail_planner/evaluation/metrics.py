"""Subset hierarchy scoring. This is not the official full-dataset M5 score."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from ..data.m5 import Dataset, Series


@dataclass
class Aggregate:
    history: list[float]
    actual: list[float]
    predicted: list[float]
    weight: float = 0.0


def hierarchy_keys(item: Series) -> tuple[tuple[str, ...], ...]:
    return (
        ("total",), ("state", item.state_id), ("store", item.store_id),
        ("category", item.cat_id), ("department", item.dept_id),
        ("state_category", item.state_id, item.cat_id),
        ("state_department", item.state_id, item.dept_id),
        ("store_category", item.store_id, item.cat_id),
        ("store_department", item.store_id, item.dept_id),
        ("item", item.item_id), ("item_state", item.item_id, item.state_id),
        ("item_store", item.item_id, item.store_id),
    )


def _scale(history: list[float]) -> float:
    first = next((index for index, value in enumerate(history) if value > 0), len(history))
    active = history[first:]
    if len(active) < 2:
        return 0.0
    return sum((right - left) ** 2 for left, right in zip(active, active[1:])) / (len(active) - 1)


def score_hierarchy(dataset: Dataset, origin: int, predictions: dict[str, list[float]]) -> dict[str, float | str]:
    horizon = len(next(iter(predictions.values())))
    if origin + horizon > len(dataset.dates):
        raise ValueError("Holdout exceeds available data")
    if set(predictions) != {item.id for item in dataset.series}:
        raise ValueError("Predictions must cover every selected series")

    aggregates: dict[tuple[str, ...], Aggregate] = {}
    used_prices = 0
    missing_prices = 0
    for item in dataset.series:
        predicted = predictions[item.id]
        if len(predicted) != horizon:
            raise ValueError("Every prediction must share the horizon")
        revenue = 0.0
        priced_days = 0
        for day in range(max(0, origin - 28), origin):
            price = dataset.prices.get((item.store_id, item.item_id, dataset.weeks[day]))
            if price is not None:
                used_prices += 1
                priced_days += 1
                revenue += item.sales[day] * price
            else:
                missing_prices += 1
        if priced_days == 0:
            revenue = sum(item.sales[max(0, origin - 28):origin])
        for key in hierarchy_keys(item):
            if key not in aggregates:
                aggregates[key] = Aggregate([0.0] * origin, [0.0] * horizon, [0.0] * horizon)
            group = aggregates[key]
            for index, value in enumerate(item.sales[:origin]):
                group.history[index] += value
            for index in range(horizon):
                group.actual[index] += item.sales[origin + index]
                group.predicted[index] += predicted[index]
            group.weight += revenue

    level_scores: dict[str, float] = {}
    for level in {key[0] for key in aggregates}:
        group_scores = []
        for key, values in aggregates.items():
            if key[0] != level:
                continue
            scale = _scale(values.history)
            if scale <= 0:
                continue
            mse = sum((a - p) ** 2 for a, p in zip(values.actual, values.predicted)) / horizon
            group_scores.append((sqrt(mse / scale), values.weight))
        total_weight = sum(weight for _, weight in group_scores)
        if total_weight:
            level_scores[level] = sum(score * weight for score, weight in group_scores) / total_weight
    if not level_scores:
        raise ValueError("No active series with a nonzero training scale")

    errors = [abs(item.sales[origin + index] - predictions[item.id][index])
              for item in dataset.series for index in range(horizon)]
    actual_total = sum(sum(item.sales[origin:origin + horizon]) for item in dataset.series)
    prediction_total = sum(sum(predictions[item.id]) for item in dataset.series)
    return {
        "subset_wrmsse": sum(level_scores.values()) / len(level_scores),
        "mae": sum(errors) / len(errors),
        "wape": sum(errors) / actual_total if actual_total else 0.0,
        "bias": (prediction_total - actual_total) / actual_total if actual_total else 0.0,
        "weight_basis": ("revenue with volume fallback" if missing_prices and used_prices else
                         "revenue" if used_prices else "unit volume"),
        "levels_scored": len(level_scores),
    }


def quantile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(probability * len(ordered) + 0.999999) - 1))
    return ordered[index]
