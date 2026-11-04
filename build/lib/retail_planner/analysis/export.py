"""Turn saved forecasts into an auditable SQL and spreadsheet analysis pack."""

from __future__ import annotations

import csv
import json
import math
import sqlite3
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from ..data.provenance import environment, fingerprint
from ..evaluation.inventory import order_scenario

SQL_DIR = Path(__file__).with_name("sql")
SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE dim_series (
    series_id TEXT PRIMARY KEY, item_id TEXT NOT NULL,
    store_id TEXT NOT NULL, category TEXT NOT NULL
);
CREATE TABLE dim_date (
    sales_date TEXT PRIMARY KEY, weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    week_start TEXT NOT NULL, period TEXT NOT NULL
);
CREATE TABLE fact_sales (
    series_id TEXT REFERENCES dim_series, sales_date TEXT REFERENCES dim_date,
    units REAL NOT NULL CHECK (units >= 0), PRIMARY KEY (series_id, sales_date)
);
CREATE TABLE fact_forecast (
    series_id TEXT REFERENCES dim_series, forecast_date TEXT REFERENCES dim_date,
    period TEXT NOT NULL CHECK (period IN ('holdout', 'future')),
    forecast_kind TEXT NOT NULL CHECK (forecast_kind IN ('selected', 'seasonal_28')),
    method TEXT NOT NULL, units REAL NOT NULL CHECK (units >= 0),
    lower_80 REAL, upper_80 REAL,
    PRIMARY KEY (series_id, forecast_date, forecast_kind)
);
CREATE TABLE model_evaluation (
    method TEXT PRIMARY KEY, selected INTEGER NOT NULL,
    validation_wrmsse REAL NOT NULL, holdout_wrmsse REAL NOT NULL, holdout_wape REAL NOT NULL
);
CREATE TABLE fact_inventory (
    series_id TEXT PRIMARY KEY REFERENCES dim_series,
    future_order_units INTEGER NOT NULL, future_on_hand_assumed INTEGER NOT NULL,
    holdout_actual_units REAL NOT NULL, holdout_selected_cost REAL NOT NULL,
    holdout_baseline_cost REAL NOT NULL
);
CREATE INDEX sales_by_date ON fact_sales(sales_date);
CREATE INDEX forecasts_by_period ON fact_forecast(period, forecast_kind);
"""


def validate_result(result: dict) -> dict:
    """Fail before export when joins, units or date alignment would be misleading."""
    rows = result["series"]
    if not rows or len(rows) != result["series_count"]:
        raise ValueError("Series count is empty or inconsistent")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate series IDs would multiply SQL joins")
    last = date.fromisoformat(result["date_range"][1])
    expected = [(last + timedelta(days=step)).isoformat() for step in range(1, 29)]
    if result["forecast_dates"] != expected:
        raise ValueError("Forecast dates must be the consecutive 28 days after history")
    if result["holdout_start"] != (last - timedelta(days=27)).isoformat():
        raise ValueError("Holdout dates do not align with observed history")
    arrays = {"history": 56, "holdout_actual": 28, "holdout_predicted": 28,
              "holdout_baseline": 28, "forecast": 28, "future_baseline": 28,
              "lower_80": 28, "upper_80": 28}
    for row in rows:
        for field, size in arrays.items():
            values = row[field]
            if len(values) != size or any(
                not math.isfinite(value) or value < 0 for value in values
            ):
                raise ValueError(f"{row['id']}: invalid {field} length or sales values")
        if row["history"][-28:] != row["holdout_actual"]:
            raise ValueError(f"{row['id']}: holdout actuals disagree with history")
        if any(not low <= point <= high for low, point, high in zip(
            row["lower_80"], row["forecast"], row["upper_80"]
        )):
            raise ValueError(f"{row['id']}: forecast lies outside its interval")
    return {"status": "passed", "unique_series": len(rows),
            "observed_item_days": 56 * len(rows),
            "holdout_item_days": 28 * len(rows),
            "checks": ["unique IDs", "date alignment", "finite nonnegative units",
                       "array lengths", "holdout/history agreement", "interval ordering"]}


def _populate(connection: sqlite3.Connection, result: dict) -> None:
    connection.executescript(SCHEMA)
    last = date.fromisoformat(result["date_range"][1])
    observed = [(last - timedelta(days=55 - step)).isoformat() for step in range(56)]
    for text in observed + result["forecast_dates"]:
        day = date.fromisoformat(text)
        period = "future" if day > last else (
            "holdout" if text >= result["holdout_start"] else "pre_holdout")
        connection.execute("INSERT INTO dim_date VALUES (?, ?, ?, ?)", (
            text, day.weekday(), (day - timedelta(days=day.weekday())).isoformat(), period))
    for row in result["series"]:
        key = row["id"]
        connection.execute("INSERT INTO dim_series VALUES (?, ?, ?, ?)",
                           (key, row["item"], row["store"], row["category"]))
        connection.executemany("INSERT INTO fact_sales VALUES (?, ?, ?)",
                               [(key, day, units) for day, units in zip(observed, row["history"])])
        for period, days, selected, baseline in (
            ("holdout", observed[-28:], row["holdout_predicted"], row["holdout_baseline"]),
            ("future", result["forecast_dates"], row["forecast"], row["future_baseline"]),
        ):
            for kind, method, values in (
                ("selected", result["selected_method"], selected),
                ("seasonal_28", "seasonal_28", baseline),
            ):
                connection.executemany("INSERT INTO fact_forecast VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [(key, day, period, kind, method, value,
                      row["lower_80"][index] if period == "future" and kind == "selected" else None,
                      row["upper_80"][index] if period == "future" and kind == "selected" else None)
                     for index, (day, value) in enumerate(zip(days, values))])
        costs = []
        actual = sum(row["holdout_actual"])
        assumptions = result["inventory"]["assumptions"]
        level = str(assumptions["cushion_percentile"])
        for kind, values in (("selected", row["holdout_predicted"]),
                             ("seasonal_28", row["holdout_baseline"])):
            costs.append(order_scenario(sum(values), actual, row["holdout_on_hand"],
                row["holdout_scale"], result["inventory"]["cushions"][kind][level],
                assumptions["shortage_cost_per_unit"], assumptions["excess_cost_per_unit"])["cost"])
        target = sum(row["forecast"]) + \
            result["inventory"]["cushions"]["selected"][level] * row["future_scale"]
        future_order = max(0, math.ceil(max(0.0, target) - row["future_on_hand"]))
        connection.execute("INSERT INTO fact_inventory VALUES (?, ?, ?, ?, ?, ?)",
                           (key, future_order, row["future_on_hand"], actual, *costs))
    for method, validation in result["validation"].items():
        holdout = result["holdout"]["by_method"][method]
        connection.execute("INSERT INTO model_evaluation VALUES (?, ?, ?, ?, ?)", (
            method, int(method == result["selected_method"]), validation["mean_subset_wrmsse"],
            holdout["subset_wrmsse"], holdout["wape"]))
    connection.commit()


def _markdown_table(rows: list[dict], columns: tuple[str, ...], limit: int = 10) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows[:limit]:
        def display(value):
            if value is None:
                return "undefined"
            return f"{value:.4f}" if isinstance(value, float) else str(value).replace("|", "\\|")
        lines.append("| " + " | ".join(display(row[name]) for name in columns) + " |")
    return "\n".join(lines)


def _case_study(result: dict, tables: dict, quality: dict) -> str:
    selected = result["holdout"]["selected"]
    baseline = result["holdout"]["seasonal_28"]
    improvement = (1 - selected["subset_wrmsse"] / baseline["subset_wrmsse"]) \
        if baseline["subset_wrmsse"] else None
    cost = result["inventory"]["selected"]["cost"]
    baseline_cost = result["inventory"]["seasonal_28"]["cost"]
    improvement_text = f"{improvement:.1%}" if improvement is not None else "undefined (zero baseline)"
    weakest = next((row for row in tables["store_performance"] if row["wape"] is not None), None)
    recommendation = (f"Review **{weakest['store_id']}**, the store with the largest holdout WAPE "
                      f"({weakest['wape']:.1%}). Inspect high-error items before changing stock policy."
                      if weakest else "No store has a defined WAPE; investigate zero-demand segments.")
    synthetic = "synthetic" in result["source"].lower()
    return f"""# Retail demand: analyst case study

