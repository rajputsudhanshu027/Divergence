"""Command line entry point for a demo or a local M5 study."""

from __future__ import annotations

import argparse
from pathlib import Path

from .data.m5 import load_m5, write_demo
from .evaluation.study import run_study
from .forecasting.lightgbm import ModelConfig
from .presentation.report import write_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a 28-day retail demand study")
    parser.add_argument("mode", choices=("demo", "run", "serve", "analyze"))
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/m5"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/latest"))
    parser.add_argument("--analysis-dir", type=Path, default=Path("reports/analysis"),
                        help="Destination for the analyst case study and SQL CSV exports")
    parser.add_argument("--limit-series", type=int, default=1000,
                        help="Deterministic sample size; 0 loads all series and needs substantial memory")
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--ml", action="store_true", help="Include a global LightGBM candidate")
    parser.add_argument("--train-days", type=int, default=365)
    parser.add_argument("--stride-days", type=int, default=14)
    parser.add_argument("--rounds", type=int, default=160)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.limit_series < 0:
        parser.error("--limit-series must be zero or positive")
    if min(args.train_days, args.stride_days, args.rounds, args.threads) < 1:
        parser.error("ML configuration values must be positive")
    if args.mode == "analyze":
        from .analysis.export import build_analytics
        try:
            manifest = build_analytics(args.output_dir, args.analysis_dir)
        except (FileNotFoundError, ValueError) as exc:
            parser.error(str(exc))
        print(f"SQL analysis: {args.analysis_dir / 'case_study.md'} | "
              f"{manifest['quality']['observed_item_days']} observed item-days")
        print(f"SQLite: {args.output_dir / 'analysis.sqlite'}")
        return
    if args.mode == "serve":
        try:
            import uvicorn
            from .presentation.api import create_app
        except ImportError as exc:
            parser.error("Install the api extra: pip install -e '.[api]'")
        uvicorn.run(create_app(args.output_dir), host=args.host, port=args.port)
        return
    data_dir = args.data_dir
    if args.mode == "demo":
        data_dir = args.output_dir / "demo_data"
        write_demo(data_dir)
    dataset = load_m5(data_dir, None if args.mode == "demo" else args.limit_series or None)
    if args.mode == "demo":
        dataset = type(dataset)(dataset.series, dataset.dates, dataset.weeks, dataset.prices,
                                "synthetic demonstration")
    config = ModelConfig(args.train_days, args.stride_days, args.rounds, args.threads)
    result = run_study(dataset, args.folds, include_ml=args.ml, model_config=config,
                       artifact_dir=args.output_dir if args.ml else None)
    write_report(result, args.output_dir)
    from .data.provenance import write_run_manifest
    write_run_manifest(data_dir, args.output_dir, vars(args))
    selected = result["holdout"]["selected"]["subset_wrmsse"]
    baseline = result["holdout"]["seasonal_28"]["subset_wrmsse"]
    print(f"{result['series_count']} series | selected {result['selected_method']} | "
          f"holdout subset WRMSSE {selected:.3f} (seasonal_28: {baseline:.3f})")
    print(f"Report: {args.output_dir / 'index.html'}")


if __name__ == "__main__":
    main()
