import json

from retail_planner.data.m5 import load_m5, write_demo
from retail_planner.evaluation.monitoring import evaluate_monitoring, monitor_report
from retail_planner.evaluation.study import run_study
from retail_planner.presentation.report import write_report


def test_monitoring_writes_machine_readable_health_check(tmp_path):
    write_demo(tmp_path / "data")
    result = run_study(load_m5(tmp_path / "data"))
    write_report(result, tmp_path / "report")

    check = monitor_report(tmp_path / "report")

    assert check["status"] in {"healthy", "alert"}
    saved = json.loads((tmp_path / "report" / "monitoring_check.json").read_text())
    assert saved["thresholds"]["minimum_price_coverage"] == 0.95


def test_monitoring_flags_reference_degradation():
    reference = {
        "profile": {"last_28_price_coverage": 1.0,
                    "recent_mean_units_per_series_day": 2.0},
        "holdout": {"coverage_80": 0.8, "coverage_90": 0.9,
                    "selected": {"wape": 0.5}},
        "monitoring": {"flags": []},
    }
    current = json.loads(json.dumps(reference))
    current["holdout"]["selected"]["wape"] = 0.7
    current["profile"]["recent_mean_units_per_series_day"] = 1.0

    check = evaluate_monitoring(current, reference)

    assert check["status"] == "alert"
    assert any("WAPE deteriorated" in alert for alert in check["alerts"])
    assert any("mean demand shifted" in alert for alert in check["alerts"])
