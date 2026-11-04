"""Write a portable analyst report and concise machine-readable artifacts."""

from __future__ import annotations

import json
from pathlib import Path


def write_report(result: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (directory / "monitoring.json").write_text(
        json.dumps(result["monitoring"], indent=2), encoding="utf-8")
    payload = json.dumps(result, separators=(",", ":")).replace("</", "<\\/")
    template = (Path(__file__).parent / "templates" / "dashboard.html").read_text(encoding="utf-8")
    (directory / "index.html").write_text(
        template.replace("__REPORT_DATA__", payload), encoding="utf-8")
    (directory / "model_card.md").write_text(_model_card(result), encoding="utf-8")


def _model_card(result: dict) -> str:
    selected = result["holdout"]["selected"]
    baseline = result["holdout"]["seasonal_28"]
    cost = result["inventory"]["selected"]["cost"]
    baseline_cost = result["inventory"]["seasonal_28"]["cost"]
    source = result["source"]
    return f"""# Model card: {result['selected_method']}

## Intended use

Compare 28-day item-store demand forecasts and explore a one-order replenishment scenario. The report supports analysis; it does not place orders or represent actual stock levels.

## Data and evaluation

- Source: {source}
- Item-store series: {result['series_count']}
- Sales dates: {result['date_range'][0]} through {result['date_range'][1]}
- Validation starts: {', '.join(result['validation_starts'])}
- Final untouched holdout starts: {result['holdout_start']}
- Selection rule: lowest mean subset hierarchy WRMSSE over validation folds.
- Sales features end before each forecast origin. Known calendar fields are available for the forecast dates; price features use only previously observed prices.

## Measured results

| Measure | Selected method | Seasonal 28-day baseline |
|---|---:|---:|
| Holdout subset WRMSSE | {selected['subset_wrmsse']:.3f} | {baseline['subset_wrmsse']:.3f} |
| Holdout WAPE | {selected['wape']:.1%} | {baseline['wape']:.1%} |
| Simulated order cost | {cost:.0f} | {baseline_cost:.0f} |

The selected method's 80% and 90% interval coverage on the holdout were {result['holdout']['coverage_80']:.1%} and {result['holdout']['coverage_90']:.1%}. Intervals are pooled, scaled absolute residual quantiles from validation folds, not item-specific probabilistic models.

## Limits and checks

This is a {result['series_count']}-series subset analysis. Its hierarchy score cannot be compared with an official M5 competition score. The inventory result assumes immediate delivery, one 28-day order, seven days of starting stock, a shortage cost of 5, and a leftover cost of 1; M5 has no observed inventory record for validating savings. Monitor store and category bias, error, and interval coverage in `monitoring.json`. Re-run on more series and more dates before any operational use.
"""
