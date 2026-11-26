# Development Divergence Explorer

A Streamlit dashboard for comparing a focus country's development trajectory with two or three countries selected by the user. It supports eight outcome indicators, country-level coverage reporting, relative-gap analysis, and CSV export.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app defaults to the checksum-verified **World Bank downloaded snapshot** when one is present; otherwise it uses the **World Bank API (live)**. Both sources contain observed country-level indicator values, subject to the World Bank's definitions, reporting gaps, and revisions. Synthetic demo data is available only as an explicit selection. The API needs no account or API key. Live responses are cached in memory for 24 hours; restarting the app clears that cache.

For development checks, install the optional test dependencies with `pip install -r requirements-dev.txt`.

## Refresh and snapshot data

Fetch a full reproducible snapshot (1960 through the current year) with:

```bash
python scripts/refresh_world_bank.py
```

To choose a different range or destination, use for example:

```bash
python scripts/refresh_world_bank.py --start-year 1990 --end-year 2024 --output-dir data
```

The script fetches the outcome indicator series for the app's 32-country universe. It writes a CSV of observed values and a JSON manifest containing retrieval time, years, series, record counts, and a SHA-256 checksum. The CSV is hash-named and immutable; the manifest atomically points to the current file. The app verifies the checksum before offering snapshot values. The latest three CSV versions are retained in the working tree; older versions remain available through Git history when committed.

The script retries transient API/network errors. It writes no new snapshot until every request succeeds and returns a non-empty panel. A failed fetch exits non-zero and leaves the current manifest and snapshot usable. If the manifest or its CSV is missing or has a checksum mismatch, snapshot mode shows a warning and the app clearly labels its synthetic fallback.

The app looks in the project `data/` directory by default. A verified snapshot older than **45 days** remains in use with a visible stale-data warning; it does not silently switch to synthetic data. Refresh it with the script or explicitly choose live API mode. An invalid/missing retrieval timestamp also warns while leaving checksum-verified values available.

### Host-local cron schedule

This host's user crontab has an active Development Divergence Explorer entry for **Mondays at 09:47 IST**. It runs the project's `.venv/bin/python scripts/refresh_world_bank.py` and appends output to `logs/world-bank-refresh.log`. The first run will create the log file; until then, an empty or missing log is expected. The `logs/` directory must exist and remain writable by the crontab owner.

Check the installed schedule and last run:

```bash
crontab -l
tail -n 50 "/home/sudhanshu-rajput/Desktop/data-science/Development Divergence Explorer/logs/world-bank-refresh.log"
grep '"retrieved_at"' "/home/sudhanshu-rajput/Desktop/data-science/Development Divergence Explorer/data/world_bank_manifest.json"
```

The crontab uses the host's local timezone. Its refresh log is append-only; configure log rotation if it will run long-term. To disable only this refresh, run `crontab -e`, remove the two Development Divergence Explorer comment/command lines, save, then run `crontab -l` to confirm the entry is gone. Do not use `crontab -r`, which removes every job in that user's crontab. Disabling the job leaves the current snapshot and log intact; the app continues to use the last checksum-valid snapshot and warns after 45 days.

The data directory keeps the current and two prior CSV snapshots; older local versions are removed unless preserved elsewhere. Each successful refresh updates the manifest timestamp, and the app sees it on its next rerun.

For an alternate data directory, point both the app and refresh command to the same path:

```bash
DDE_SNAPSHOT_DIR="/absolute/path/to/cache" streamlit run app.py
python scripts/refresh_world_bank.py --output-dir "/absolute/path/to/cache"
```

### GitHub Actions schedule

The separate [GitHub Actions workflow](.github/workflows/refresh-world-bank.yml) is configured for Mondays at 04:17 UTC and supports manual dispatch. It is **not active** from this workspace because no Git remote/repository is configured. Activation requires putting it on the hosted repository's default branch, enabling Actions, and allowing `GITHUB_TOKEN` content writes to that branch. Branch protection may require a pull-request-based update instead. Neither schedule needs a World Bank API key.

## Data sources and measures

Live observations come from the [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392). Outcome series:

