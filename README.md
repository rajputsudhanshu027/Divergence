<<<<<<< HEAD
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
||||||| (empty tree)
=======
# Retail Demand Planner

Forecast retail sales, compare forecasting methods, and explore inventory decisions using Python, LightGBM, SQLite, and FastAPI.

The project asks: **Which stores and products need closer stock review, and how much might they need for the next 28 days?** It includes a reproducible forecasting workflow, an interactive dashboard, seven SQL analyses, and a documented study of 1,000 item-store histories from the public M5 dataset.

**Start with the [case study](reports/portfolio/case_study.md)** to see the findings without installing anything. The [portfolio folder](reports/portfolio/) contains small CSV exports and an audit manifest. Raw data and full generated reports are excluded from Git.

## Quick start

### 1. Install the project

You need **Python 3.10 or newer** and [uv](https://docs.astral.sh/uv/getting-started/installation/). Clone or download this repository, then open a terminal in its root folder, beside `pyproject.toml`.

```bash
uv sync --locked --all-extras
```

This installs the project and its modeling, dashboard, and development dependencies into `.venv`. If you prefer pip, see [alternative installation](docs/usage.md#install-with-pip).

### 2. Generate a demonstration

```bash
uv run retail-planner demo --ml --output-dir reports/demo
```

No dataset download is needed. This creates a small **synthetic** dataset, compares the forecasting methods, and writes a dashboard, forecasts, model, and evaluation artifacts to `reports/demo/`. Synthetic demonstration scores are separate from the real-data results below.

### 3. Open the dashboard

```bash
uv run retail-planner serve --output-dir reports/demo
```

Open **http://127.0.0.1:8000/**. Choose a store and product to inspect sales and forecasts, then change the order cushion and simulated costs. Interactive API documentation is at **http://127.0.0.1:8000/docs**.

Keep the terminal running while using the dashboard; press **Ctrl+C** to stop it. You can also open `reports/demo/index.html` directly in a browser without starting the server.

### 4. Explore the SQL analysis

In a second terminal, from the same project folder:

```bash
uv run retail-planner analyze --output-dir reports/demo --analysis-dir reports/demo-analysis
uv run python scripts/run_query.py store_performance --database reports/demo/analysis.sqlite --limit 5
```

The analysis command creates a SQLite database beside the source report and writes seven CSVs, a case study, a summary, and an export manifest to `reports/demo-analysis/`. See the [analyst guide](docs/analyst-guide.md) for the schema, queries, and spreadsheet exercises.

## Run the real M5 study

1. Download and extract `sales_train_evaluation.csv`, `calendar.csv`, and `sell_prices.csv` from the [M5 data archive](https://zenodo.org/records/10203108).
2. Put all three files directly in `data/raw/m5/`. See [data notes](docs/data.md) for fields, checksums, and sampling details.
3. Run the following commands from the repository root:

```bash
uv run retail-planner run --ml --data-dir data/raw/m5 --limit-series 1000 --output-dir reports/latest
uv run retail-planner analyze --output-dir reports/latest --analysis-dir reports/analysis
uv run retail-planner serve --output-dir reports/latest
```

The input directory must look like this:

```text
data/raw/m5/
├── calendar.csv
├── sales_train_evaluation.csv
└── sell_prices.csv
```

Training the real study takes more time and memory than the synthetic demonstration. `--limit-series 1000` uses a deterministic sample. Omit `--ml` to compare only the four simple forecasting methods. Start with the sample before considering the complete dataset.

Generated analysis goes to `reports/analysis/`; the checked-in `reports/portfolio/` remains the published study snapshot. Reusing an output directory replaces its generated files.

## Saved study results

The published study covers **1,000 item-store histories across 1,941 days**, using three historical validation periods and a separate final 28-day holdout.

| Forecasting method | Holdout subset hierarchy WRMSSE ↓ |
|---|---:|
| LightGBM | 0.773 |
| Weekday blend | 0.785 |
| 28-day seasonal baseline | 0.988 |

LightGBM achieved **21.7% lower forecast error** than the 28-day seasonal baseline, and about **1.5% lower error** than the stronger weekday blend. Its holdout WAPE was **75.0%**, so substantial forecasting error remains.

The one-order inventory simulation produced a cost of **29,281 versus 31,995** in arbitrary units, about **8.5% lower**. This is a hypothetical scenario, not measured business savings. See the [case study](reports/portfolio/case_study.md) for segment findings and limitations.

## How the workflow works

1. Load sales, calendar information, and prices from the three M5 tables.
2. Compare four baselines and, when requested, a global LightGBM model over three expanding-window validation folds.
3. Select the method with the lowest mean validation subset hierarchy WRMSSE. Calibrate forecast intervals and inventory cushions using validation residuals.
4. Evaluate the selected method on the separate final 28 days.
5. Forecast the next 28 days, save the results and provenance, and generate the HTML report.
6. Optionally export the SQL analysis or serve the saved report through FastAPI.

Sales-derived features stop before each forecast date. Known calendar events can be used in advance. The API reads saved results; training happens through the `run` or `demo` command. Read the [methodology](docs/methodology.md) for scoring and assumptions.

## Repository structure

```text
retail-demand-planner/
├── README.md                 # Setup, workflow, and findings
├── CONTRIBUTING.md           # Development and validation
├── pyproject.toml            # Dependencies, CLI, and package resources
├── uv.lock                   # Resolved dependency versions
├── Dockerfile                # Container for serving a generated report
├── data/                     # Data setup notes; raw CSVs stay local
├── docs/                     # Architecture, usage, method, and guides
├── reports/
│   ├── README.md             # Generated artifacts and retention conventions
│   └── portfolio/            # Shareable results from the published M5 study
├── scripts/
│   └── run_query.py          # Read-only query runner for a generated database
├── src/retail_planner/
│   ├── cli.py                # Command parsing and workflow orchestration
│   ├── data/                 # M5 loading, data records, and run provenance
│   ├── forecasting/          # Baselines and optional LightGBM model
│   ├── evaluation/           # Validation, metrics, diagnostics, inventory
│   ├── analysis/             # SQLite exports and packaged SQL queries
│   └── presentation/         # HTML report, template, and HTTP interface
├── tests/                    # Forecasting, analysis, CLI, and integration checks
└── .github/workflows/ci.yml   # Automated validation on pushes and pull requests
```

See [architecture](docs/architecture.md) for the dependency diagram, module interfaces, and where to make changes. See [report artifacts](reports/README.md) for the files generated by each command.

## Documentation

| Guide | Read it to… |
|---|---|
| [Usage and troubleshooting](docs/usage.md) | Use command options, HTTP endpoints, pip, or Docker; resolve setup errors |
| [Architecture](docs/architecture.md) | Understand module responsibilities, dependencies, and data flow |
| [Data](docs/data.md) | Download the inputs and understand their fields and sampling |
| [Methodology](docs/methodology.md) | Understand validation, metrics, intervals, and inventory assumptions |
| [Analyst guide](docs/analyst-guide.md) | Explore the SQL model, queries, and spreadsheet exercises |
| [Five-minute demonstration](docs/demo.md) | Present the real-data study step by step |
| [Interview preparation](docs/interview-prep.md) | Practice explaining the results and limitations |
| [Contributing](CONTRIBUTING.md) | Set up development and validate a change |

## Scope and limitations

- Results describe a sampled historical study, not an official full-M5 competition score or a live deployment. Forecast dates follow the dataset cutoff, not today's date.
- Zero sales can reflect low demand or unavailable stock; this dataset cannot distinguish them.
- Inventory calculations assume immediate delivery, one order, and seven days of starting stock. The order cushion does not guarantee item-level service.
- Cost controls change the retrospective simulation; they do not change the order rule.
- New study runs save input hashes, selected-series fingerprints, configuration, and package versions in `run_manifest.json`. The published study has export-time metadata; its original training environment was not recorded.

This is a portfolio and research project. Operational ordering would require additional inventory data, validation, and ongoing monitoring.
>>>>>>> 81a3116 (first commit)
