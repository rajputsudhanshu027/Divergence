"""Resampling methods for descriptive peer sensitivity and trend breaks."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


ROBUST_SCALING = "Robust (median/IQR)"


def distance_scores(values: pd.DataFrame, selected: str, method: str) -> pd.DataFrame:
    """Euclidean distance after feature-wise z-score or robust scaling."""
    if selected not in values.index or values.shape[1] == 0:
        return pd.DataFrame(columns=["country", "distance"])
    scaled = values.copy().astype(float)
    for column in scaled.columns:
        center = scaled[column].median() if method == ROBUST_SCALING else scaled[column].mean()
        spread = scaled[column].quantile(.75) - scaled[column].quantile(.25) if method == ROBUST_SCALING else scaled[column].std(ddof=0)
        if not spread or pd.isna(spread):
            spread = 1.0
        scaled[column] = (scaled[column] - center) / spread
    distances = ((scaled - scaled.loc[selected]) ** 2).mean(axis=1).pow(.5).sort_values()
    return distances.rename("distance").rename_axis("country").reset_index()


def select_peers(
    features: pd.DataFrame, selected: str, peer_count: int, method: str
) -> tuple[list[str], pd.DataFrame, list[str]]:
    usable = features.dropna(axis=1, how="all").dropna(axis=0, how="any")
    if usable.shape[1] == 0 or selected not in usable.index or len(usable) < 2:
        return [], pd.DataFrame(columns=["country", "distance"]), list(usable.columns)
    scores = distance_scores(usable, selected, method)
    peers = scores.loc[scores.country != selected, "country"].head(peer_count).tolist()
    return peers, scores, list(usable.columns)


def _baseline_matrix(data: pd.DataFrame, year: int, features: list[str], tolerance: int) -> pd.DataFrame:
    sample = data[data["feature"].isin(features) & data["year"].between(year - tolerance, year + tolerance)].copy()
    if sample.empty:
        return pd.DataFrame()
    sample["distance"] = (sample["year"] - year).abs()
    sample["later"] = (sample["year"] > year).astype(int)
    baseline = sample.sort_values(["country", "feature", "distance", "later", "year"])
    baseline = baseline.groupby(["country", "feature"], as_index=False).head(1)
    return baseline.pivot(index="country", columns="feature", values="value")


def bootstrap_peer_stability(
    data: pd.DataFrame,
    selected: str,
    peer_count: int,
    method: str,
    baseline_year: int,
    feature_names: list[str],
    replicates: int = 250,
    tolerance: int = 2,
    seed: int = 2026,
) -> dict[str, Any]:
    """Resample features and near-baseline observations; compare selected peer sets.

    This estimates design stability of a fixed-k nearest-peer set, not the
    probability that countries are true peers and not population uncertainty.
    """
    empty = {"mean_jaccard": None, "low_jaccard": None, "high_jaccard": None,
             "valid_replicates": 0, "attempted_replicates": replicates, "frequencies": {}}
    if not feature_names or replicates < 1:
        return empty
    sample = data[data["feature"].isin(feature_names) & data["year"].between(baseline_year - tolerance, baseline_year + tolerance)]
    if sample.empty:
        return empty
    base_matrix = _baseline_matrix(sample, baseline_year, feature_names, tolerance)
    baseline_peers, _, _ = select_peers(base_matrix, selected, peer_count, method)
    if not baseline_peers:
        return empty
    baseline_set = set(baseline_peers)
    candidates: dict[str, dict[str, np.ndarray]] = {}
    for (country, feature), group in sample.groupby(["country", "feature"]):
        candidates.setdefault(country, {})[feature] = group["value"].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    overlaps: list[float] = []
    selected_counts: dict[str, int] = {}
    for _ in range(replicates):
        draws = rng.choice(feature_names, size=len(feature_names), replace=True)
        matrix_rows: dict[str, list[float]] = {}
        for country, by_feature in candidates.items():
            values: list[float] = []
            for position, feature in enumerate(draws):
                available = by_feature.get(str(feature))
                if available is None or not len(available):
                    break
                values.append(float(available[rng.integers(0, len(available))]))
            if len(values) == len(draws):
                matrix_rows[country] = values
        if selected not in matrix_rows:
            continue
        columns = [f"feature_{position}" for position in range(len(draws))]
        matrix = pd.DataFrame.from_dict(matrix_rows, orient="index", columns=columns)
        group, _, _ = select_peers(matrix, selected, peer_count, method)
        if not group:
            continue
        group_set = set(group)
        overlaps.append(len(baseline_set & group_set) / len(baseline_set | group_set))
        for country in group_set:
            selected_counts[country] = selected_counts.get(country, 0) + 1
    valid = len(overlaps)
    if not valid:
        return empty
    frequencies = {country: count / valid for country, count in selected_counts.items()}
    for country in baseline_set:
        frequencies.setdefault(country, 0.0)
    return {
        "mean_jaccard": float(np.mean(overlaps)),
        "low_jaccard": float(np.quantile(overlaps, .05)),
        "high_jaccard": float(np.quantile(overlaps, .95)),
        "valid_replicates": valid,
        "attempted_replicates": replicates,
        "frequencies": frequencies,
    }


def _linear_fit(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
    design = np.column_stack((np.ones(len(x)), x))
    coefficients = np.linalg.lstsq(design, y, rcond=None)[0]
    fitted = design @ coefficients
    residuals = y - fitted
    return fitted, float(np.square(residuals).sum()), residuals


def _sup_f_statistic(x: np.ndarray, y: np.ndarray, minimum_segment: int) -> tuple[float, int | None]:
    n = len(y)
    _, null_rss, _ = _linear_fit(x, y)
    best_statistic = -math.inf
    best_split: int | None = None
    denominator_df = n - 4
    if denominator_df <= 0:
        return float("nan"), None
    for split in range(minimum_segment, n - minimum_segment + 1):
        _, left_rss, _ = _linear_fit(x[:split], y[:split])
        _, right_rss, _ = _linear_fit(x[split:], y[split:])
        alternative_rss = left_rss + right_rss
        numerator = max(0.0, (null_rss - alternative_rss) / 2)
        statistic = numerator / max(alternative_rss / denominator_df, 1e-12)
        if statistic > best_statistic:
            best_statistic, best_split = statistic, split
    return float(best_statistic), best_split


def supf_break_test(
    gaps: pd.DataFrame,
    minimum_segment: int = 5,
    bootstrap_replicates: int = 499,
    seed: int = 2026,
) -> dict[str, Any]:
    """Test for one unknown level/slope break with an AR(1) residual bootstrap.

    The empirical bootstrap p-value is for the maximum Chow F statistic across
    eligible break dates, so it accounts for selecting the date from the data.
    Under the null, residuals follow an estimated AR(1) process with empirical
    i.i.d. innovations. This is approximate inference and does not model how
    comparison countries were selected or how the relative gap was constructed.
    """
    unavailable = {"year": None, "sup_f": None, "p_value": None, "critical_95": None,
                   "rho": None, "observations": 0, "replicates": 0, "reason": "No usable gap series."}
    gap_column = "Gap (% of comparison mean)" if "Gap (% of comparison mean)" in gaps else "Gap (% of peer mean)"
    if not {"year", gap_column}.issubset(gaps.columns):
        return unavailable
    sample = gaps[["year", gap_column]].dropna().sort_values("year")
    n = len(sample)
    if n < 2 * minimum_segment + 2:
        return {**unavailable, "observations": n, "reason": f"At least {2 * minimum_segment + 2} observed years are required."}
    years = sample["year"].to_numpy(dtype=float)
    x = years - years.mean()
    y = sample[gap_column].to_numpy(dtype=float)
    if float(np.std(y)) <= 1e-10:
        return {**unavailable, "observations": n, "reason": "The observed gap has no variation."}
    fitted, _, residuals = _linear_fit(x, y)
    observed_statistic, split = _sup_f_statistic(x, y, minimum_segment)
    if split is None or bootstrap_replicates < 99:
        return {**unavailable, "observations": n, "reason": "At least 99 bootstrap replicates are required."}

    gaps_in_years = np.diff(years)
    centered_residuals = residuals - residuals.mean()
    candidates = np.linspace(-0.9, 0.95, 186)
    rho = float(min(candidates, key=lambda phi: np.square(
        centered_residuals[1:] - np.power(phi, gaps_in_years) * centered_residuals[:-1]
    ).sum()))
    innovations = centered_residuals[1:] - np.power(rho, gaps_in_years) * centered_residuals[:-1]
    innovations = innovations - innovations.mean()
    if not len(innovations) or float(np.std(innovations)) <= 1e-12:
        innovations = centered_residuals - centered_residuals.mean()
    rng = np.random.default_rng(seed)
    bootstrap_stats = np.empty(bootstrap_replicates, dtype=float)
    for iteration in range(bootstrap_replicates):
        errors = np.empty(n, dtype=float)
        errors[0] = rng.choice(centered_residuals)
        innovations_draw = rng.choice(innovations, size=n - 1, replace=True)
        for index, innovation in enumerate(innovations_draw, start=1):
            errors[index] = rho ** gaps_in_years[index - 1] * errors[index - 1] + innovation
        bootstrap_stats[iteration], _ = _sup_f_statistic(x, fitted + errors, minimum_segment)
    p_value = (1 + int(np.count_nonzero(bootstrap_stats >= observed_statistic))) / (bootstrap_replicates + 1)
    return {
        "year": int(years[split]),
        "sup_f": observed_statistic,
        "p_value": p_value,
        "critical_95": float(np.quantile(bootstrap_stats, .95)),
        "rho": rho,
        "observations": n,
        "replicates": bootstrap_replicates,
        "reason": None,
    }
