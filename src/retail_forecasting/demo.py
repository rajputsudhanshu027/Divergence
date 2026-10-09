"""Small, deterministic, M5-shaped demo data for learning without Kaggle download."""

import pandas as pd


def demo_daily(days: int = 220, series_count: int = 5) -> pd.DataFrame:
    start = pd.Timestamp("2015-01-01")
    rows = []
    for series_idx in range(series_count):
        for d in range(1, days + 1):
            # Predictable weekly behavior + a mild, nonstationary trend.
            dow = (d - 1) % 7
            units = max(0, int((series_idx % 3) + (dow in (4, 5)) * 4 +
                               (d // 65) + (d % (11 + series_idx) == 0) * 2))
            rows.append({
                "id": f"DEMO_{series_idx}_CA_1_validation",
                "item_id": f"DEMO_{series_idx}",
                "store_id": "CA_1",
                "day_index": d,
                "date": start + pd.Timedelta(days=d-1),
                "sales": units,
            })
    return pd.DataFrame(rows)
