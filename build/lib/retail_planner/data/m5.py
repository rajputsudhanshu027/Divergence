"""M5 data records, CSV ingestion, and a small synthetic demonstration dataset."""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


@dataclass(frozen=True)
class Series:
    id: str
    item_id: str
    dept_id: str
    cat_id: str
    store_id: str
    state_id: str
    sales: tuple[float, ...]


@dataclass(frozen=True)
class CalendarDay:
    date: str
    week: str
    weekday: int
    month: int
    event: int
    snap_ca: int
    snap_tx: int
    snap_wi: int

    def snap_for(self, state: str) -> int:
        return {"CA": self.snap_ca, "TX": self.snap_tx, "WI": self.snap_wi}.get(state, 0)


@dataclass(frozen=True)
class Dataset:
    series: tuple[Series, ...]
    dates: tuple[str, ...]
    weeks: tuple[str, ...]
    prices: dict[tuple[str, str, str], float]
    source: str
    calendar: tuple[CalendarDay, ...] = ()


def load_m5(directory: Path, limit_series: int | None = None) -> Dataset:
    sales_path = directory / "sales_train_evaluation.csv"
    calendar_path = directory / "calendar.csv"
    price_path = directory / "sell_prices.csv"
    for path in (sales_path, calendar_path, price_path):
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}. See README.md for data setup.")

    calendar: dict[str, CalendarDay] = {}
    with calendar_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            day = date.fromisoformat(row["date"])
            calendar[row["d"]] = CalendarDay(
                date=row["date"], week=row["wm_yr_wk"], weekday=day.weekday(),
                month=day.month, event=int(bool(row.get("event_name_1") or row.get("event_name_2"))),
                snap_ca=int(row.get("snap_CA") or 0), snap_tx=int(row.get("snap_TX") or 0),
                snap_wi=int(row.get("snap_WI") or 0),
            )

    selected: list[Series] = []
    with sales_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Sales CSV has no header")
        day_columns = sorted(
            (name for name in reader.fieldnames if name.startswith("d_") and name[2:].isdigit()),
            key=lambda name: int(name[2:]),
        )
        if len(day_columns) < 168:
            raise ValueError("Need at least 168 daily sales columns for three folds and a holdout")
        missing_days = [day for day in day_columns if day not in calendar]
        if missing_days:
            raise ValueError(f"Calendar is missing {missing_days[0]}")
        randomizer = random.Random(13)
        for seen, row in enumerate(reader, start=1):
            slot = seen - 1 if not limit_series or seen <= limit_series else randomizer.randrange(seen)
            if limit_series and slot >= limit_series:
                continue
            item = Series(
                id=row["id"], item_id=row["item_id"], dept_id=row["dept_id"],
                cat_id=row["cat_id"], store_id=row["store_id"], state_id=row["state_id"],
                sales=tuple(float(row[day] or 0) for day in day_columns),
            )
            if slot == len(selected):
                selected.append(item)
            else:
                selected[slot] = item
    if not selected:
        raise ValueError("Sales CSV has no series")

    wanted = {(item.store_id, item.item_id) for item in selected}
    prices: dict[tuple[str, str, str], float] = {}
    with price_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pair = (row["store_id"], row["item_id"])
            if pair in wanted and row["sell_price"]:
                prices[(pair[0], pair[1], row["wm_yr_wk"])] = float(row["sell_price"])

    all_days = [calendar[day] for day in day_columns]
    last_number = int(day_columns[-1][2:])
    for step in range(1, 29):
        key = f"d_{last_number + step}"
        if key in calendar:
            all_days.append(calendar[key])
        else:
            next_date = date.fromisoformat(all_days[-1].date) + timedelta(days=1)
            all_days.append(CalendarDay(
                date=next_date.isoformat(),
                week=f"{next_date.isocalendar().year}{next_date.isocalendar().week:02d}",
                weekday=next_date.weekday(), month=next_date.month,
                event=0, snap_ca=0, snap_tx=0, snap_wi=0,
            ))

    return Dataset(
        series=tuple(selected),
        dates=tuple(day.date for day in all_days[:len(day_columns)]),
        weeks=tuple(day.week for day in all_days[:len(day_columns)]),
        prices=prices,
        source="M5 sales_train_evaluation.csv",
        calendar=tuple(all_days),
    )


def write_demo(directory: Path) -> None:
    """Small deterministic fixture with M5's column layout, never a benchmark dataset."""
    directory.mkdir(parents=True, exist_ok=True)
    days = 224
    start = date(2025, 1, 1)
    with (directory / "calendar.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "d", "wm_yr_wk"])
        for index in range(days):
            day = start + timedelta(days=index)
            writer.writerow([day.isoformat(), f"d_{index + 1}", f"{day.isocalendar().year}{day.isocalendar().week:02d}"])

    metadata = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
    with (directory / "sales_train_evaluation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(metadata + [f"d_{index + 1}" for index in range(days)])
        for store_index, store in enumerate(("CA_1", "TX_1", "WI_1")):
            for category_index, category in enumerate(("FOODS", "HOBBIES")):
                for item_index in range(4):
                    item = f"{category}_{item_index + 1:02d}"
                    base = 4 + 2 * store_index + 3 * category_index + item_index
                    values = []
                    for index in range(days):
                        weekday = (start + timedelta(days=index)).weekday()
                        weekend = 3 if weekday >= 5 else 0
                        seasonal = (index // 28) % 3
                        noise = ((index * 17 + item_index * 11 + store_index * 7) % 7) - 3
                        values.append(max(0, base + weekend + seasonal + noise))
                    writer.writerow([f"{item}_{store}_evaluation", item, category + "_1", category,
                                     store, store.split("_")[0], *values])

    with (directory / "sell_prices.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["store_id", "item_id", "wm_yr_wk", "sell_price"])
        weeks = sorted({f"{(start + timedelta(days=index)).isocalendar().year}"
                        f"{(start + timedelta(days=index)).isocalendar().week:02d}" for index in range(days)})
        for store in ("CA_1", "TX_1", "WI_1"):
            for category_index, category in enumerate(("FOODS", "HOBBIES")):
                for item_index in range(4):
                    item = f"{category}_{item_index + 1:02d}"
                    for week in weeks:
                        writer.writerow([store, item, week, f"{2.0 + category_index + item_index * .25:.2f}"])
