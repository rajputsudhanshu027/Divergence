# Usage and troubleshooting

Run commands from the repository root. Start with the [README quick start](../README.md#quick-start) if this is your first run.

## Install with pip

The README uses uv and the checked-in lockfile. A standard pip installation is also supported:

```bash
python -m venv .venv
```

Activate the environment using the command for your shell:

| Shell | Command |
|---|---|
| Linux/macOS Bash or Zsh | `source .venv/bin/activate` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |

Then install and generate a demonstration:

```bash
python -m pip install -e '.[ml,api,dev]'
retail-planner demo --ml --output-dir reports/demo
retail-planner serve --output-dir reports/demo
```

For Windows Command Prompt, use double quotes around `".[ml,api,dev]"`. A pip installation resolves the version ranges in `pyproject.toml`; uv uses the resolved versions in `uv.lock`.

### Dependency groups

| Extra | Installs | Needed for |
|---|---|---|
| `ml` | NumPy and LightGBM | Training and forecasting with `--ml` |
| `api` | FastAPI and Uvicorn | `serve` and interactive API documentation |
| `dev` | pytest and HTTPX | Automated verification |

The baseline study, HTML report generation, and SQLite analysis use the Python standard library. `uv sync --locked --all-extras` installs all three extras for the documented workflow.

## Commands

Get the complete option list:

```bash
uv run retail-planner --help
```

| Command | Purpose | Reads | Writes |
|---|---|---|---|
| `demo` | Generate and evaluate synthetic sales | Generated demo CSVs | Demo CSVs, forecasts, report, optional model, run manifest |
| `run` | Evaluate models on supplied M5 data | Three M5 CSVs | Forecasts, report, optional model, run manifest |
| `analyze` | Build SQL analysis from a saved study | `<output-dir>/results.json` | SQLite in the report directory; exports in `<analysis-dir>` |
| `serve` | Open saved results over HTTP | `<output-dir>/results.json` and `index.html` | No report artifacts |
| `monitor` | Evaluate saved metrics and optional reference drift | One or two saved reports | `monitoring_check.json` |

Always specify `--output-dir reports/demo` for a synthetic demonstration. The shared default is `reports/latest`, including for `demo`. Reusing a directory replaces its generated files.

### Study options

These options apply to `run` and `demo`:

| Option | Default | Meaning |
|---|---|---|
| `--output-dir` | `reports/latest` | Destination for report artifacts |
| `--ml` | Off | Include the global LightGBM candidate |
| `--folds` | `3` | Number of 28-day validation windows; minimum 2 |
| `--train-days` | `365` | Historical span used to choose eligible ML training origins |
| `--stride-days` | `14` | Spacing between ML training origins |
| `--rounds` | `160` | LightGBM boosting rounds |
| `--threads` | `4` | LightGBM training thread count |
| `--tune-trials` | `0` | Optuna trials on a completed window before the validation folds |
| `--config` | None | JSON experiment profile; explicit command-line values override profile defaults |

`run` also accepts `--data-dir` (default `data/raw/m5`) and `--limit-series` (default `1000`). A zero limit reads all series and can require substantial memory. `demo` generates and uses its own small dataset in `<output-dir>/demo_data/`.

Use `--config configs/sample.json` for the recruiter study or `--config configs/full.json` for the resource-intensive full-series experiment. The full profile is not suitable for a typical laptop.

### Analysis options

```bash
uv run retail-planner analyze --output-dir reports/latest --analysis-dir reports/analysis
```

`--output-dir` identifies the **existing source report**. `--analysis-dir` selects the **export destination**, defaulting to `reports/analysis`. This command does not retrain a model or update the HTML dashboard. Only target `reports/portfolio` when deliberately replacing the published study.

### Serving options

```bash
uv run retail-planner serve --output-dir reports/demo --port 8001
```

The default host is `127.0.0.1`, and the default port is `8000`. If you change the port, use that port in the dashboard and API URLs. The application loads results at startup; restart it after regenerating its report.

### Monitoring options

```bash
uv run retail-planner monitor --output-dir reports/latest
uv run retail-planner monitor --output-dir reports/candidate --reference-dir reports/latest --fail-on-alert
```

The check flags low recent price coverage, interval miscalibration, saved store/category warnings, more than 15% WAPE deterioration, and more than 25% recent-demand movement versus a reference. `--fail-on-alert` returns status 1 for scheduled jobs or deployment gates.

## Query the database

First run `analyze` for your chosen report, then:

```bash
uv run python scripts/run_query.py model_comparison --database reports/demo/analysis.sqlite
uv run python scripts/run_query.py store_performance --database reports/demo/analysis.sqlite --limit 10
```

The runner opens SQLite in read-only mode and prints CSV to the terminal. The query name is a packaged SQL filename without `.sql`. It defaults to `reports/latest/analysis.sqlite` and 20 output rows. The [analyst guide](analyst-guide.md) explains all seven queries.

## HTTP endpoints

Start `serve`, then open `/docs` for interactive request forms and complete schemas.

| Method | Path | Returns |
|---|---|---|
| GET | `/` | Saved HTML dashboard |
| GET | `/health` | Status, dataset source, number of series |
| GET | `/metrics` | Profile, validation, holdout, monitoring, inventory |
| GET | `/series` | Series IDs; optional `store`, `category`, and `limit` filters |
| GET | `/forecast/{series_id}` | Saved history and forecasts for one series |
| POST | `/scenario` | Historical order costs and future order quantities |

For example:

```bash
curl http://127.0.0.1:8000/health
curl 'http://127.0.0.1:8000/series?limit=1'
```

Use an ID returned by `/series` in the `/forecast/{series_id}` path or the following `/scenario` body. Replace the placeholder value before submitting it through `/docs`:

```json
{
  "series_id": "COPY_AN_ID_FROM_SERIES",
  "cushion_percentile": 0.9,
  "shortage_cost": 5,
  "excess_cost": 1
}
```

The cushion must be `0.8`, `0.9`, or `0.95`. Costs must be between 0 and 10,000. Costs adjust the retrospective simulation; the cushion adjusts the order rule. Requests reuse saved forecasts and validation cushions.

## Serve with Docker

Generate a report on the host first. From the repository root in a Bash-compatible shell:

```bash
docker build -t retail-demand-planner .
docker run --rm -p 8000:8000 --mount "type=bind,source=$(pwd)/reports/demo,target=/app/reports/latest,readonly" retail-demand-planner
```

Open http://127.0.0.1:8000/. The image installs the HTTP dependencies and serves the mounted report; it does not include raw data or generate a study. The mount source must be an existing absolute directory containing both `results.json` and `index.html`. For a real study, mount `reports/latest` instead of `reports/demo`.

## Troubleshooting

| Symptom | Resolution |
|---|---|
| `uv` is not found | Install uv from the README link, reopen the terminal, or use pip above. |
| `retail-planner` is not found | Run `uv sync --locked --all-extras`, then `uv run retail-planner`. With pip, activate `.venv` first. |
| Missing M5 CSV or calendar day | Extract all three required files into the same `--data-dir`. Check filenames and [source checksums](data.md). |
| No `results.json` / no report | Generate one with `demo` or `run`, then pass the same `--output-dir` to `serve` or `analyze`. A fresh checkout includes only the small portfolio exports. |
| Missing analysis database | Run `analyze` and point the query runner at `<output-dir>/analysis.sqlite`. |
| Optional ML or HTTP dependency is missing | Run `uv sync --locked --all-extras` or install the appropriate pip extra. |
| Linux LightGBM reports missing `libgomp.so.1` | Install your distribution's OpenMP runtime; on Debian/Ubuntu the package is `libgomp1`. The Docker image includes it. |
| Port 8000 is already in use | Start `serve --port 8001` and open the matching URL. |
| Training uses too much memory | Reduce `--limit-series` for `run`; optionally reduce ML training days, increase stride days, or omit `--ml`. |
| Demo results differ from the case study | The demonstration uses synthetic data. The case study records the published M5 run. |
| Dashboard still shows an old run | Verify the report directory and restart `serve`; it reads JSON once at startup. |

See [report artifacts](../reports/README.md) to check what each step creates.
