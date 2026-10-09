# Retail demand forecasting — guided M5 starter (Milestone 1)

This repository is the **first runnable milestone** of an end-to-end demand-forecasting and inventory-optimization project. We start with a small number of SKU-store sales series and honest, simple predictions. Machine learning, forecast uncertainty, inventory decisions, dashboard, and API come *after* these foundations are understood.

**What you learn now:** M5's data shape, why forecasts are made at an origin date, three 28-day baselines, expanding-window backtests, evaluation metrics, and how leakage is prevented.

## 0. Create your Python environment

Use Python 3.10+ (3.11 recommended). Open a terminal in this directory:

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## 1. Run immediately, without any download

```bash
python -m retail_forecasting.cli demo
pytest -q
```

This demo uses **synthetic, not Walmart, data**. It produces:
- `data/outputs/fold_scores.csv` — one row per model and time window
- `data/outputs/backtest_predictions.csv` — each forecast and its observed result
- `data/outputs/example_backtest.png` — history, future actuals, and model predictions

Read the scores; **smaller MAE/RMSE/WAPE is better**. Then read `src/retail_forecasting/baselines.py` and `src/retail_forecasting/backtest.py`.

## 2. Download the real dataset

Official Kaggle page: https://www.kaggle.com/competitions/m5-forecasting-accuracy/data

You may need to sign in and accept competition rules. Place these two exact filenames in `data/raw/`:

```text
data/raw/
    sales_train_validation.csv
    calendar.csv
```

**Do not rename** `sales_train_evaluation.csv` to `sales_train_validation.csv`. They have different observed periods. The first milestone intentionally uses the validation dataset with daily sales `d_1` to `d_1913`.

Run:

```bash
python -m retail_forecasting.cli run --data-dir data/raw --store CA_1 --series 30
```

If comfortable, try `--series 100` next. Starter reads only the most recent 365 days to reduce memory. Later, we'll incorporate `sell_prices.csv` and the complete history for official scoring.

## 3. Understand the actual exercise

**Unit of prediction:** one (`item_id`, `store_id`, `date`) combination; target `sales` = observed units sold that day.

**Data format:** M5's original sales table has one row per item-store and columns `d_1`, `d_2`, ..., `d_1913`. `to_daily()` reshapes it into one row per item-store-day and merges dates from `calendar.csv`.

**Forecast origin:** the last day you are allowed to observe when producing a forecast. An origin of `d_1801` predicts `d_1802` through `d_1829` without reading those future units.

**Simple model 1 — last_value:** predict the most recently observed day's unit sales every day for 28 days.

**Simple model 2 — seasonal_7:** repeat the most recent complete 7-day pattern four times, preserving weekdays.

**Simple model 3 — mean_28:** predict the average daily sales from the preceding 28 days.

The 28-day forecast is made **in one shot from the origin**; don't replace unknown future units with their actual observed values to compute days 2–28.

## 4. Our validation plan

On `sales_train_validation.csv` (`d_1` through `d_1913`):

| Fold | Observed through | Forecast window |
| --- | --- | --- |
| 1 | d_1801 | d_1802–d_1829 |
| 2 | d_1829 | d_1830–d_1857 |
| 3 | d_1857 | d_1858–d_1885 |
| Final untouched test | d_1885 | **d_1886–d_1913** |

The starter *does not score* the final test period. We keep that untouched for model selection and comparison later. The script reads the dates but forecast features and validation scores never use this last period.

**Metrics:** MAE = mean absolute error; RMSE = root mean squared error; WAPE = absolute-error sum / actual-demand sum ×100%. When total actual sales are zero, WAPE is undefined, rather than zero. These are **not the competition's WRMSSE**, which requires multiple hierarchy levels, series scaling, and revenue weights. Do not compare these numbers to official M5 leaderboard scores.

## 5. Learning exercises (edit the code)

1. Run the synthetic demo. Explain in your own words what one prediction row in `backtest_predictions.csv` means.
2. Inspect `baselines.py`. Change `mean_28` to use the mean of the past 14 days; rerun. Is MAE better in each fold, or only in one?
3. Open `tests/test_backtest.py`. Explain why modifying a future observation must not modify a forecast made before that observation.
4. Run with 30, then 100 M5 series. Does the best baseline remain the same? Compare the folds rather than just the average.
5. Inspect zero-demand days. Why might repeating the last observed day be a poor forecasting strategy for an intermittently sold product?

## 6. Next milestones

| Milestone | Build | Core skill |
| --- | --- | --- |
| 1 **(this starter)** | Real data loader + 3 baselines + 3 folds + tests | Time-series framing and leakage |
| 2 | Lag/rolling features + calendar/SNAP + causal feature tests | Feature engineering |
| 3 | Global LightGBM forecaster, with honest 28-day inference | Supervised forecasting |
| 4 | Official hierarchy and WRMSSE + multiple-store backtests | Fair model evaluation |
| 5 | Quantile forecasts + coverage checks | Uncertainty |
| 6 | Lead-time demand, reorder points, cost simulation | Inventory decision-making |
| 7 | Streamlit planner + FastAPI + test/monitoring | End-to-end deployment |

### Critical caveats

- **Sales are not exactly demand.** M5 contains observed sales; inventory stockouts can censor unobserved customer demand. Do not treat a zero sale as proof that nobody wanted the product.
- **M5 lacks full replenishment economics.** Supplier lead times, initial stock, holding cost, and lost-sale penalties for the inventory simulator must be explicitly assumed or provided. Any demonstrated savings are *scenario-based simulation*, not measured historical business impact.
- Training a more complex model does **not** guarantee beating these simple baselines. Check each fold and segment before claiming improvements.
- Keep competition data out of git. The `.gitignore` excludes downloaded raw CSV files.

## Source

- M5 competition data: https://www.kaggle.com/competitions/m5-forecasting-accuracy/data
- Official reproducibility methods: https://github.com/Mcompetitions/M5-methods
