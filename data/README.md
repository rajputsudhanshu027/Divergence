# Input data

Raw data stays local and is excluded from Git. Download and extract these three files from the [M5 data archive](https://zenodo.org/records/10203108):

```text
data/raw/m5/
├── calendar.csv
├── sales_train_evaluation.csv
└── sell_prices.csv
```

Run the [real-data workflow](../README.md#run-the-real-m5-study) from the repository root. Use `--data-dir` if the files are stored elsewhere. See [data notes](../docs/data.md) for fields, source checksums, deterministic sampling, and feature cutoffs.

The synthetic `demo` command needs no download. It writes its generated CSVs into `<output-dir>/demo_data/`, keeping them beside that demonstration's artifacts.
