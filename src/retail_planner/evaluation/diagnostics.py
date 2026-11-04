"""Dataset profiles and holdout diagnostics by store and category."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from ..data.m5 import Dataset


def profile_dataset(dataset: Dataset) -> dict:
    last = len(dataset.dates)
    total_observations = len(dataset.series) * last
    zero_observations = sum(value == 0 for item in dataset.series for value in item.sales)
    priced = 0
    possible = len(dataset.series) * 28
    for item in dataset.series:
        for day in range(last - 28, last):
            priced += (item.store_id, item.item_id, dataset.weeks[day]) in dataset.prices
    return {
        "series": len(dataset.series), "days": last,
        "zero_demand_share": zero_observations / total_observations,
        "last_28_price_coverage": priced / possible,
        "stores": dict(sorted(Counter(item.store_id for item in dataset.series).items())),
        "categories": dict(sorted(Counter(item.cat_id for item in dataset.series).items())),
        "recent_mean_units_per_series_day": mean(
            mean(item.sales[-28:]) for item in dataset.series),
    }


def holdout_monitoring(dataset: Dataset, origin: int, predictions: dict[str, list[float]],
                       radius_80: float) -> dict:
    groups: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"series": 0, "actual": 0, "predicted": 0, "absolute_error": 0,
                 "covered": 0, "observations": 0, "recent_demand": 0, "previous_demand": 0})
    for item in dataset.series:
        scale = max(1.0, mean(item.sales[origin - 28:origin]))
        for key in (("store", item.store_id), ("category", item.cat_id)):
            group = groups[key]
            group["series"] += 1
            group["recent_demand"] += sum(item.sales[origin - 28:origin])
            group["previous_demand"] += sum(item.sales[origin - 56:origin - 28])
            for actual, point in zip(item.sales[origin:origin + 28], predictions[item.id]):
                group["actual"] += actual
                group["predicted"] += point
                group["absolute_error"] += abs(actual - point)
                group["covered"] += max(0.0, point - radius_80 * scale) <= actual <= point + radius_80 * scale
                group["observations"] += 1
    segments = []
    for (level, name), values in sorted(groups.items()):
        actual = values["actual"]
        segments.append({
            "level": level, "name": name, "series": int(values["series"]),
            "wape": values["absolute_error"] / actual if actual else None,
            "bias": (values["predicted"] - actual) / actual if actual else None,
            "coverage_80": values["covered"] / values["observations"],
            "recent_vs_previous_28": (values["recent_demand"] / values["previous_demand"] - 1)
            if values["previous_demand"] else None,
        })
    flags = []
    for row in segments:
        if row["bias"] is not None and abs(row["bias"]) > 0.1:
            flags.append(f"{row['level']} {row['name']}: holdout bias exceeds 10%")
        if row["coverage_80"] < 0.7:
            flags.append(f"{row['level']} {row['name']}: 80% interval coverage below 70%")
    return {"segments": segments, "flags": flags,
            "rules": {"absolute_bias": 0.1, "minimum_80_coverage": 0.7}}
