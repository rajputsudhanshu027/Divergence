# Retail demand: analyst case study

## Business question

Which stores and products need a closer stock review, and does a demand forecast improve a simple order scenario?

## Data and scope

- Source: **M5 sales_train_evaluation.csv**. Public historical retail data; a sampled study, not a live store deployment.
- 1,000 item-store histories; full study dates 2011-01-29 to 2016-05-22.
- Full-study zero-sales share: 68.3%.
- SQL mart: only the **last 56 observed days**, the **28-day historical holdout predictions**, and **28 future forecast days**. It is not the complete raw dataset.
- Future means dates after this historical dataset's cutoff, not forecasts for today's stores.

## Approach

Validate the exported records, build a SQLite star schema, join actuals to forecasts at item-store-day grain, and compare stores, categories, weekdays, and complete weeks. Choose a forecasting method using rolling validation before examining the holdout.

## Findings

- Selected method: **lightgbm**.
- Holdout subset hierarchy WRMSSE: **0.773**, versus **0.988** for the 28-day repeat; relative reduction **21.7%**.
- Holdout WAPE: **75.0%**. Lower error than a baseline still leaves substantial uncertainty.
- Simulated order cost: **29,281** versus **31,995** in arbitrary cost units.
- Observed 80% / 90% interval coverage: **79.2% / 89.8%**.

### Method comparison

| method | validation_wrmsse | holdout_wrmsse | selected |
| --- | --- | --- | --- |
| lightgbm | 0.7491 | 0.7735 | 1 |
| weekday_blend | 0.7892 | 0.7854 | 0 |
| seasonal_7 | 0.9591 | 0.9715 | 0 |
| seasonal_28 | 0.9689 | 0.9884 | 0 |
| last | 1.4481 | 1.3076 | 0 |

### Store review

WAPE and bias below are decimal ratios. Positive bias means overforecasting. Undefined WAPE means zero observed demand.

| store_id | series_count | actual_units | wape | bias |
| --- | --- | --- | --- | --- |
| CA_1 | 106 | 3234.0000 | 0.8840 | -0.1075 |
| WI_1 | 104 | 3075.0000 | 0.8756 | -0.2040 |
| TX_1 | 102 | 2955.0000 | 0.8571 | 0.0494 |
| WI_2 | 95 | 2926.0000 | 0.7954 | -0.0055 |
| CA_2 | 97 | 3703.0000 | 0.7487 | -0.1323 |
| WI_3 | 96 | 3055.0000 | 0.7383 | -0.1037 |
| CA_3 | 114 | 6322.0000 | 0.7154 | -0.0257 |
| CA_4 | 85 | 2978.0000 | 0.7056 | -0.0204 |
| TX_3 | 94 | 4523.0000 | 0.6625 | -0.1622 |
| TX_2 | 107 | 4905.0000 | 0.6548 | 0.0103 |

### Category comparison

| category | actual_units | selected_wape | baseline_wape | selected_bias |
| --- | --- | --- | --- | --- |
| HOBBIES | 3531.0000 | 1.0839 | 1.2036 | -0.0473 |
| HOUSEHOLD | 9853.0000 | 0.8160 | 0.9967 | 0.0261 |
| FOODS | 24292.0000 | 0.6753 | 0.8606 | -0.1090 |

### Largest item errors

| series_id | actual_units | predicted_units | absolute_error_units |
| --- | --- | --- | --- |
| FOODS_3_785_CA_3_evaluation | 608.0000 | 135.3369 | 473.1384 |
| FOODS_3_804_TX_3_evaluation | 754.0000 | 363.1569 | 394.7840 |
| FOODS_1_043_WI_1_evaluation | 317.0000 | 4.3030 | 313.2199 |
| FOODS_3_120_TX_3_evaluation | 782.0000 | 682.7682 | 251.7112 |
| HOUSEHOLD_1_459_CA_3_evaluation | 422.0000 | 633.3978 | 226.2150 |

## Recommended next action

Review **CA_1**, the store with the largest holdout WAPE (88.4%). Inspect high-error items before changing stock policy. Compare the sign of bias and the costs of shortages and leftovers. Validate the assumptions in a staged pilot with lead times and real inventory before approving an order rule. SQL identifies review candidates; it cannot establish why a store is difficult to forecast.

## Quality and reproducibility

56,000 observed item-days passed checks for unique IDs, aligned dates, finite nonnegative sales, matching holdout/history values, and ordered interval bounds. Primary keys and foreign keys protect joins. See `export_manifest.json` for result and SQL checksums, row counts, and the environment observed when exporting.

## Limits

These scores cover a subset and cannot be compared with the official M5 leaderboard. Zero sales may reflect low demand or unavailable stock; the data cannot distinguish them. Inventory costs are a one-order simulation, not revenue or measured savings. The SQL mart's 56-day trends cannot establish annual seasonality. Forecast intervals are pooled and do not guarantee item-level service. Export-time metadata does not reconstruct the original training environment.
