"""Data loading and transformation.

M5 stores one item-store series per row with d_1, d_2, ... daily columns.
We intentionally read only a small sample for the first learning milestone.
"""
from pathlib import Path

import pandas as pd

METADATA = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]


def load_sales_subset(
    path: str | Path,
    store_id: str = "CA_1",
    max_series: int = 30,
    lookback_days: int = 365,
) -> pd.DataFrame:
    """Select a limited set of series and recent day columns without loading full M5.

    Note: because we retain only recent history, official M5 WRMSSE cannot be
    computed from this subset; the starter uses MAE/RMSE/WAPE instead.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}. Download the Kaggle M5 data first.")
    if max_series < 1 or lookback_days < 1:
        raise ValueError("max_series and lookback_days must be positive")
    header = pd.read_csv(path, nrows=0).columns.tolist()
    missing = set(METADATA) - set(header)
    if missing:
        raise ValueError(f"Sales file is missing columns: {sorted(missing)}")
    day_cols = sorted(
        (col for col in header if col.startswith("d_") and col[2:].isdigit()),
        key=lambda col: int(col[2:]),
    )
    if len(day_cols) < lookback_days:
        raise ValueError(f"Requested {lookback_days} days but file has {len(day_cols)}")
    usecols = METADATA + day_cols[-lookback_days:]
    selected_chunks = []
    count = 0
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=100):
        matches = chunk.loc[chunk["store_id"].eq(store_id)]
        if matches.empty:
            continue
        take = matches.head(max_series - count)
        selected_chunks.append(take)
        count += len(take)
        if count >= max_series:
            break
    if count == 0:
        raise ValueError(f"No rows found for store_id={store_id!r}")
    return pd.concat(selected_chunks, ignore_index=True)


def to_daily(sales: pd.DataFrame, calendar: pd.DataFrame) -> pd.DataFrame:
    """Melt d_* columns into a dated, item/store daily series table."""
    day_cols = sorted(
        (col for col in sales if col.startswith("d_") and col[2:].isdigit()),
        key=lambda col: int(col[2:]),
    )
    if not day_cols:
        raise ValueError("No M5 day columns found")
    required_calendar = {"d", "date"}
    if not required_calendar.issubset(calendar):
        raise ValueError(f"Calendar must include {sorted(required_calendar)}")
    long = sales.melt(
        id_vars=METADATA, value_vars=day_cols, var_name="d", value_name="sales"
    )
    long["day_index"] = long["d"].str[2:].astype("int32")
    long["sales"] = pd.to_numeric(long["sales"], errors="raise")
    if long["sales"].isna().any() or (long["sales"] < 0).any():
        raise ValueError("Daily unit sales must be nonnegative and nonmissing")
    dates = calendar[["d", "date"]].copy()
    if dates["d"].duplicated().any():
        raise ValueError("Calendar has duplicate day keys")
    long = long.merge(dates, how="left", on="d", validate="many_to_one")
    if long["date"].isna().any():
        raise ValueError("One or more sales day keys are missing from calendar")
    long["date"] = pd.to_datetime(long["date"])
    return long.sort_values(["id", "day_index"], ignore_index=True)


def load_daily_from_kaggle(
    data_dir: str | Path, store_id: str = "CA_1", max_series: int = 30,
    lookback_days: int = 365,
) -> pd.DataFrame:
    data_dir = Path(data_dir)
    sales = load_sales_subset(
        data_dir / "sales_train_validation.csv",
        store_id=store_id, max_series=max_series, lookback_days=lookback_days,
    )
    calendar_path = data_dir / "calendar.csv"
    if not calendar_path.is_file():
        raise FileNotFoundError(f"Missing {calendar_path}")
    calendar = pd.read_csv(calendar_path, usecols=["d", "date"])
    return to_daily(sales, calendar)
