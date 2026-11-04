"""Shared one-order inventory calculation for studies, SQL exports, and HTTP scenarios."""

from __future__ import annotations

from math import ceil
from statistics import mean

from ..data.m5 import Dataset


def order_scenario(forecast_total: float, actual_total: float, on_hand: int,
                   scale: float, cushion: float, shortage_cost: float = 5.0,
                   excess_cost: float = 1.0) -> dict[str, float]:
    if min(on_hand, scale, shortage_cost, excess_cost) < 0:
        raise ValueError("Stock, scale, and costs must be nonnegative")
    target = max(0.0, forecast_total + cushion * scale)
    order = max(0, ceil(target - on_hand))
    remaining = on_hand + order - actual_total
    shortage = max(0.0, -remaining)
    excess = max(0.0, remaining)
    return {"cost": shortage_cost * shortage + excess_cost * excess,
            "shortage_units": shortage, "excess_units": excess, "ordered_units": order}


def evaluate_inventory(dataset: Dataset, origin: int, predictions: dict[str, list[float]],
                       cushion: float, shortage_cost: float = 5.0,
                       excess_cost: float = 1.0) -> dict[str, float]:
    """One order covering 28 days, assuming seven days of starting stock."""
    shortage = excess = orders = cost = 0.0
    for item in dataset.series:
        scale = max(1.0, mean(item.sales[origin - 28:origin]))
        on_hand = ceil(7 * mean(item.sales[origin - 28:origin]))
        outcome = order_scenario(sum(predictions[item.id]),
                                 sum(item.sales[origin:origin + 28]),
                                 on_hand, scale, cushion, shortage_cost, excess_cost)
        shortage += outcome["shortage_units"]
        excess += outcome["excess_units"]
        orders += outcome["ordered_units"]
        cost += outcome["cost"]
    return {"cost": round(cost, 2), "shortage_units": round(shortage, 1),
            "excess_units": round(excess, 1), "ordered_units": round(orders, 1)}
