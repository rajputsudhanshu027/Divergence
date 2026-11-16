# Five-minute interview demonstration

## Before the interview

From the project folder:

```bash
uv sync --locked --all-extras
uv run retail-planner analyze
uv run retail-planner serve --output-dir reports/latest
```

The saved real-data report must exist. A fresh checkout includes the small portfolio CSVs and case study, but raw data, the trained model, database, and full dashboard are excluded from Git. Follow the README to rebuild them. Keep the [case study](../reports/portfolio/case_study.md) open as a fallback if a local service fails. Do not run training during the interview.

## 0:00–0:45 — State the decision

“This project asks which retail products and stores need closer stock review. I analyzed a seeded sample of 1,000 item-store histories, compared demand forecasting methods, and used SQL to identify where their errors matter. The stock-cost comparison is a simulation.”

Explain the data flow from source files through model evaluation to the dashboard. Show how the checks support the reported results.

## 0:45–1:30 — Show the data and model

Open http://127.0.0.1:8000/ and choose an item-store pair. Point to observed sales, future predictions, and the interval. Dates are historical: “future” means after the dataset cutoff, not after today.

Explain the distinction between three rolling validation windows and the final holdout. Model selection uses validation results. The selected model's final error is 0.759 versus 0.988 for the 28-day repeat, a 23.2% reduction in this subset score. The weekday blend is close at 0.785, so model complexity deserves scrutiny.

## 1:30–2:30 — Demonstrate SQL

In a second terminal:

```bash
uv run python scripts/run_query.py store_performance
uv run python scripts/run_query.py category_performance
```

Open [the store SQL](../src/retail_planner/analysis/sql/store_performance.sql). Explain the item-store-day grain, two-key join, forecast filter, `GROUP BY`, and why WAPE is a ratio of sums.

For the saved M5 run: CA_1 has 88.4% WAPE. HOBBIES has 108.4% selected WAPE versus 120.4% for the baseline. Improvement does not mean forecasting is dependable.

## 2:30–3:30 — Show the decision and its assumptions

Change the order cushion in the dashboard and explain why the future order changes. Change shortage and leftover costs and explain that these affect the historical cost comparison rather than the order rule.

The saved scenario's total cost is 29,045 versus 31,995, about 9.2% lower. Costs are arbitrary units with an immediate one-time order and assumed starting stock. They are not currency, measured savings, or actual business impact.

## 3:30–4:30 — Recommend an action

“I would review CA_1 and the largest-error items, inspect the direction of bias, and check for assortment changes or unavailable stock using additional operational data. I would compare a simpler weekday method before maintaining a more complex model. I would validate an ordering rule with actual lead times and inventory in a staged pilot.”

Describe these as hypotheses and next steps. This dataset cannot identify the cause of every error.

## 4:30–5:00 — Explain quality and scope

Show `reports/portfolio/export_manifest.json` and describe checksums, row counts, data checks, and export-time metadata. Point to tests that reconcile SQL calculations to the forecast evaluation and test saved-model prediction parity.

Close with one limitation and one concrete next experiment. Offer to write a SQL query live or explain a KPI from the case study.

## Offline alternative

Open the saved `reports/latest/index.html` directly, or show the committed case study and CSVs. Be clear about which artifacts come from the real M5 study and which are synthetic workflow checks.
