from pathlib import Path

import pytest

from retail_planner.data.m5 import load_m5, write_demo


def test_demo_loader_aligns_sales_calendar_prices_and_future_dates(tmp_path):
    write_demo(tmp_path)

    dataset = load_m5(tmp_path)

    assert len(dataset.series) == 24
    assert len(dataset.dates) == len(dataset.series[0].sales)
    assert len(dataset.calendar) == len(dataset.dates) + 28
    assert dataset.prices
    assert dataset.calendar[0].date == dataset.dates[0]


def test_sampling_is_deterministic_and_not_a_prefix(tmp_path):
    write_demo(tmp_path)

    first = load_m5(tmp_path, limit_series=7)
    second = load_m5(tmp_path, limit_series=7)
    full = load_m5(tmp_path)

    assert [item.id for item in first.series] == [item.id for item in second.series]
    assert [item.id for item in first.series] != [item.id for item in full.series[:7]]


def test_loader_reports_missing_required_input(tmp_path):
    with pytest.raises(FileNotFoundError, match="sales_train_evaluation.csv"):
        load_m5(Path(tmp_path))
