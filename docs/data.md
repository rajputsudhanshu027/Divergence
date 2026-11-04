# Data notes

The project reads three M5 CSVs: `sales_train_evaluation.csv`, `calendar.csv`, and `sell_prices.csv`. The public files are available from the [University of Nicosia archive](https://zenodo.org/records/10203108) and the [M5 Kaggle page](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data). Data files stay outside version control.

| Source field | Meaning | Use here |
|---|---|---|
| `id` | Item-store series identifier | Joining forecasts to source rows |
| `item_id`, `dept_id`, `cat_id` | Product hierarchy | Categorical model features and hierarchy score |
| `store_id`, `state_id` | Location hierarchy | Categorical model features and segment checks |
| `d_1` … `d_1941` | Daily unit sales | Forecast targets, lag features, backtests |
| `date`, `d`, `wm_yr_wk` | Calendar date, day key, retail week | Aligning sales and prices |
| `event_name_1/2` | Calendar events | Known-ahead event indicator |
| `snap_CA/TX/WI` | State SNAP indicator | Known-ahead calendar feature |
| `sell_price` | Store-item-week selling price | Last observed price feature and revenue weight |

The sales table is read as rows of item-store histories. A seeded reservoir sample keeps the study reproducible while covering the file rather than its first rows. The 1,000-series run is a subset study, not an official competition submission. For every forecast origin, lag, rolling, age, and price features stop before that origin. Calendar events and SNAP fields are used for the prediction dates because they are known in advance. Future selling prices are not used by the model.

Missing selling prices in the trailing 28-day weight period trigger a unit-volume fallback for that series. `results.json` records the weight basis. A full M5 leaderboard comparison would need all series, the competition's exact evaluation windows, and the official scoring weights.

The archive lists these MD5 checksums:

| File | MD5 |
|---|---|
| `calendar.csv` | `3ffeab2991b0c8e861d008b39ea4c95c` |
| `sales_train_evaluation.csv` | `b806dfc9f30a745102b708c09951f6aa` |
| `sell_prices.csv` | `08c591caa99e55daf3e0ccac913f7c85` |