## Business question

Which stores and products need a closer stock review, and does a demand forecast improve a simple order scenario?

## Data and scope

- Source: **{result['source']}**. {"Synthetic workflow demonstration; no real retail conclusions." if synthetic else "Public historical retail data; a sampled study, not a live store deployment."}
- {result['series_count']:,} item-store histories; full study dates {result['date_range'][0]} to {result['date_range'][1]}.
- Full-study zero-sales share: {result['profile']['zero_demand_share']:.1%}.
- SQL mart: only the **last 56 observed days**, the **28-day historical holdout predictions**, and **28 future forecast days**. It is not the complete raw dataset.
- Future means dates after this historical dataset's cutoff, not forecasts for today's stores.

## Approach

Validate the exported records, build a SQLite star schema, join actuals to forecasts at item-store-day grain, and compare stores, categories, weekdays, and complete weeks. Choose a forecasting method using rolling validation before examining the holdout.

## Findings

- Selected method: **{result['selected_method']}**.
- Holdout subset hierarchy WRMSSE: **{selected['subset_wrmsse']:.3f}**, versus **{baseline['subset_wrmsse']:.3f}** for the 28-day repeat; relative reduction **{improvement_text}**.
- Holdout WAPE: **{selected['wape']:.1%}**. Lower error than a baseline still leaves substantial uncertainty.
- Simulated order cost: **{cost:,.0f}** versus **{baseline_cost:,.0f}** in arbitrary cost units.
- Observed 80% / 90% interval coverage: **{result['holdout']['coverage_80']:.1%} / {result['holdout']['coverage_90']:.1%}**.

