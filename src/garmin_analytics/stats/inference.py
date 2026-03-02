from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu, spearmanr


def _clean_1d(values: Sequence[float] | pd.Series | np.ndarray) -> np.ndarray:
    series = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    return series.to_numpy(dtype=float)


def _clean_paired(
    x: Sequence[float] | pd.Series | np.ndarray,
    y: Sequence[float] | pd.Series | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    frame = pd.DataFrame({"x": pd.Series(x), "y": pd.Series(y)})
    frame["x"] = pd.to_numeric(frame["x"], errors="coerce")
    frame["y"] = pd.to_numeric(frame["y"], errors="coerce")
    frame = frame.dropna(subset=["x", "y"])
    return frame["x"].to_numpy(dtype=float), frame["y"].to_numpy(dtype=float)


def _bootstrap_ci_from_estimates(
    estimates: np.ndarray,
    *,
    confidence_level: float,
) -> tuple[float, float]:
    alpha = 1.0 - confidence_level
    low = float(np.quantile(estimates, alpha / 2.0))
    high = float(np.quantile(estimates, 1.0 - alpha / 2.0))
    return low, high


def cliffs_delta(
    x: Sequence[float] | pd.Series | np.ndarray,
    y: Sequence[float] | pd.Series | np.ndarray,
) -> float:
    """Return Cliff's delta for two independent samples."""
    x_arr = _clean_1d(x)
    y_arr = _clean_1d(y)
    if len(x_arr) == 0 or len(y_arr) == 0:
        return np.nan
    diff = x_arr[:, None] - y_arr[None, :]
    greater = float(np.sum(diff > 0))
    lower = float(np.sum(diff < 0))
    return (greater - lower) / float(len(x_arr) * len(y_arr))


def bootstrap_median_difference(
    x: Sequence[float] | pd.Series | np.ndarray,
    y: Sequence[float] | pd.Series | np.ndarray,
    *,
    confidence_level: float = 0.95,
    n_boot: int = 4000,
    random_state: int = 42,
) -> dict[str, float]:
    """Bootstrap CI for median(x) - median(y) on two independent samples."""
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")
    if n_boot < 100:
        raise ValueError("n_boot must be at least 100")

    x_arr = _clean_1d(x)
    y_arr = _clean_1d(y)
    if len(x_arr) == 0 or len(y_arr) == 0:
        raise ValueError("Both samples must contain at least one numeric value")

    rng = np.random.default_rng(random_state)
    estimates = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        x_boot = rng.choice(x_arr, size=len(x_arr), replace=True)
        y_boot = rng.choice(y_arr, size=len(y_arr), replace=True)
        estimates[i] = float(np.median(x_boot) - np.median(y_boot))

    ci_low, ci_high = _bootstrap_ci_from_estimates(estimates, confidence_level=confidence_level)
    observed = float(np.median(x_arr) - np.median(y_arr))
    return {
        "n_x": int(len(x_arr)),
        "n_y": int(len(y_arr)),
        "median_x": float(np.median(x_arr)),
        "median_y": float(np.median(y_arr)),
        "median_diff": observed,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "confidence_level": float(confidence_level),
    }


def mann_whitney_summary(
    x: Sequence[float] | pd.Series | np.ndarray,
    y: Sequence[float] | pd.Series | np.ndarray,
    *,
    alternative: str = "two-sided",
    confidence_level: float = 0.95,
    n_boot: int = 4000,
    random_state: int = 42,
) -> dict[str, float | str]:
    """Return a compact Mann-Whitney summary with effect size and median-diff CI."""
    x_arr = _clean_1d(x)
    y_arr = _clean_1d(y)
    if len(x_arr) == 0 or len(y_arr) == 0:
        raise ValueError("Both samples must contain at least one numeric value")

    test = mannwhitneyu(x_arr, y_arr, alternative=alternative, method="auto")
    median_diff = bootstrap_median_difference(
        x_arr,
        y_arr,
        confidence_level=confidence_level,
        n_boot=n_boot,
        random_state=random_state,
    )
    return {
        "test": "mannwhitneyu",
        "alternative": alternative,
        "n_x": int(len(x_arr)),
        "n_y": int(len(y_arr)),
        "median_x": float(np.median(x_arr)),
        "median_y": float(np.median(y_arr)),
        "median_diff": float(median_diff["median_diff"]),
        "median_diff_ci_low": float(median_diff["ci_low"]),
        "median_diff_ci_high": float(median_diff["ci_high"]),
        "statistic_u": float(test.statistic),
        "p_value": float(test.pvalue),
        "cliffs_delta": float(cliffs_delta(x_arr, y_arr)),
    }


def bootstrap_spearman_ci(
    x: Sequence[float] | pd.Series | np.ndarray,
    y: Sequence[float] | pd.Series | np.ndarray,
    *,
    confidence_level: float = 0.95,
    n_boot: int = 4000,
    random_state: int = 42,
) -> dict[str, float]:
    """Bootstrap CI for Spearman rho on paired data."""
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")
    if n_boot < 100:
        raise ValueError("n_boot must be at least 100")

    x_arr, y_arr = _clean_paired(x, y)
    if len(x_arr) < 3:
        raise ValueError("Need at least 3 paired observations for bootstrap Spearman CI")

    observed = float(spearmanr(x_arr, y_arr).statistic)
    rng = np.random.default_rng(random_state)
    estimates: list[float] = []
    idx = np.arange(len(x_arr))
    max_attempts = max(n_boot * 5, 1000)
    attempts = 0
    while len(estimates) < n_boot and attempts < max_attempts:
        attempts += 1
        boot_idx = rng.choice(idx, size=len(idx), replace=True)
        x_boot = x_arr[boot_idx]
        y_boot = y_arr[boot_idx]
        if np.all(x_boot == x_boot[0]) or np.all(y_boot == y_boot[0]):
            continue
        estimate = float(spearmanr(x_boot, y_boot).statistic)
        if not np.isnan(estimate):
            estimates.append(estimate)

    if len(estimates) < max(100, int(n_boot * 0.8)):
        raise ValueError("Could not generate enough non-degenerate bootstrap Spearman samples")

    estimate_arr = np.asarray(estimates, dtype=float)
    ci_low, ci_high = _bootstrap_ci_from_estimates(estimate_arr, confidence_level=confidence_level)
    return {
        "n": int(len(x_arr)),
        "rho": observed,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "confidence_level": float(confidence_level),
    }


def spearman_summary(
    x: Sequence[float] | pd.Series | np.ndarray,
    y: Sequence[float] | pd.Series | np.ndarray,
    *,
    alternative: str = "two-sided",
    confidence_level: float = 0.95,
    n_boot: int = 4000,
    random_state: int = 42,
) -> dict[str, float | str]:
    """Return Spearman rho with p-value and bootstrap CI."""
    x_arr, y_arr = _clean_paired(x, y)
    if len(x_arr) < 3:
        raise ValueError("Need at least 3 paired observations for Spearman correlation")

    test = spearmanr(x_arr, y_arr, alternative=alternative)
    ci = bootstrap_spearman_ci(
        x_arr,
        y_arr,
        confidence_level=confidence_level,
        n_boot=n_boot,
        random_state=random_state,
    )
    return {
        "test": "spearmanr",
        "alternative": alternative,
        "n": int(len(x_arr)),
        "rho": float(test.statistic),
        "p_value": float(test.pvalue),
        "rho_ci_low": float(ci["ci_low"]),
        "rho_ci_high": float(ci["ci_high"]),
    }


def kruskal_summary(groups: Mapping[str, Sequence[float] | pd.Series | np.ndarray]) -> dict[str, float | str]:
    """Return a compact Kruskal-Wallis summary for multiple groups."""
    cleaned: dict[str, np.ndarray] = {name: _clean_1d(values) for name, values in groups.items()}
    cleaned = {name: values for name, values in cleaned.items() if len(values) > 0}
    if len(cleaned) < 2:
        raise ValueError("Need at least two non-empty groups for Kruskal-Wallis")

    stat = kruskal(*cleaned.values(), nan_policy="omit")
    out: dict[str, float | str] = {
        "test": "kruskal",
        "group_count": int(len(cleaned)),
        "statistic_h": float(stat.statistic),
        "p_value": float(stat.pvalue),
    }
    for name, values in cleaned.items():
        key = name.replace(" ", "_")
        out[f"n_{key}"] = int(len(values))
        out[f"median_{key}"] = float(np.median(values))
    return out
