import pandas as pd
import pandas.testing as pdt

from retail_forecasting.backtest import evaluate_baselines, origins_for_backtest
from retail_forecasting.demo import demo_daily


def test_final_month_is_untouched():
    daily = demo_daily(days=200, series_count=2)
    result = evaluate_baselines(daily)
    assert origins_for_backtest(200) == [88, 116, 144]
    assert result["day_index"].max() == 172
    assert not (result["day_index"] >= 173).any()
    assert len(result) == 2 * 3 * 28 * 3


def test_changing_future_cannot_change_past_origin_forecast():
    daily = demo_daily(days=200, series_count=1)
    before = evaluate_baselines(daily)
    changed = daily.copy()
    # Change observations AFTER the first origin only.
    changed.loc[changed["day_index"] >= 89, "sales"] += 1000
    after = evaluate_baselines(changed)
    before_first = before.loc[before["fold"] == 1, ["method", "day_index", "predicted"]]
    after_first = after.loc[after["fold"] == 1, ["method", "day_index", "predicted"]]
    pdt.assert_frame_equal(before_first.reset_index(drop=True), after_first.reset_index(drop=True))


def test_higher_sales_in_future_does_change_actual_not_first_predictions():
    daily = demo_daily(days=200, series_count=1)
    original = evaluate_baselines(daily)
    tampered = daily.copy()
    tampered.loc[tampered["day_index"] == 90, "sales"] += 5
    result = evaluate_baselines(tampered)
    assert original.loc[(original["fold"] == 1) & (original["day_index"] == 90), "actual"].iloc[0] != result.loc[(result["fold"] == 1) & (result["day_index"] == 90), "actual"].iloc[0]
    pdt.assert_series_equal(
        original.loc[original["fold"] == 1, "predicted"].reset_index(drop=True),
        result.loc[result["fold"] == 1, "predicted"].reset_index(drop=True),
    )
