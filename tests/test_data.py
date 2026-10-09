import pandas as pd
import pytest

from retail_forecasting.data import load_sales_subset, to_daily


def test_melt_and_calendar_join():
    sales = pd.DataFrame([{
        "id": "ITEM_1_CA_1_validation", "item_id": "ITEM_1", "dept_id": "FOODS_1",
        "cat_id": "FOODS", "store_id": "CA_1", "state_id": "CA", "d_1": 0, "d_2": 2,
    }])
    calendar = pd.DataFrame({"d": ["d_1", "d_2"], "date": ["2011-01-29", "2011-01-30"]})
    result = to_daily(sales, calendar)
    assert result["sales"].tolist() == [0, 2]
    assert result["day_index"].tolist() == [1, 2]
    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == ["2011-01-29", "2011-01-30"]


def test_subset_loader_filters_store_and_recent_days(tmp_path):
    path = tmp_path / "sales_train_validation.csv"
    pd.DataFrame([
        {"id": "x", "item_id": "x", "dept_id": "d", "cat_id": "c", "store_id": "CA_1", "state_id": "CA", "d_1": 1, "d_2": 2, "d_3": 3},
        {"id": "y", "item_id": "y", "dept_id": "d", "cat_id": "c", "store_id": "TX_1", "state_id": "TX", "d_1": 4, "d_2": 5, "d_3": 6},
    ]).to_csv(path, index=False)
    sample = load_sales_subset(path, store_id="TX_1", max_series=1, lookback_days=2)
    assert sample["id"].tolist() == ["y"]
    assert "d_1" not in sample.columns
    assert sample["d_2"].iloc[0] == 5
    with pytest.raises(ValueError):
        load_sales_subset(path, store_id="NO_SUCH_STORE", max_series=1, lookback_days=2)
