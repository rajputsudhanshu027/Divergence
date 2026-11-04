import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from retail_planner.data.m5 import Dataset, Series, load_m5, write_demo
from retail_planner.evaluation.study import run_study
from retail_planner.forecasting.lightgbm import ModelConfig, _codes, feature_row, training_origins
from retail_planner.forecasting.lightgbm import predict_lightgbm, save_model, train_lightgbm
from retail_planner.presentation.api import create_app
from retail_planner.presentation.report import write_dashboard, write_report


def _changed_holdout(dataset):
    series = tuple(
        Series(item.id, item.item_id, item.dept_id, item.cat_id,
               item.store_id, item.state_id,
               item.sales[:-28] + tuple(value + 3 for value in item.sales[-28:]))
        for item in dataset.series
    )
    return Dataset(series, dataset.dates, dataset.weeks, dataset.prices,
                   dataset.source, dataset.calendar)


def test_model_features_and_training_windows_cannot_see_holdout():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        write_demo(path)
        original = load_m5(path)
        assert len(original.calendar) == len(original.dates) + 28
        altered = _changed_holdout(original)
        origin = len(original.dates) - 28
        config = ModelConfig(train_days=70, stride_days=14, rounds=20, threads=2)
        assert max(training_origins(origin, config)) + 28 <= origin
        assert feature_row(original, original.series[0], origin, 7, _codes(original)) == \
            feature_row(altered, altered.series[0], origin, 7, _codes(altered))



def test_report_and_api_scenario():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        write_demo(path / "data")
        result = run_study(load_m5(path / "data"))
        write_report(result, path / "report")
        assert (path / "report" / "index.html").is_file()
        assert (path / "report" / "monitoring.json").is_file()
        assert (path / "report" / "model_card.md").is_file()

        client = TestClient(create_app(path / "report"))
        assert client.get("/health").json()["series_count"] == 24
        rows = client.get("/series", params={"store": "CA_1"}).json()
        assert rows and all(row["store"] == "CA_1" for row in rows)
        series_id = rows[0]["id"]
        forecast = client.get(f"/forecast/{series_id}")
        assert forecast.status_code == 200
        assert len(forecast.json()["forecast"]) == 28
        response = client.post("/scenario", json={
            "series_id": series_id, "cushion_percentile": 0.9,
            "shortage_cost": 5, "excess_cost": 1,
        })
        assert response.status_code == 200
        assert response.json()["selected"]["ordered_units"] >= 0
        assert response.json()["future_order_units"] >= 0
        higher = client.post("/scenario", json={
            "series_id": series_id, "cushion_percentile": 0.95,
        }).json()
        assert higher["future_order_units"] >= response.json()["future_order_units"]
        assert client.post("/scenario", json={"series_id": series_id,
                                               "cushion_percentile": 0.6}).status_code == 422
        assert client.get("/forecast/missing").status_code == 404


def test_dashboard_refresh_preserves_saved_study_artifacts(tmp_path):
    write_demo(tmp_path / "data")
    result = run_study(load_m5(tmp_path / "data"))
    report_dir = tmp_path / "report"
    write_report(result, report_dir)
    saved = {name: (report_dir / name).read_bytes()
             for name in ("results.json", "monitoring.json", "model_card.md")}
    result["source"] = "synthetic demonstration with refreshed presentation"

    write_dashboard(result, report_dir)

    assert "synthetic demonstration with refreshed presentation" in (report_dir / "index.html").read_text()
    for name, content in saved.items():
        assert (report_dir / name).read_bytes() == content


def test_saved_lightgbm_reproduces_future_predictions(tmp_path):
    import pytest
    lgb = pytest.importorskip("lightgbm")
    write_demo(tmp_path / "data")
    dataset = load_m5(tmp_path / "data")
    config = ModelConfig(train_days=28, stride_days=28, rounds=3, threads=1)
    cutoff = len(dataset.dates)
    booster, codes, training_rows = train_lightgbm(dataset, cutoff, config)
    expected = predict_lightgbm(dataset, cutoff, booster, codes)
    save_model(booster, codes, config, dataset.dates[-1], tmp_path, training_rows)
    reloaded = lgb.Booster(model_file=str(tmp_path / "lightgbm.txt"))
    actual = predict_lightgbm(dataset, cutoff, reloaded, codes)
    for series_id in expected:
        assert actual[series_id] == pytest.approx(expected[series_id])