| Measure | World Bank indicator |
| --- | --- |
| GDP per capita (constant 2015 US$) | `NY.GDP.PCAP.KD` |
| Life expectancy at birth | `SP.DYN.LE00.IN` |
| Access to electricity | `EG.ELC.ACCS.ZS` |
| Secondary school enrollment, gross | `SE.SEC.ENRR` |
| CO₂ emissions excluding LULUCF (t CO₂e per capita) | `EN.GHG.CO2.PC.CE.AR5` |
| Poverty headcount ($2.15/day, 2017 PPP) | `SI.POV.DDAY` |
| Labor force participation, ages 15+ | `SL.TLF.CACT.ZS` |
| Access to clean cooking fuels and technologies | `EG.CFT.ACCS.ZS` |

The emissions measure uses the World Bank's current CO₂-equivalent series, excluding land use, land-use change, and forestry (LULUCF). It differs from the older `EN.ATM.CO2E.PC` fossil CO₂-only series and should not be spliced with it as if the definitions were unchanged. See the [World Bank indicator metadata](https://data.worldbank.org/indicator/EN.GHG.CO2.PC.CE.AR5).

The comparison universe is a fixed set of 32 countries in Asia, Latin America, Africa, and the Middle East. Users select a focus country and two or three comparison countries directly. Coverage for each selected country is visible in the app; missing values are left out of the annual comparison mean.

## Direct country comparison and interpretation

1. Choose the outcome indicator, focus country, two or three comparison countries, source, and outcome period.
2. The trajectory chart shows each selected country and the equal-weight mean of available comparison-country observations for each year. The downloadable table identifies how many comparison countries contribute in each year.
3. The relative gap is `(focus value − comparison mean) / |comparison mean| × 100`. The change in gap is the difference between first and last observed relative gaps, in percentage points.

These are descriptive comparisons. User-selected countries are not matched controls or causal counterfactuals. A gap does not explain why outcomes differ or predict future outcomes. Indicators have uneven coverage and may be revised by the World Bank.

## Statistical sensitivity procedures

**One-break inference.** For at least 12 observed gap values, the app tests a null of one linear trend against an alternative with separate intercepts and slopes on either side of a single break. It searches candidate boundaries with at least five observations on each side and uses the maximum Chow F statistic. The empirical p-value comes from 499 null bootstrap series: an OLS trend plus an estimated AR(1) residual process, with empirical innovations resampled and autocorrelation decayed across missing-year gaps. The same maximum-over-breaks statistic is recalculated for each replicate, adjusting for the search across candidate dates. A fixed random seed makes the result reproducible for the same data.

This is approximate inference conditional on the user-selected countries and relative-gap series. It assumes a one-break model and an adequate AR(1)/innovation bootstrap; it does not adjust for exploring multiple indicators, countries, comparison groups, or periods. The selected year is the first observed year after the candidate boundary; the app does not provide a break-date confidence interval. Treat the p-value as evidence against this particular one-trend null, not as a causal explanation or proof of a policy effect.

## Demo data, case studies, and refresh

Demo values are deterministic generated examples used only to exercise the interface. They are not measured country statistics, are not calibrated to real countries, and must not be cited as evidence. Live mode falls back to these examples only with an explicit warning and source label.

Three sourced case-study starting points are in [CASE_STUDIES.md](CASE_STUDIES.md): Bangladesh and Ethiopia electricity access, plus Viet Nam GDP growth and poverty context. They pair World Bank indicator series with official contextual material and explicitly avoid causal attribution. The app does not generate case-study claims because outcome indicators alone cannot establish policy mechanisms; verify explanations against country-specific primary sources before drawing conclusions.

The local snapshot command and scheduled workflow provide reproducible cached data. Live observations remain on-demand and cached for 24 hours per running app process. The three case studies pair World Bank outcomes with independent government/statistical sources where available; further source validation and more case studies remain future work.

## Project status

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the intended scope and evaluation measures. Schedule activation still requires a hosted GitHub repository with Actions enabled and write permission for `GITHUB_TOKEN`. No World Bank credentials are required.
