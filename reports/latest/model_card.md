# Model card: lightgbm

## Intended use

Compare 28-day item-store demand forecasts and explore a one-order replenishment scenario. The report supports analysis; it does not place orders or represent actual stock levels.

## Data and evaluation

- Source: M5 sales_train_evaluation.csv
- Item-store series: 1000
- Sales dates: 2011-01-29 through 2016-05-22
- Validation starts: 2016-02-01, 2016-02-29, 2016-03-28
- Final untouched holdout starts: 2016-04-25
- Selection rule: lowest mean subset hierarchy WRMSSE over validation folds.
- Sales features end before each forecast origin. Known calendar fields are available for the forecast dates; price features use only previously observed prices.

## Measured results

| Measure | Selected method | Seasonal 28-day baseline |
|---|---:|---:|
| Holdout subset WRMSSE | 0.773 | 0.988 |
| Holdout WAPE | 75.0% | 92.8% |
| Simulated order cost | 29281 | 31995 |

The selected method's 80% and 90% interval coverage on the holdout were 79.2% and 89.8%. Intervals are pooled, scaled absolute residual quantiles from validation folds, not item-specific probabilistic models.

## Limits and checks

This is a 1000-series subset analysis. Its hierarchy score cannot be compared with an official M5 competition score. The inventory result assumes immediate delivery, one 28-day order, seven days of starting stock, a shortage cost of 5, and a leftover cost of 1; M5 has no observed inventory record for validating savings. Monitor store and category bias, error, and interval coverage in `monitoring.json`. Re-run on more series and more dates before any operational use.
