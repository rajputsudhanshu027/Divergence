# Development Divergence Explorer — Project Plan

## Goal

Let users compare a focus country's development trajectory with two or three countries they choose, and inspect when and how outcomes separate.

## Problem and intended users

Large development dashboards make users interpret indicators one at a time. Students, researchers, policymakers, and general readers need a clear way to compare country trajectories and spot unusually positive or negative patterns.

## Current MVP

- Streamlit dashboard with offline synthetic demo data.
- Optional unauthenticated World Bank indicator fetch plus checksum-verified offline snapshots.
- Eight outcomes, user-selected comparisons, country coverage, trajectory and relative-gap charts, and CSV export.
- Three country case studies grounded in World Bank series and independent official context sources.
- Local refresh script and host-local weekly cron schedule; a separate GitHub Actions workflow is prepared but not activated.

## Planned work

1. [x] Expand beyond the initial indicator set to life expectancy, education, electrification, emissions, poverty, and labor participation.
2. [x] Let users select two or three comparison countries directly.
3. [x] Add missing-data coverage reporting and year-specific comparison-group counts.
4. [x] Compare each selected country's outcome series and the available-data comparison mean.
5. [x] Add a max-Chow-F one-break test with an AR(1)-residual bootstrap and explicit statistical caveats.
6. [x] Prepare three evidence-based country case studies and an interactive explorer.
7. [x] Add scheduled data refresh and reproducible cached datasets.

### Statistical and refresh implementation notes

The comparison interface plots each selected country's outcome alongside the focus country and the available-data mean. Missing country-years are not imputed. Users can choose any two or three countries in the fixed universe.

Item 5 tests one unknown break in the relative-gap trend. The maximum Chow F statistic is compared with 499 bootstrap draws generated under an estimated AR(1) residual null with empirical innovations. The max statistic adjusts the p-value for searching break dates; inference is approximate and conditional on the user-selected countries, outcome, and period. It does not adjust across all dashboard explorations.

Item 7 is implemented as a runnable local command and a weekly GitHub Actions workflow. `scripts/refresh_world_bank.py` downloads the dashboard indicator series for the fixed country universe, writes a hash-addressed CSV plus a checksum manifest, and retains the current and two previous CSV versions in the working tree. The app can load a verified snapshot offline. The workflow commits the refreshed files to the default branch.

The host-local cron entry is installed for Mondays at 09:47 IST and runs the project's `.venv/bin/python scripts/refresh_world_bank.py`, appending to `logs/world-bank-refresh.log`. The log file is expected to appear after the first scheduled run. README documents crontab/log/manifest status checks and how to remove only this job; this does not delete the last cached snapshot. The independent GitHub Actions schedule remains inactive because this workspace has no Git repository or remote. Its remaining activation step is to push the workflow to a hosted repository's default branch, enable Actions, and grant the workflow's built-in `GITHUB_TOKEN` permission to write contents (or adapt it to open a pull request if branch protection blocks direct commits). Neither schedule needs a World Bank API key.

The app reads `data/world_bank_manifest.json` and its hash-addressed CSV by default; `DDE_SNAPSHOT_DIR` can point both the app and refresh script at another directory. A verified snapshot older than 45 days stays usable and is visibly flagged stale rather than replaced by demo values.

## Suggested stack and sources

Python, pandas, NumPy, requests, Plotly, and Streamlit. Primary data source: [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392).

## Measures and evaluation

Measure missing-data coverage and the size of selected-country relative gaps across alternate indicators and comparison groups. Evaluate conclusions through case studies and sensitivity analysis; predictive accuracy is not the objective.

## Scope and cautions

The fixed country catalog limits the available comparisons, and the app uses one selected indicator at a time. Divergence scores are descriptive comparisons, not causal explanations. Clearly identify data coverage and the selected comparison countries.

## Effort estimate

Full portfolio scope: approximately 6–8 weeks (80–120 hours).
