# Reports and generated artifacts

## Directory conventions

| Directory | Contents | Included in Git? |
|---|---|---|
| `portfolio/` | Published M5 study: case study, summary, seven CSVs, export manifest | Yes |
| `latest/` | Locally generated real-data study, model, dashboard, optional database | No |
| `analysis/` | Default destination for local SQL exports | No |
| `demo/` | Synthetic demonstration data, model, and dashboard | No |
| `demo-analysis/` | SQL exports from the synthetic demonstration | No |
| Other generated report folders | Artifacts from experiments or development | No |

The portfolio folder is a published snapshot. Default analysis commands write elsewhere. To refresh the snapshot deliberately, generate a real-data report and use `--analysis-dir reports/portfolio`. This replaces its case study, summary, CSVs, and export manifest together.

## Files written by `run` and `demo`

All paths below are relative to `--output-dir`.

| File | Purpose |
|---|---|
| `results.json` | Evaluation, history, holdout predictions, future forecasts, intervals, and inventory assumptions |
| `index.html` | Self-contained dashboard with embedded results; opens directly in a browser |
| `model_card.md` | Intended use, metrics, assumptions, and limitations |
| `monitoring.json` | Segment error, bias, coverage, and warning flags |
| `run_manifest.json` | Input checksums, selected-series fingerprint, run options, and observed environment |
| `lightgbm.txt` | Final fitted LightGBM model; written only with `--ml` |
| `lightgbm_metadata.json` | Feature schema, categorical codes, model configuration, training cutoff; written only with `--ml` |
| `demo_data/` | Generated input CSVs; written only by `demo` |

## Files written by `analyze`

`analysis.sqlite` is created in the **source report directory**, selected by `--output-dir`. It contains series/date dimensions, sales and forecast facts, model evaluation, and inventory scenarios.

The following files go into **`--analysis-dir`**, defaulting to `reports/analysis`:

- `case_study.md`: business question, findings, and limitations.
- `summary.json`: compact study metrics and diagnostics.
- Seven CSVs: `store_performance`, `category_performance`, `weekly_demand`, `weekday_demand`, `model_comparison`, `error_review`, and `inventory_review`.
- `export_manifest.json`: source-result hash, SQL hashes, output hashes, row counts, quality checks, export environment, and whether an original run manifest was available.

The SQL mart contains the last 56 observed days plus 28-day holdout and future forecasts. It does not contain the entire raw M5 history.

Reusing output directories replaces generated files. Keep each experiment in its own folder when comparing runs. See [usage](../docs/usage.md) for commands and [architecture](../docs/architecture.md) for data flow.