### Method comparison

{_markdown_table(tables['model_comparison'], ('method', 'validation_wrmsse', 'holdout_wrmsse', 'selected'))}

### Store review

WAPE and bias below are decimal ratios. Positive bias means overforecasting. Undefined WAPE means zero observed demand.

{_markdown_table(tables['store_performance'], ('store_id', 'series_count', 'actual_units', 'wape', 'bias'))}

### Category comparison

{_markdown_table(tables['category_performance'], ('category', 'actual_units', 'selected_wape', 'baseline_wape', 'selected_bias'))}

### Largest item errors

{_markdown_table(tables['error_review'], ('series_id', 'actual_units', 'predicted_units', 'absolute_error_units'), 5)}

## Recommended next action

{recommendation} Compare the sign of bias and the costs of shortages and leftovers. Validate the assumptions in a staged pilot with lead times and real inventory before approving an order rule. SQL identifies review candidates; it cannot establish why a store is difficult to forecast.

## Quality and reproducibility

{quality['observed_item_days']:,} observed item-days passed checks for unique IDs, aligned dates, finite nonnegative sales, matching holdout/history values, and ordered interval bounds. Primary keys and foreign keys protect joins. See `export_manifest.json` for result and SQL checksums, row counts, and the environment observed when exporting.

## Limits

These scores cover a subset and cannot be compared with the official M5 leaderboard. Zero sales may reflect low demand or unavailable stock; the data cannot distinguish them. Inventory costs are a one-order simulation, not revenue or measured savings. The SQL mart's 56-day trends cannot establish annual seasonality. Forecast intervals are pooled and do not guarantee item-level service. Export-time metadata does not reconstruct the original training environment.
"""


def build_analytics(report_dir: Path, output_dir: Path) -> dict:
    """Build local SQLite plus small, shareable CSVs without retraining a model."""
    report_dir, output_dir = Path(report_dir), Path(output_dir)
    result_path = report_dir / "results.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    quality = validate_result(result)
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = {}
    with tempfile.TemporaryDirectory(dir=report_dir) as temporary:
        database = Path(temporary) / "analysis.sqlite"
        with sqlite3.connect(database) as connection:
            connection.row_factory = sqlite3.Row
            _populate(connection, result)
            for query in sorted(SQL_DIR.glob("*.sql")):
                cursor = connection.execute(query.read_text(encoding="utf-8"))
                headers = [field[0] for field in cursor.description]
                rows = [dict(row) for row in cursor]
                tables[query.stem] = rows
                with (output_dir / f"{query.stem}.csv").open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(rows)
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("SQL mart failed foreign key checks")
        database.replace(report_dir / "analysis.sqlite")
    (output_dir / "case_study.md").write_text(_case_study(result, tables, quality), encoding="utf-8")
    summary = {key: result[key] for key in (
        "source", "series_count", "date_range", "holdout_start", "selected_method",
        "profile", "validation", "holdout", "monitoring", "inventory")}
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1, "kind": "analysis_export_from_saved_results",
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment_observed_at_export": environment(),
        "original_run_manifest_available": (report_dir / "run_manifest.json").is_file(),
        "source_results": fingerprint(result_path), "quality": quality,
        "sql": {path.name: fingerprint(path) for path in sorted(SQL_DIR.glob("*.sql"))},
        "csv_rows": {name: len(rows) for name, rows in tables.items()},
        "outputs": {name: fingerprint(output_dir / name) for name in (
            "case_study.md", "summary.json", *(f"{name}.csv" for name in tables))},
        "database": fingerprint(report_dir / "analysis.sqlite"),
    }
    (output_dir / "export_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
