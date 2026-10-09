# Lesson 1 — What exactly are we predicting?

## 1. Business question

Suppose you manage one Walmart store. For every stocked product, you want an estimate of daily unit sales during the **next 28 days**. Better estimates can eventually improve purchase quantities, but forecasting is only the first step.

A **SKU-store series** is the history of sales for one product in one store. Sales of Product A in Store X and Product A in Store Y form *different* series because local patterns can differ.

## 2. The data table

M5 starts with a wide table:

| item_id | store_id | d_1 | d_2 | d_3 |
| --- | --- | ---: | ---: | ---: |
| A | CA_1 | 2 | 0 | 4 |
| B | CA_1 | 1 | 1 | 0 |

Our loader reshapes it to long form:

| item_id | store_id | day_index | sales |
| --- | --- | ---: | ---: |
| A | CA_1 | 1 | 2 |
| A | CA_1 | 2 | 0 |
| A | CA_1 | 3 | 4 |
| B | CA_1 | 1 | 1 |

The **target** is `sales`. Calendar dates are attached by joining the `d` keys to `calendar.csv`. We only use `sales` and dates for our first baselines; prices and holiday/SNAP information come in Lesson 2.

## 3. Predicting without cheating

At cutoff `d_50`, you are allowed to read actual sales **through** `d_50` but not `d_51` onward. If the task is to predict the next 28 days, the targets are `d_51..d_78`.

A common mistake: create a rolling-mean feature for `d_55` that uses observed sales from `d_51..d_54`. That data does not yet exist when the 28-day plan is produced at `d_50`. It is **future leakage**.

The starter's three forecasts are generated **directly from the observations available at the cutoff**, even for predictions 28 days ahead.

## 4. Why multiple baselines?

- **Last value:** future daily sales = most recent day's units. Trivial; easy to beat for weekday patterns.
- **Seasonal 7:** future daily sales repeat the last 7 known days. Useful when Monday looks more like Monday than Sunday.
- **Mean 28:** future daily sales = average of the last 28 known days. It smooths noisy individual days but misses weekly peaks.

For example, if the last seven units are `[3, 1, 3, 2, 5, 1, 0]`, the seasonal-7 forecast repeats exactly that vector on days 1–7, 8–14, 15–21, and 22–28. It does **not** use the actual sales from any of those future days.

## 5. Why we use a rolling backtest

Randomly splitting daily sales mixes past and future. Instead, we simulate three historical dates on which a planner could have made a forecast. For each date, hide the next 28 days, forecast them, then compare with actual sales. This tells us how a method holds up across time.

We set aside the last 28 days so that later decisions about which forecasting model to use are not optimized against the final report card. Our early plots and scoring stop before that final month.

## 6. Inspect three metrics

- **MAE** is the average error in units, without regard to sign. An MAE of 2 means about 2 units absolute error per item-day on average.
- **RMSE** penalizes large misses more strongly, because errors are squared before aggregation.
- **WAPE** is absolute error as a percentage of the total actual sales volume; when actual sales sum to zero it is undefined.

These beginner metrics are deliberately simpler than M5's official **WRMSSE**, which requires hierarchy-wide aggregation, scaling, and weights. Do not treat a starter score as a Kaggle score.

## 7. Your assignment

1. Run `python -m retail_forecasting.cli demo`.
2. Open `data/outputs/example_backtest.png`. Identify the **vertical dashed line**. Which side is history and which side is the forecast period?
3. Open `data/outputs/fold_scores.csv`. For each fold, identify the lowest MAE. Does the winning method change?
4. Inspect `src/retail_forecasting/baselines.py`; explain why the weekly baseline repeats **the last 7 days** rather than the **first 7 days**.
5. In `src/retail_forecasting/baselines.py`, change `mean_28` to average over the last 14 days, preserving the function name temporarily. Rerun the demo and explain what changed. Then undo your edit.
6. Run `pytest -q`. Read `test_changing_future_cannot_change_past_origin_forecast` in `tests/test_backtest.py` and explain why that test matters.

**Checkpoint before Lesson 2:** You can define *SKU-store*, *forecast origin*, *horizon*, *time-series leakage*, and *MAE*, and can point to the exact lines that implement each baseline.
