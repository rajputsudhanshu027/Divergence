# Method and decision record

## The question

Predict 28 days of sales for each selected item-store pair, then test whether using that prediction would improve a simple one-order inventory scenario. The stock exercise is explicitly hypothetical because M5 does not contain on-hand inventory, purchase orders, delivery times, or holding costs.

## Validation

Three expanding-window validation folds cover consecutive 28-day windows immediately before the final 28-day holdout. Each model forecast uses only sales available before that fold's origin. The global LightGBM candidate is retrained at each origin on completed historical 28-day windows. A fixed configuration is used across folds, so the holdout does not tune hyperparameters. The method with the lowest mean validation subset hierarchy WRMSSE is selected. Absolute residuals from those validation folds calibrate 80% and 90% forecast intervals; aggregate residuals calibrate order cushions. The final holdout is then evaluated once.

## Models

The comparison includes last observed sales, seven-day repeat, 28-day repeat, and a weekday blend of four recent weeks with a capped level adjustment. The LightGBM model is global across selected series and predicts each of the 28 horizon days directly. Its features are horizon day, known calendar fields, item/store/category/department codes, sales lags, rolling demand summaries, item age, and last observed price. A direct horizon model avoids recursively feeding its own forecasts back as sales features.

LightGBM uses a Poisson objective, 31 leaves, learning rate 0.05, 160 rounds, and a fixed seed. Training windows are spaced 14 days apart over the last 365 eligible days. These settings keep the first study tractable; they are not presented as tuned optima. The saved `lightgbm.txt` and `lightgbm_metadata.json` record the final fitted candidate and its feature schema.

## Metrics and decisions

The scorer aggregates selected bottom-level forecasts upward through the 12 M5 hierarchy levels. Within each level, it revenue-weights RMSSE using the 28 days before the forecast origin, then averages level scores. If a selected series lacks a usable price, its unit volume is used as a fallback. This is called **subset hierarchy WRMSSE** throughout the project. It should not be compared with an official full-M5 result.

The report also shows WAPE, bias, mean absolute error, interval coverage, and store/category diagnostics. A lower forecast error does not automatically mean a better inventory decision. The order simulation assumes immediate delivery, seven days of starting stock, one order to cover 28 days, and explicit shortage/leftover unit costs. The large order quantity uses the future forecast; the cost comparison uses the final historical holdout. Changing the **cushion percentile** changes the order, while changing unit costs changes the retrospective cost comparison. The percentile is pooled across item-store series and is not a verified service rate for any single item. Both methods use calibration from their own validation residuals.

## Monitoring triggers

`monitoring.json` records store and category WAPE, bias, interval coverage, and recent demand change. It flags a segment if absolute holdout bias exceeds 10% or 80% interval coverage falls below 70%. These are investigation thresholds, not automatic retraining rules. Before production use, monitor data arrivals, missing prices, distribution shifts, weekly bias, stockout impact, and human overrides on a continuing basis.
