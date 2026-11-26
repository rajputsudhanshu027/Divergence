import numpy as np
import pandas as pd

from analysis import bootstrap_peer_stability, supf_break_test


def test_supf_bootstrap_detects_large_level_and_slope_change():
    rng = np.random.default_rng(23)
    years = np.arange(1980, 2020)
    trend = 0.15 * (years - 1980)
    post_break = years >= 2000
    values = trend + post_break * (7 + 0.35 * (years - 2000)) + rng.normal(0, 0.35, len(years))
    gaps = pd.DataFrame({"year": years, "Gap (% of peer mean)": values})

    result = supf_break_test(gaps, minimum_segment=6, bootstrap_replicates=199, seed=11)

    assert result["year"] in range(1997, 2004)
    assert result["p_value"] < 0.05
    assert result["replicates"] == 199


def test_supf_bootstrap_reports_when_series_is_too_short():
    gaps = pd.DataFrame({"year": range(2000, 2010), "Gap (% of peer mean)": range(10)})

    result = supf_break_test(gaps)

    assert result["p_value"] is None
    assert "12 observed years" in result["reason"]


def test_peer_set_resampling_is_reproducible_and_reports_jaccard():
    rows = []
    values = {
        "Selected": (10, 10), "Peer A": (11, 10), "Peer B": (10, 11),
        "Peer C": (12, 12), "Peer D": (16, 17), "Peer E": (18, 16),
    }
    for country, pair in values.items():
        for year in (1999, 2000, 2001):
            rows.extend([
                {"country": country, "feature": "income", "year": year, "value": pair[0] + (year - 2000) * .01},
                {"country": country, "feature": "urban", "year": year, "value": pair[1] + (year - 2000) * .01},
            ])
    data = pd.DataFrame(rows)

    first = bootstrap_peer_stability(data, "Selected", 2, "Z-score", 2000, ["income", "urban"], replicates=99, seed=4)
    second = bootstrap_peer_stability(data, "Selected", 2, "Z-score", 2000, ["income", "urban"], replicates=99, seed=4)

    assert first["valid_replicates"] == 99
    assert 0 <= first["mean_jaccard"] <= 1
    assert first["frequencies"] == second["frequencies"]
    assert first["mean_jaccard"] == second["mean_jaccard"]
