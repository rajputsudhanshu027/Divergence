"""One global, direct-horizon LightGBM model trained only on completed windows."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path
from statistics import mean, pstdev

from ..data.m5 import CalendarDay, Dataset, Series

FEATURE_NAMES = (
    "horizon_day", "target_weekday", "target_month", "known_event", "known_snap",
    "item_code", "store_code", "department_code", "category_code",
    "lag_1", "lag_7", "lag_28", "lag_56", "mean_7", "mean_28", "mean_56",
    "std_28", "zero_share_28", "recent_vs_previous_28", "item_age_days",
    "last_known_price", "price_change_7d",
)
CATEGORICAL_FEATURES = (5, 6, 7, 8)


@dataclass(frozen=True)
class ModelConfig:
    train_days: int = 365
    stride_days: int = 14
    rounds: int = 160
    threads: int = 4
    early_stopping_rounds: int = 20
    learning_rate: float = 0.05
    num_leaves: int = 31
    min_data_in_leaf: int = 40
    feature_fraction: float = 0.9
    bagging_fraction: float = 1.0
    lambda_l1: float = 0.0
    lambda_l2: float = 0.0


def training_origins(cutoff: int, config: ModelConfig) -> range:
    """Every target in every training example is strictly before cutoff."""
    last = cutoff - 28
    first = max(56, last - config.train_days)
    if last < first:
        raise ValueError("Need at least 84 historical days before fitting LightGBM")
    return range(first, last + 1, config.stride_days)


def _codes(dataset: Dataset) -> dict[str, dict[str, int]]:
    columns = {
        "item_id": sorted({item.item_id for item in dataset.series}),
        "store_id": sorted({item.store_id for item in dataset.series}),
        "dept_id": sorted({item.dept_id for item in dataset.series}),
        "cat_id": sorted({item.cat_id for item in dataset.series}),
    }
    return {column: {value: index for index, value in enumerate(values)}
            for column, values in columns.items()}


def _calendar_day(dataset: Dataset, index: int) -> CalendarDay:
    if dataset.calendar:
        return dataset.calendar[index]
    day = date.fromisoformat(dataset.dates[-1]) + timedelta(days=index - len(dataset.dates) + 1) \
        if index >= len(dataset.dates) else date.fromisoformat(dataset.dates[index])
    return CalendarDay(day.isoformat(), "", day.weekday(), day.month, 0, 0, 0, 0)


def _known_price(dataset: Dataset, item: Series, origin: int) -> tuple[float, float]:
    def recent_price(end: int) -> float:
        for index in range(min(end, len(dataset.weeks) - 1), max(-1, end - 56), -1):
            price = dataset.prices.get((item.store_id, item.item_id, dataset.weeks[index]))
            if price is not None:
                return price
        return 0.0

    current = recent_price(origin - 1)
    prior = recent_price(origin - 8)
    return current, (current / prior - 1.0) if prior else 0.0


def _base(dataset: Dataset, item: Series, origin: int, codes: dict) -> list[float]:
    history = item.sales[:origin]
    recent = history[-28:]
    previous = history[-56:-28]
    first_sale = next((index for index, value in enumerate(history) if value > 0), origin)
    price, price_change = _known_price(dataset, item, origin)
    return [
        float(codes["item_id"][item.item_id]), float(codes["store_id"][item.store_id]),
        float(codes["dept_id"][item.dept_id]), float(codes["cat_id"][item.cat_id]),
        history[-1], history[-7], history[-28], history[-56],
        mean(history[-7:]), mean(recent), mean(history[-56:]), pstdev(recent),
        sum(value == 0 for value in recent) / 28,
        mean(recent) / max(1.0, mean(previous)),
        float(max(0, origin - first_sale)), price, price_change,
    ]


def _row_from_base(dataset: Dataset, item: Series, origin: int, step: int,
                   base: list[float]) -> list[float]:
    day = _calendar_day(dataset, origin + step)
    return [float(step + 1), float(day.weekday), float(day.month), float(day.event),
            float(day.snap_for(item.state_id)), *base]


def feature_row(dataset: Dataset, item: Series, origin: int, step: int,
                codes: dict[str, dict[str, int]]) -> list[float]:
    """`step` is zero based; every sales-derived feature ends at origin - 1."""
    if origin < 56 or step < 0 or step >= 28:
        raise ValueError("Need 56 days of history and a step in the 28-day horizon")
    return _row_from_base(dataset, item, origin, step, _base(dataset, item, origin, codes))


def _training_arrays(dataset: Dataset, origins, codes: dict):
    import numpy as np

    rows: list[list[float]] = []
    labels: list[float] = []
    for origin in origins:
        for item in dataset.series:
            base = _base(dataset, item, origin, codes)
            for step in range(28):
                rows.append(_row_from_base(dataset, item, origin, step, base))
                labels.append(item.sales[origin + step])
    return np.asarray(rows, dtype=np.float32), np.asarray(labels, dtype=np.float32)


def _parameters(config: ModelConfig) -> dict:
    return {
        "objective": "poisson", "metric": "poisson",
        "learning_rate": config.learning_rate, "num_leaves": config.num_leaves,
        "min_data_in_leaf": config.min_data_in_leaf,
        "feature_fraction": config.feature_fraction,
        "bagging_fraction": config.bagging_fraction,
        "lambda_l1": config.lambda_l1, "lambda_l2": config.lambda_l2,
        "verbosity": -1, "seed": 13, "feature_fraction_seed": 13,
        "bagging_seed": 13, "num_threads": config.threads,
    }


def train_lightgbm(dataset: Dataset, cutoff: int, config: ModelConfig):
    try:
        import lightgbm as lgb
    except ImportError as exc:
        raise RuntimeError("Install the ml extra: pip install -e '.[ml]'") from exc

    codes = _codes(dataset)
    origins = list(training_origins(cutoff, config))
    if len(origins) < 2:
        raise ValueError("LightGBM needs at least two completed training windows")
    training = origins[:-1]
    validation = origins[-1:]
    matrix, target = _training_arrays(dataset, training, codes)
    valid_matrix, valid_target = _training_arrays(dataset, validation, codes)
    train_set = lgb.Dataset(matrix, label=target, feature_name=list(FEATURE_NAMES),
                            categorical_feature=list(CATEGORICAL_FEATURES))
    valid_set = lgb.Dataset(valid_matrix, label=valid_target, reference=train_set,
                            feature_name=list(FEATURE_NAMES),
                            categorical_feature=list(CATEGORICAL_FEATURES))
    booster = lgb.train(
        _parameters(config), train_set, num_boost_round=config.rounds,
        valid_sets=[valid_set], valid_names=["time_validation"],
        callbacks=[lgb.early_stopping(
            min(config.early_stopping_rounds, max(1, config.rounds // 2)), verbose=False)],
    )
    return booster, codes, len(target)


def tune_lightgbm(dataset: Dataset, cutoff: int, config: ModelConfig, trials: int) -> tuple[ModelConfig, dict]:
    """Tune on the last completed pre-validation window; no target at/after cutoff is used."""
    if trials < 1:
        return config, {"trials": 0, "best_value": None, "best_params": {}}
    try:
        import lightgbm as lgb
        import numpy as np
        import optuna
    except ImportError as exc:
        raise RuntimeError("Install the ml extra: pip install -e '.[ml]'") from exc

    codes = _codes(dataset)
    origins = list(training_origins(cutoff, config))
    if len(origins) < 2:
        raise ValueError("Tuning needs at least two completed training windows")
    train_matrix, train_target = _training_arrays(dataset, origins[:-1], codes)
    valid_matrix, valid_target = _training_arrays(dataset, origins[-1:], codes)

    def objective(trial):
        candidate = replace(
            config,
            learning_rate=trial.suggest_float("learning_rate", 0.02, 0.1, log=True),
            num_leaves=trial.suggest_int("num_leaves", 31, 127),
            min_data_in_leaf=trial.suggest_int("min_data_in_leaf", 20, 120),
            feature_fraction=trial.suggest_float("feature_fraction", 0.6, 1.0),
            bagging_fraction=trial.suggest_float("bagging_fraction", 0.6, 1.0),
            lambda_l1=trial.suggest_float("lambda_l1", 1e-8, 10.0, log=True),
            lambda_l2=trial.suggest_float("lambda_l2", 1e-8, 10.0, log=True),
        )
        train_set = lgb.Dataset(train_matrix, label=train_target,
                                feature_name=list(FEATURE_NAMES),
                                categorical_feature=list(CATEGORICAL_FEATURES))
        valid_set = lgb.Dataset(valid_matrix, label=valid_target, reference=train_set,
                                feature_name=list(FEATURE_NAMES),
                                categorical_feature=list(CATEGORICAL_FEATURES))
        booster = lgb.train(
            _parameters(candidate), train_set, num_boost_round=config.rounds,
            valid_sets=[valid_set],
            callbacks=[lgb.early_stopping(
                min(config.early_stopping_rounds, max(1, config.rounds // 2)), verbose=False)],
        )
        predicted = booster.predict(valid_matrix, num_threads=config.threads)
        return float(np.mean(np.abs(valid_target - predicted)))

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="minimize", sampler=optuna.samplers.TPESampler(seed=13))
    study.optimize(objective, n_trials=trials, show_progress_bar=False)
    tuned = replace(config, **study.best_params)
    return tuned, {"trials": trials, "best_value": study.best_value,
                   "best_params": study.best_params,
                   "tuning_cutoff": dataset.dates[cutoff - 1]}


def predict_lightgbm(dataset: Dataset, origin: int, booster, codes: dict) -> dict[str, list[float]]:
    import numpy as np

    rows = []
    for item in dataset.series:
        base = _base(dataset, item, origin, codes)
        rows.extend(_row_from_base(dataset, item, origin, step, base) for step in range(28))
    predicted = booster.predict(np.asarray(rows, dtype=np.float32), num_threads=4)
    return {item.id: [max(0.0, float(value)) for value in predicted[index * 28:(index + 1) * 28]]
            for index, item in enumerate(dataset.series)}


def save_model(booster, codes: dict, config: ModelConfig, cutoff_date: str,
               directory: Path, training_rows: int) -> None:
    import json

    directory.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(directory / "lightgbm.txt"))
    metadata = {"feature_names": FEATURE_NAMES, "categorical_features": CATEGORICAL_FEATURES,
                "codes": codes, "config": vars(config), "cutoff_date": cutoff_date,
                "training_rows": training_rows}
    (directory / "lightgbm_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
