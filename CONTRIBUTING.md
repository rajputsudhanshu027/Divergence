# Development guide

## Set up

Use Python 3.10 or newer. From the repository root:

```bash
uv sync --locked --all-extras
```

Read [architecture](docs/architecture.md) before changing module responsibilities, [methodology](docs/methodology.md) before changing evaluation behavior, and [usage](docs/usage.md) for command options.

## Make a change

- Keep numerical and data-loading logic independent of FastAPI and the HTML template.
- Use `evaluation/inventory.py` for order calculations shared by the study, SQL exports, and HTTP scenarios.
- Preserve the time cutoff: no sales feature or training target may cross its forecast origin. Model selection and residual calibration must not use the final holdout.
- Keep SQL and HTML resources inside their owning packages and declared in `pyproject.toml`.
- Write generated artifacts to local report folders. Refresh `reports/portfolio/` only when intentionally publishing a replacement study, and regenerate its case study, summary, CSVs, and manifest together.
- Update documentation when a command, default path, import location, or artifact format changes.

## Validate

The tests cover time leakage, model selection, metric reconciliation, database constraints, report generation, CLI behavior, HTTP scenarios, and saved-model prediction parity.

The `dev` extra includes pytest. To run the forecasting checks in a standard development environment:

```bash
uv run pytest -q tests/test_study.py
```

Choose the relevant test files for the change, using the table in the [architecture guide](docs/architecture.md#where-to-make-a-change). The [GitHub Actions workflow](.github/workflows/ci.yml) installs the package as a distribution, checks the tests, generates a synthetic ML report, and builds its SQL analysis. This also exercises the packaged SQL and HTML resources.

For a manual workflow check, use a separate output folder:

```bash
uv run retail-planner demo --ml --output-dir reports/dev-demo
uv run retail-planner analyze --output-dir reports/dev-demo --analysis-dir reports/dev-analysis
uv run retail-planner serve --output-dir reports/dev-demo
```

Inspect the chart, product filters, order cushion, cost controls, and `/docs`. Synthetic results verify workflow behavior; they do not reproduce the real-data study's scores.

## Reproduce a real-data study

Follow the [README](README.md#run-the-real-m5-study) to obtain the three input CSVs. Keep the run manifest with the result artifacts. It records input SHA-256 hashes, selected-series fingerprint, CLI configuration, and package versions. Report the sample size, validation dates, holdout dates, selected method, and baseline when presenting results.

Use the term **subset hierarchy WRMSSE** for the implemented score. Inventory outcomes are simulated in arbitrary cost units. The published study's export-time manifest does not reconstruct its original training environment.
