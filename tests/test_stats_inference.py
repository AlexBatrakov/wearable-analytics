from __future__ import annotations

import pandas as pd

from garmin_analytics.stats.inference import (
    bootstrap_median_difference,
    bootstrap_spearman_ci,
    cliffs_delta,
    kruskal_summary,
    mann_whitney_summary,
    spearman_summary,
)


def test_cliffs_delta_detects_complete_separation() -> None:
    delta = cliffs_delta([5, 6, 7], [1, 2, 3])
    assert delta == 1.0


def test_bootstrap_median_difference_returns_expected_direction() -> None:
    out = bootstrap_median_difference([10, 11, 12], [1, 2, 3], n_boot=500, random_state=1)

    assert out["median_x"] == 11.0
    assert out["median_y"] == 2.0
    assert out["median_diff"] == 9.0
    assert out["ci_low"] > 0


def test_mann_whitney_summary_reports_effect_size() -> None:
    out = mann_whitney_summary([10, 11, 12], [1, 2, 3], alternative="greater", n_boot=500, random_state=1)

    assert out["test"] == "mannwhitneyu"
    assert out["p_value"] < 0.1
    assert out["cliffs_delta"] > 0.9
    assert out["median_diff"] > 0


def test_spearman_summary_detects_positive_monotonic_relation() -> None:
    out = spearman_summary([1, 2, 3, 4, 5], [10, 20, 30, 40, 50], n_boot=500, random_state=1)

    assert out["test"] == "spearmanr"
    assert out["rho"] > 0.99
    assert out["rho_ci_low"] > 0.9


def test_bootstrap_spearman_ci_returns_interval() -> None:
    out = bootstrap_spearman_ci([1, 2, 3, 4, 5], [5, 4, 3, 2, 1], n_boot=500, random_state=1)

    assert out["rho"] < -0.99
    assert out["ci_high"] < 0


def test_kruskal_summary_reports_group_medians() -> None:
    out = kruskal_summary(
        {
            "sat": pd.Series([8, 9, 10]),
            "sun": pd.Series([1, 2, 3]),
            "midweek": pd.Series([4, 5, 6]),
        }
    )

    assert out["test"] == "kruskal"
    assert out["group_count"] == 3
    assert out["median_sat"] == 9.0
    assert out["median_sun"] == 2.0
