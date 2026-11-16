"""Evaluate saved-study health against explicit investigation thresholds."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def evaluate_monitoring(current: dict, reference: dict | None = None) -> dict:
    alerts = list(current.get("monitoring", {}).get("flags", []))
    profile = current["profile"]
    holdout = current["holdout"]
    price_coverage = profile.get("last_28_price_coverage", 0.0)
    if price_coverage < 0.95:
        alerts.append(f"recent price coverage {price_coverage:.1%} is below 95%")
    for level in (80, 90):
        observed = holdout[f"coverage_{level}"]
        target = level / 100
        if abs(observed - target) > 0.05:
            alerts.append(
                f"{level}% interval coverage {observed:.1%} is outside target ±5 percentage points")

    comparisons = {}
    if reference is not None:
        current_wape = holdout["selected"]["wape"]
        reference_wape = reference["holdout"]["selected"]["wape"]
        relative_change = current_wape / reference_wape - 1 if reference_wape else 0.0
        comparisons["holdout_wape_relative_change"] = relative_change
        if relative_change > 0.15:
            alerts.append(f"holdout WAPE deteriorated {relative_change:.1%} versus reference")
        current_demand = profile["recent_mean_units_per_series_day"]
        reference_demand = reference["profile"]["recent_mean_units_per_series_day"]
        demand_change = current_demand / reference_demand - 1 if reference_demand else 0.0
        comparisons["recent_demand_relative_change"] = demand_change
        if abs(demand_change) > 0.25:
            alerts.append(f"recent mean demand shifted {demand_change:.1%} versus reference")

    return {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "alert" if alerts else "healthy",
        "alerts": sorted(set(alerts)),
        "comparisons": comparisons,
        "thresholds": {
            "minimum_price_coverage": 0.95,
            "interval_coverage_tolerance": 0.05,
            "maximum_wape_deterioration": 0.15,
            "maximum_absolute_demand_shift": 0.25,
        },
    }


def monitor_report(report_dir: Path, reference_dir: Path | None = None) -> dict:
    current_path = report_dir / "results.json"
    if not current_path.is_file():
        raise FileNotFoundError(f"No report at {current_path}; run a study first")
    current = json.loads(current_path.read_text(encoding="utf-8"))
    reference = None
    if reference_dir is not None:
        reference_path = reference_dir / "results.json"
        if not reference_path.is_file():
            raise FileNotFoundError(f"No reference report at {reference_path}")
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
    check = evaluate_monitoring(current, reference)
    (report_dir / "monitoring_check.json").write_text(
        json.dumps(check, indent=2) + "\n", encoding="utf-8")
    return check
