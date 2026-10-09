"""Run as: python -m retail_forecasting.cli demo | run"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from retail_forecasting.backtest import evaluate_baselines, origins_for_backtest
from retail_forecasting.data import load_daily_from_kaggle
from retail_forecasting.demo import demo_daily
from retail_forecasting.metrics import average_folds, score


def make_plot(daily: pd.DataFrame, preds: pd.DataFrame, output: Path) -> None:
    series_id = str(preds["id"].iloc[0])
    last_fold = int(preds["fold"].max())
    preds = preds.loc[(preds["id"] == series_id) & (preds["fold"] == last_fold)]
    origin = int(preds["origin_day"].iloc[0])
    past = daily.loc[(daily["id"] == series_id) &
                     daily["day_index"].between(origin - 55, origin)]
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(past["date"], past["sales"], label="Observed history", linewidth=1.5)
    ax.plot(preds.loc[preds["method"] == "seasonal_7", "date"],
            preds.loc[preds["method"] == "seasonal_7", "actual"],
            label="Actual future (backtest)", linewidth=2)
    for method in ["last_value", "seasonal_7", "mean_28"]:
        part = preds.loc[preds["method"] == method]
        ax.plot(part["date"], part["predicted"], label=method, alpha=0.8)
    ax.axvline(past["date"].max(), linestyle="--", color="black", alpha=0.5)
    ax.set(title=f"Backtest: {series_id} | fold {last_fold}", ylabel="Daily units")
    ax.legend(ncol=2, fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output, dpi=140)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="M5 forecasting learning milestone 1")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Run a synthetic dataset; no Kaggle download needed")
    demo.add_argument("--output", type=Path, default=Path("data/outputs"))
    run = sub.add_parser("run", help="Run on official M5 CSV files")
    run.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    run.add_argument("--store", default="CA_1")
    run.add_argument("--series", type=int, default=30)
    run.add_argument("--lookback-days", type=int, default=365)
    run.add_argument("--output", type=Path, default=Path("data/outputs"))
    args = parser.parse_args()

    if args.command == "demo":
        daily = demo_daily()
        output = args.output
        print("DATA SOURCE: synthetic demo, NOT Walmart M5")
    else:
        daily = load_daily_from_kaggle(
            args.data_dir, store_id=args.store,
            max_series=args.series, lookback_days=args.lookback_days,
        )
        output = args.output
        print(f"DATA SOURCE: Kaggle M5 sample ({args.store}, {args.series} series max)")

    last_day = int(daily["day_index"].max())
    holdout_start = last_day - 28 + 1
    training_only = daily.loc[daily["day_index"] < holdout_start]
    print(f"Sampled SKU-store series: {daily['id'].nunique()}")
    print(f"Training-period zero-sales rate: {(training_only['sales'] == 0).mean():.1%}")
    print(f"Backtest forecast origins: {origins_for_backtest(last_day)}")
    print(f"Untouched final 28-day test period: d_{holdout_start}..d_{last_day}")

    preds = evaluate_baselines(daily)
    fold_scores = score(preds)
    summary = average_folds(fold_scores)
    print("\nScores by fold (lower is better):")
    print(fold_scores.round(3).to_string(index=False))
    print("\nAverage fold scores (NOT official M5 WRMSSE):")
    print(summary.round(3).to_string(index=False))

    output.mkdir(parents=True, exist_ok=True)
    preds.to_csv(output / "backtest_predictions.csv", index=False)
    fold_scores.to_csv(output / "fold_scores.csv", index=False)
    make_plot(daily, preds, output / "example_backtest.png")
    print(f"\nSaved predictions, scores, and plot to {output.resolve()}")


if __name__ == "__main__":
    main()
