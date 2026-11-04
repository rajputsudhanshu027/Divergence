import csv
import json
import sqlite3

import pytest

from retail_planner.analysis.export import build_analytics, validate_result
from retail_planner.data.m5 import load_m5, write_demo
from retail_planner.data.provenance import fingerprint, write_run_manifest
from retail_planner.evaluation.study import run_study
from retail_planner.presentation.report import write_report


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    root = tmp_path_factory.mktemp("analyst")
    write_demo(root / "data")
    result = run_study(load_m5(root / "data"))
    result["source"] = "synthetic demonstration"
    write_report(result, root / "report")
    return root, result


def test_sql_metrics_reconcile_to_evaluation_and_simulated_costs(report, tmp_path):
    root, result = report
    manifest = build_analytics(root / "report", tmp_path)
    with sqlite3.connect(root / "report" / "analysis.sqlite") as connection:
        actual, error = connection.execute("""
            SELECT SUM(s.units), SUM(ABS(s.units - f.units))
            FROM fact_sales s JOIN fact_forecast f
              ON s.series_id = f.series_id AND s.sales_date = f.forecast_date
            WHERE f.period = 'holdout' AND f.forecast_kind = 'selected'
        """).fetchone()
        assert error / actual == pytest.approx(result["holdout"]["selected"]["wape"])
        costs = connection.execute(
            "SELECT SUM(holdout_selected_cost), SUM(holdout_baseline_cost) FROM fact_inventory"
        ).fetchone()
        assert costs[0] == pytest.approx(result["inventory"]["selected"]["cost"], abs=0.01)
        assert costs[1] == pytest.approx(result["inventory"]["seasonal_28"]["cost"], abs=0.01)
        assert not connection.execute("PRAGMA foreign_key_check").fetchall()
        assert connection.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0] == 24 * 56
        assert connection.execute("SELECT COUNT(*) FROM fact_forecast").fetchone()[0] == 24 * 112
    assert manifest["quality"]["status"] == "passed"
    assert manifest["source_results"] == fingerprint(root / "report" / "results.json")
    assert set(manifest["csv_rows"]) == {
        "store_performance", "category_performance", "weekly_demand", "weekday_demand",
        "model_comparison", "error_review", "inventory_review",
    }
    assert "Synthetic workflow demonstration" in (tmp_path / "case_study.md").read_text()
    assert not manifest["original_run_manifest_available"]


def test_sql_uses_null_for_zero_demand_and_keeps_methods_separate(report, tmp_path):
    root, original = report
    result = json.loads(json.dumps(original))
    row = result["series"][0]
    row["history"] = [0.0] * 56
    row["holdout_actual"] = [0.0] * 28
    zero_report = tmp_path / "zero"
    write_report(result, zero_report)
    build_analytics(zero_report, tmp_path / "exports")
    with sqlite3.connect(zero_report / "analysis.sqlite") as connection:
        rows = connection.execute("""
            SELECT forecast_kind, COUNT(*) FROM fact_forecast
            WHERE series_id = ? GROUP BY forecast_kind
        """, (row["id"],)).fetchall()
        assert dict(rows) == {"seasonal_28": 56, "selected": 56}
    with (tmp_path / "exports" / "error_review.csv").open() as handle:
        exported = next(item for item in csv.DictReader(handle) if item["series_id"] == row["id"])
    assert exported["wape"] == ""


@pytest.mark.parametrize("damage, message", [
    ("duplicate", "Duplicate series"),
    ("negative", "invalid history"),
    ("nan", "invalid history"),
    ("dates", "Forecast dates"),
    ("history", "disagree with history"),
    ("interval", "outside its interval"),
])
def test_corrupt_records_are_rejected_before_export(report, damage, message):
    _, original = report
    result = json.loads(json.dumps(original))
    row = result["series"][0]
    if damage == "duplicate":
        result["series"][1]["id"] = row["id"]
    elif damage == "negative":
        row["history"][0] = -1
    elif damage == "nan":
        row["history"][0] = float("nan")
    elif damage == "dates":
        result["forecast_dates"][0] = "1900-01-01"
    elif damage == "history":
        row["holdout_actual"][0] += 1
    else:
        row["upper_80"][0] = 0
        row["forecast"][0] = 100
    with pytest.raises(ValueError, match=message):
        validate_result(result)


def test_weekly_comparison_drops_partial_weeks(report, tmp_path):
    root, _ = report
    build_analytics(root / "report", tmp_path)
    with (tmp_path / "weekly_demand.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert rows and all(row["days_observed"] == "7" for row in rows)
    for store in {row["store_id"] for row in rows}:
        first = next(row for row in rows if row["store_id"] == store)
        assert first["previous_week_units"] == ""
        assert first["wow_change"] == ""


def test_new_run_manifest_hashes_inputs_and_records_options(report):
    root, _ = report
    write_run_manifest(root / "data", root / "report", {"mode": "demo", "output_dir": root / "report"})
    manifest = json.loads((root / "report" / "run_manifest.json").read_text())
    assert manifest["kind"] == "recorded_at_run_completion"
    assert manifest["inputs"]["calendar.csv"] == fingerprint(root / "data" / "calendar.csv")
    assert manifest["options"]["output_dir"] == str(root / "report")
    assert manifest["results"] == fingerprint(root / "report" / "results.json")
