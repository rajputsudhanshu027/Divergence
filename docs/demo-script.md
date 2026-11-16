# Recruiter demo script

Target length: 2–4 minutes. Record the browser and terminal at 1440×900 or larger.

## 0:00–0:25 — Problem and result

Open the README. State the decision: which item-store pairs need stock review and how many units might be needed over 28 days. Show the headline 23.2% seasonal-baseline improvement, calibrated interval coverage, and 9.2% simulated cost reduction. Say explicitly that this is a 1,000-series subset study.

## 0:25–1:10 — Planner

Open the dashboard. Change the store and product. Point out 56 days of history, the 28-day forecast, the shaded 80% interval, assumed stock, and suggested order. Change the cushion from 80% to 95% and show that the order cannot decrease.

## 1:10–1:45 — Evaluation honesty

Expand “Compare the forecasting methods.” Explain the three expanding-window validation folds and untouched holdout. Mention that LightGBM beat the seasonal baseline comfortably but improved only 3.4% over the stronger weekday blend. Show interval coverage and explain that it is empirical, not a guarantee.

## 1:45–2:20 — Decision layer

Expand “Explore inventory costs.” Change shortage and excess cost assumptions. Explain that costs change the retrospective comparison but not the forecast. Expand the store/category review and identify one flagged segment using WAPE and bias.

## 2:20–2:50 — Reproducibility and monitoring

In the terminal, show `make sample`, the run manifest, and `retail-planner monitor`. Briefly open the CI workflow and the model-analysis notebook. Close with the most important limitation: real ordering needs current inventory, lead times, service constraints, and a staged pilot.
