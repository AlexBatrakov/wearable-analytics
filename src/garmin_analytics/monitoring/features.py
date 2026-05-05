from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .foundation import (
    SEMANTIC_WINDOW_COLUMNS,
    build_monitoring_daily_features,
    normalize_heart_rate_frame,
    normalize_stress_frame,
)


CATALOG_COLUMNS = [
    "column",
    "family",
    "signal",
    "phase",
    "window",
    "metric",
    "description",
    "unit",
    "dtype",
    "non_null_count",
    "non_null_pct",
    "missing_count",
    "missing_pct",
    "n_unique",
    "is_all_null",
    "is_constant_non_null",
    "is_mostly_missing",
    "is_sparse_or_rare",
    "zero_pct",
    "min",
    "p05",
    "p25",
    "median",
    "p75",
    "p95",
    "max",
    "mean",
    "std",
    "example_values",
    "analysis_role",
    "recommended_for_eda",
    "candidate_model_feature",
    "caution",
]


@dataclass(frozen=True)
class MonitoringFeaturesFullConfig:
    """Configuration for the wide monitoring feature table."""

    max_hr_bpm: float = 192.0
    gap_break_minutes: float = 2.0
    min_valid_minutes: int = 5
    min_paired_minutes: int = 10
    min_sleep_duration_hours: float = 2.0
    max_sleep_duration_hours: float = 16.0
    min_wake_duration_hours: float = 6.0
    max_wake_duration_hours: float = 30.0
    boundary_gap_tolerance_minutes: float = 60.0
    endpoint_band_minutes: float = 30.0
    endpoint_search_horizon_minutes: float = 90.0


PHASES = ("sleep", "wake")
SIGNALS = ("hr", "stress")
STRESS_STATE_COLUMNS = (
    "resting",
    "resting_0_25",
    "low",
    "low_26_50",
    "medium",
    "medium_51_75",
    "high",
    "high_76_100",
    "active",
)
HR_ZONE_COLUMNS = (
    "below_zone1",
    "zone1",
    "zone1_50_60",
    "zone2",
    "zone2_60_70",
    "zone3",
    "zone3_70_80",
    "zone4",
    "zone4_80_90",
    "zone5",
    "zone5_90_100",
    "above_mhr",
)
SEMANTIC_WINDOW_QUALITY_COLUMNS = {
    "semantic_day_duration_hours",
    "sleep_duration_plausible",
    "wake_duration_plausible",
    "semantic_day_duration_plausible",
    "semantic_window_plausible",
    "sleep_duration_outlier",
    "wake_duration_outlier",
    "wake_duration_gt_24h",
    "wake_duration_gt_30h",
    "wake_duration_gt_48h",
}


FEATURE_FAMILY_ORDER = [
    "identity/window metadata",
    "semantic window quality",
    "foundation coverage",
    "distribution/shape",
    "stress state fractions",
    "HR MHR zones",
    "variability/gaps",
    "missingness/coverage",
    "episodes/state structure",
    "recovery/deactivation",
    "relative windows",
    "anchored windows",
    "trends",
    "sleep-wake contrast",
    "HR/stress coupling",
    "raw stress status",
    "other",
]


def _indexed_by_timestamp(df: pd.DataFrame, timestamp_col: str = "timestamp_utc") -> pd.DataFrame:
    out = df.copy()
    out[timestamp_col] = pd.to_datetime(out[timestamp_col], errors="coerce", utc=True)
    out = out.dropna(subset=[timestamp_col]).sort_values(timestamp_col)
    return out.set_index(timestamp_col, drop=False)


def _time_slice(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if df.empty or pd.isna(start) or pd.isna(end) or start >= end:
        return df.iloc[0:0].copy()
    subset = df.loc[start:end]
    if subset.empty:
        return subset.copy()
    return subset.loc[(subset.index >= start) & (subset.index < end)].copy()


def _sort_by_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    out = df.reset_index(drop=True).copy()
    out["timestamp_utc"] = pd.to_datetime(out["timestamp_utc"], errors="coerce", utc=True)
    return out.dropna(subset=["timestamp_utc"]).sort_values("timestamp_utc").reset_index(drop=True)


def _duration_minutes(start: pd.Timestamp, end: pd.Timestamp) -> float:
    if pd.isna(start) or pd.isna(end) or start >= end:
        return 0.0
    return float((end - start).total_seconds() / 60.0)


def _coverage_fraction(valid_count: int, start: pd.Timestamp, end: pd.Timestamp) -> float:
    expected = _duration_minutes(start, end)
    if expected <= 0:
        return np.nan
    return float(min(valid_count / expected, 1.0))


def _flag(value: bool) -> int:
    return int(bool(value))


def _semantic_window_quality_features(
    sleep_duration_hours: float,
    wake_duration_hours: float,
    config: MonitoringFeaturesFullConfig,
) -> dict[str, float | int]:
    semantic_day_duration_hours = float(sleep_duration_hours) + float(wake_duration_hours)
    sleep_plausible = (
        config.min_sleep_duration_hours
        <= float(sleep_duration_hours)
        <= config.max_sleep_duration_hours
    )
    wake_plausible = (
        config.min_wake_duration_hours
        <= float(wake_duration_hours)
        <= config.max_wake_duration_hours
    )
    semantic_day_plausible = (
        (config.min_sleep_duration_hours + config.min_wake_duration_hours)
        <= semantic_day_duration_hours
        <= (config.max_sleep_duration_hours + config.max_wake_duration_hours)
    )
    return {
        "semantic_day_duration_hours": semantic_day_duration_hours,
        "sleep_duration_plausible": _flag(sleep_plausible),
        "wake_duration_plausible": _flag(wake_plausible),
        "semantic_day_duration_plausible": _flag(semantic_day_plausible),
        "semantic_window_plausible": _flag(sleep_plausible and wake_plausible and semantic_day_plausible),
        "sleep_duration_outlier": _flag(not sleep_plausible),
        "wake_duration_outlier": _flag(not wake_plausible),
        "wake_duration_gt_24h": _flag(float(wake_duration_hours) > 24.0),
        "wake_duration_gt_30h": _flag(float(wake_duration_hours) > 30.0),
        "wake_duration_gt_48h": _flag(float(wake_duration_hours) > 48.0),
    }


def _nan_record(prefix: str, suffixes: list[str]) -> dict[str, float]:
    return {f"{prefix}_{suffix}": np.nan for suffix in suffixes}


def _numeric_values(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").dropna().astype(float)


def _trimmed_mean(values: pd.Series, proportion: float = 0.10) -> float:
    if values.empty:
        return np.nan
    sorted_values = values.sort_values(ignore_index=True)
    trim = int(np.floor(len(sorted_values) * proportion))
    if trim > 0 and len(sorted_values) > 2 * trim:
        sorted_values = sorted_values.iloc[trim:-trim]
    return float(sorted_values.mean())


def _entropy_from_counts(counts: pd.Series | np.ndarray) -> float:
    counts_array = np.asarray(counts, dtype=float)
    positive = counts_array[counts_array > 0]
    if positive.size == 0:
        return np.nan
    probabilities = positive / positive.sum()
    return float(-(probabilities * np.log2(probabilities)).sum())


def _categorical_entropy(labels: pd.Series, categories: tuple[str, ...]) -> float:
    if labels.empty:
        return np.nan
    counts = labels.value_counts().reindex(categories, fill_value=0)
    return _entropy_from_counts(counts.to_numpy(dtype=float))


def _stress_histogram_entropy(values: pd.Series) -> float:
    """Entropy over fixed Garmin-like stress-state bins across the 0..100 scale."""
    numeric = _numeric_values(values)
    if numeric.empty:
        return np.nan
    labels = numeric.map(_stress_state).dropna()
    return _categorical_entropy(labels, STRESS_STATE_COLUMNS)


def _hr_histogram_entropy(values: pd.Series, max_hr_bpm: float) -> float:
    """Entropy over fixed MHR-zone bins derived from the configured max HR."""
    numeric = _numeric_values(values)
    if numeric.empty:
        return np.nan
    labels = numeric.map(lambda value: _hr_zone(value, max_hr_bpm)).dropna()
    return _categorical_entropy(labels, HR_ZONE_COLUMNS)


def _histogram_entropy(values: pd.Series, *, signal: str, max_hr_bpm: float) -> float:
    if values.empty:
        return np.nan
    if signal == "hr":
        return _hr_histogram_entropy(values, max_hr_bpm)
    if signal == "stress":
        return _stress_histogram_entropy(values)
    raise ValueError(f"Unsupported entropy signal: {signal}")


def _shape_stats(values: pd.Series, prefix: str, *, signal: str, max_hr_bpm: float) -> dict[str, float]:
    numeric = _numeric_values(values)
    suffixes = [
        "min",
        "max",
        "p05",
        "p10",
        "p25",
        "p95",
        "iqr",
        "range",
        "trimmed_mean",
        "mad",
        "skewness",
        "kurtosis",
        "histogram_entropy",
        "coefficient_of_variation",
    ]
    record = _nan_record(prefix, suffixes)
    if numeric.empty:
        return record

    p25 = float(numeric.quantile(0.25))
    p75 = float(numeric.quantile(0.75))
    mean = float(numeric.mean())
    std = float(numeric.std(ddof=0))
    median = float(numeric.median())
    minimum = float(numeric.min())
    maximum = float(numeric.max())
    record.update(
        {
            f"{prefix}_min": minimum,
            f"{prefix}_max": maximum,
            f"{prefix}_p05": float(numeric.quantile(0.05)),
            f"{prefix}_p10": float(numeric.quantile(0.10)),
            f"{prefix}_p25": p25,
            f"{prefix}_p95": float(numeric.quantile(0.95)),
            f"{prefix}_iqr": p75 - p25,
            f"{prefix}_range": maximum - minimum,
            f"{prefix}_trimmed_mean": _trimmed_mean(numeric),
            f"{prefix}_mad": float((numeric - median).abs().median()),
            f"{prefix}_histogram_entropy": _histogram_entropy(
                numeric,
                signal=signal,
                max_hr_bpm=max_hr_bpm,
            ),
            f"{prefix}_coefficient_of_variation": std / mean if mean != 0 else np.nan,
        }
    )
    if len(numeric) >= 3:
        record[f"{prefix}_skewness"] = float(numeric.skew())
    if len(numeric) >= 4:
        record[f"{prefix}_kurtosis"] = float(numeric.kurt())
    return record


def _stress_state(value: float) -> str | None:
    if 0 <= value <= 25:
        return "resting_0_25"
    if 26 <= value <= 50:
        return "low_26_50"
    if 51 <= value <= 75:
        return "medium_51_75"
    if 76 <= value <= 100:
        return "high_76_100"
    return None


def _stress_state_features(values: pd.Series, prefix: str) -> dict[str, float]:
    numeric = _numeric_values(values)
    record = {f"{prefix}_frac_{state}": np.nan for state in STRESS_STATE_COLUMNS}
    record[f"{prefix}_frac_medium_or_high_51_100"] = np.nan
    if numeric.empty:
        return record

    states = numeric.map(_stress_state)
    denominator = len(numeric)
    for state in STRESS_STATE_COLUMNS:
        record[f"{prefix}_frac_{state}"] = float((states == state).sum() / denominator)
    record[f"{prefix}_frac_medium_or_high_51_100"] = float((numeric >= 51).sum() / denominator)
    return record


def _hr_zone(value: float, max_hr_bpm: float) -> str | None:
    if max_hr_bpm <= 0 or pd.isna(value):
        return None
    ratio = float(value) / float(max_hr_bpm)
    if ratio < 0.50:
        return "below_zone1"
    if ratio < 0.60:
        return "zone1_50_60"
    if ratio < 0.70:
        return "zone2_60_70"
    if ratio < 0.80:
        return "zone3_70_80"
    if ratio < 0.90:
        return "zone4_80_90"
    if ratio <= 1.00:
        return "zone5_90_100"
    return "above_mhr"


def _hr_zone_features(values: pd.Series, prefix: str, max_hr_bpm: float) -> dict[str, float]:
    numeric = _numeric_values(values)
    record = {f"{prefix}_frac_{zone}": np.nan for zone in HR_ZONE_COLUMNS}
    record[f"{prefix}_frac_zone1_plus"] = np.nan
    record[f"{prefix}_frac_zone2_plus"] = np.nan
    record[f"{prefix}_frac_zone3_plus"] = np.nan
    if numeric.empty:
        return record

    zones = numeric.map(lambda value: _hr_zone(value, max_hr_bpm))
    denominator = len(numeric)
    for zone in HR_ZONE_COLUMNS:
        record[f"{prefix}_frac_{zone}"] = float((zones == zone).sum() / denominator)
    record[f"{prefix}_frac_zone1_plus"] = float((numeric >= 0.50 * max_hr_bpm).sum() / denominator)
    record[f"{prefix}_frac_zone2_plus"] = float((numeric >= 0.60 * max_hr_bpm).sum() / denominator)
    record[f"{prefix}_frac_zone3_plus"] = float((numeric >= 0.70 * max_hr_bpm).sum() / denominator)
    return record


def _diff_features(
    values_df: pd.DataFrame,
    value_col: str,
    prefix: str,
    gap_break_minutes: float,
) -> dict[str, float | int]:
    suffixes = [
        "mean_abs_diff",
        "median_abs_diff",
        "std_diff",
        "max_abs_jump",
        "roughness",
    ]
    record: dict[str, float | int] = {
        f"{prefix}_diff_valid_pair_count": 0,
        f"{prefix}_diff_gap_break_count": 0,
        f"{prefix}_longest_observed_gap_minutes": np.nan,
    }
    record.update(_nan_record(prefix, suffixes))

    valid = _sort_by_timestamp(values_df.dropna(subset=[value_col]))
    if len(valid) < 2:
        return record

    timestamps = pd.to_datetime(valid["timestamp_utc"], errors="coerce", utc=True)
    numeric = pd.to_numeric(valid[value_col], errors="coerce")
    gaps = timestamps.diff().dt.total_seconds() / 60.0
    diffs = numeric.diff()
    eligible = gaps <= gap_break_minutes
    eligible.iloc[0] = False
    valid_diffs = diffs.loc[eligible].dropna().astype(float)

    positive_gaps = gaps.dropna()
    record[f"{prefix}_diff_valid_pair_count"] = int(len(valid_diffs))
    record[f"{prefix}_diff_gap_break_count"] = int((positive_gaps > gap_break_minutes).sum())
    record[f"{prefix}_longest_observed_gap_minutes"] = (
        float(positive_gaps.max()) if not positive_gaps.empty else np.nan
    )
    if valid_diffs.empty:
        return record

    abs_diffs = valid_diffs.abs()
    record.update(
        {
            f"{prefix}_mean_abs_diff": float(abs_diffs.mean()),
            f"{prefix}_median_abs_diff": float(abs_diffs.median()),
            f"{prefix}_std_diff": float(valid_diffs.std(ddof=0)),
            f"{prefix}_max_abs_jump": float(abs_diffs.max()),
            f"{prefix}_roughness": float((valid_diffs**2).mean()),
        }
    )
    return record


def _missing_gap_features(
    timestamps: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
    prefix: str,
    gap_break_minutes: float,
) -> dict[str, float | int]:
    record: dict[str, float | int] = {
        f"{prefix}_longest_missing_gap_minutes": np.nan,
        f"{prefix}_missing_gap_count": 0,
        f"{prefix}_small_gap_count": 0,
        f"{prefix}_large_gap_count": 0,
    }
    duration = _duration_minutes(start, end)
    if duration <= 0:
        return record

    valid_ts = (
        pd.to_datetime(timestamps, errors="coerce", utc=True)
        .dropna()
        .drop_duplicates()
        .sort_values()
    )
    if valid_ts.empty:
        record[f"{prefix}_longest_missing_gap_minutes"] = float(duration)
        record[f"{prefix}_missing_gap_count"] = 1
        record[f"{prefix}_large_gap_count"] = 1 if duration > gap_break_minutes else 0
        record[f"{prefix}_small_gap_count"] = 1 if duration <= gap_break_minutes else 0
        return record

    missing_lengths: list[float] = []
    first_gap = np.floor(_duration_minutes(start, valid_ts.iloc[0]))
    if first_gap > 0:
        missing_lengths.append(float(first_gap))

    for previous, current in zip(valid_ts.iloc[:-1], valid_ts.iloc[1:], strict=False):
        gap = np.floor(_duration_minutes(previous, current)) - 1.0
        if gap > 0:
            missing_lengths.append(float(gap))

    trailing_gap = np.floor(_duration_minutes(valid_ts.iloc[-1], end)) - 1.0
    if trailing_gap > 0:
        missing_lengths.append(float(trailing_gap))

    if not missing_lengths:
        record[f"{prefix}_longest_missing_gap_minutes"] = 0.0
        return record

    record[f"{prefix}_longest_missing_gap_minutes"] = float(max(missing_lengths))
    record[f"{prefix}_missing_gap_count"] = len(missing_lengths)
    record[f"{prefix}_small_gap_count"] = int(sum(0 < gap <= gap_break_minutes for gap in missing_lengths))
    record[f"{prefix}_large_gap_count"] = int(sum(gap > gap_break_minutes for gap in missing_lengths))
    return record


def _boundary_coverage_features(
    valid: pd.DataFrame,
    value_col: str,
    phase: str,
    signal: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    boundary_gap_tolerance_minutes: float,
) -> dict[str, float | int]:
    prefix = f"{phase}_{signal}"
    record: dict[str, float | int] = {
        f"{prefix}_minutes_to_first_valid": np.nan,
        f"{prefix}_minutes_from_last_valid_to_end": np.nan,
        f"{prefix}_start_boundary_covered": 0,
        f"{prefix}_end_boundary_covered": 0,
    }
    ordered = _sort_by_timestamp(valid.dropna(subset=[value_col]))
    if ordered.empty:
        return record
    first_ts = pd.Timestamp(ordered.iloc[0]["timestamp_utc"])
    last_ts = pd.Timestamp(ordered.iloc[-1]["timestamp_utc"])
    minutes_to_first = _duration_minutes(start, first_ts)
    minutes_from_last = _duration_minutes(last_ts, end)
    record[f"{prefix}_minutes_to_first_valid"] = minutes_to_first
    record[f"{prefix}_minutes_from_last_valid_to_end"] = minutes_from_last
    record[f"{prefix}_start_boundary_covered"] = _flag(minutes_to_first <= boundary_gap_tolerance_minutes)
    record[f"{prefix}_end_boundary_covered"] = _flag(minutes_from_last <= boundary_gap_tolerance_minutes)
    return record


def _run_lengths(
    timestamps: pd.Series,
    labels: pd.Series,
    target_labels: set[str],
    gap_break_minutes: float,
) -> list[tuple[pd.Timestamp, pd.Timestamp, int]]:
    runs: list[tuple[pd.Timestamp, pd.Timestamp, int]] = []
    current_start: pd.Timestamp | None = None
    current_end: pd.Timestamp | None = None
    current_count = 0
    previous_ts: pd.Timestamp | None = None

    for ts, label in zip(timestamps, labels, strict=False):
        if pd.isna(ts):
            continue
        ts = pd.Timestamp(ts)
        is_target = label in target_labels
        gap_break = (
            previous_ts is not None
            and _duration_minutes(previous_ts, ts) > gap_break_minutes
        )
        if gap_break and current_start is not None and current_end is not None:
            runs.append((current_start, current_end, current_count))
            current_start = None
            current_end = None
            current_count = 0

        if is_target:
            if current_start is None:
                current_start = ts
                current_count = 0
            current_end = ts
            current_count += 1
        elif current_start is not None and current_end is not None:
            runs.append((current_start, current_end, current_count))
            current_start = None
            current_end = None
            current_count = 0

        previous_ts = ts

    if current_start is not None and current_end is not None:
        runs.append((current_start, current_end, current_count))
    return runs


def _episode_stats(
    timestamps: pd.Series,
    labels: pd.Series,
    target_labels: set[str],
    start: pd.Timestamp,
    end: pd.Timestamp,
    prefix: str,
    gap_break_minutes: float,
) -> dict[str, float | int]:
    runs = _run_lengths(timestamps, labels, target_labels, gap_break_minutes)
    record: dict[str, float | int] = {
        f"{prefix}_episode_count": len(runs),
        f"{prefix}_total_minutes": int(sum(run[2] for run in runs)),
        f"{prefix}_has_event": _flag(bool(runs)),
        f"{prefix}_mean_duration_minutes": 0.0,
        f"{prefix}_median_duration_minutes": 0.0,
        f"{prefix}_max_duration_minutes": 0.0,
        f"{prefix}_time_to_first_minutes": np.nan,
        f"{prefix}_time_since_last_minutes": np.nan,
        f"{prefix}_fragmentation_index": 0.0,
    }
    if not runs:
        return record

    durations = pd.Series([run[2] for run in runs], dtype=float)
    total = float(durations.sum())
    first_ts = runs[0][0]
    last_ts = runs[-1][1]
    record.update(
        {
            f"{prefix}_mean_duration_minutes": float(durations.mean()),
            f"{prefix}_median_duration_minutes": float(durations.median()),
            f"{prefix}_max_duration_minutes": float(durations.max()),
            f"{prefix}_time_to_first_minutes": _duration_minutes(start, first_ts),
            f"{prefix}_time_since_last_minutes": _duration_minutes(last_ts, end),
            f"{prefix}_fragmentation_index": len(runs) / total if total > 0 else np.nan,
        }
    )
    return record


def _transition_features(
    timestamps: pd.Series,
    labels: pd.Series,
    valid_count: int,
    prefix: str,
    gap_break_minutes: float,
) -> dict[str, float | int]:
    transitions = 0
    previous_ts: pd.Timestamp | None = None
    previous_label: str | None = None
    for ts, label in zip(timestamps, labels, strict=False):
        if pd.isna(ts) or label is None:
            continue
        ts = pd.Timestamp(ts)
        if (
            previous_ts is not None
            and previous_label is not None
            and _duration_minutes(previous_ts, ts) <= gap_break_minutes
            and label != previous_label
        ):
            transitions += 1
        previous_ts = ts
        previous_label = label

    valid_hours = valid_count / 60.0
    return {
        f"{prefix}_state_transition_count": transitions,
        f"{prefix}_transitions_per_valid_hour": transitions / valid_hours if valid_hours > 0 else np.nan,
    }


def _stress_episode_features(
    valid: pd.DataFrame,
    phase: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    gap_break_minutes: float,
) -> dict[str, float | int]:
    timestamps = pd.to_datetime(valid["timestamp_utc"], errors="coerce", utc=True)
    labels = pd.to_numeric(valid["stress_level"], errors="coerce").map(_stress_state)
    record: dict[str, float | int] = {}
    record.update(
        _episode_stats(
            timestamps,
            labels,
            {"high_76_100"},
            start,
            end,
            f"{phase}_stress_high",
            gap_break_minutes,
        )
    )
    record.update(
        _episode_stats(
            timestamps,
            labels,
            {"medium_51_75", "high_76_100"},
            start,
            end,
            f"{phase}_stress_elevated",
            gap_break_minutes,
        )
    )
    record.update(_transition_features(timestamps, labels, len(valid), f"{phase}_stress", gap_break_minutes))
    low_runs = _run_lengths(timestamps, labels, {"low_26_50"}, gap_break_minutes)
    recovery_runs = _run_lengths(timestamps, labels, {"resting_0_25"}, gap_break_minutes)
    record[f"{phase}_stress_longest_low_episode_minutes"] = (
        float(max(run[2] for run in low_runs)) if low_runs else 0.0
    )
    record[f"{phase}_stress_longest_recovery_episode_minutes"] = (
        float(max(run[2] for run in recovery_runs)) if recovery_runs else 0.0
    )
    return record


def _hr_episode_features(
    valid: pd.DataFrame,
    phase: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    max_hr_bpm: float,
    gap_break_minutes: float,
) -> dict[str, float | int]:
    timestamps = pd.to_datetime(valid["timestamp_utc"], errors="coerce", utc=True)
    labels = pd.to_numeric(valid["heart_rate"], errors="coerce").map(
        lambda value: _hr_zone(value, max_hr_bpm)
    )
    record: dict[str, float | int] = {}
    record.update(
        _episode_stats(
            timestamps,
            labels,
            {
                "zone1_50_60",
                "zone2_60_70",
                "zone3_70_80",
                "zone4_80_90",
                "zone5_90_100",
                "above_mhr",
            },
            start,
            end,
            f"{phase}_hr_zone1_plus",
            gap_break_minutes,
        )
    )
    record.update(
        _episode_stats(
            timestamps,
            labels,
            {"zone2_60_70", "zone3_70_80", "zone4_80_90", "zone5_90_100", "above_mhr"},
            start,
            end,
            f"{phase}_hr_zone2_plus",
            gap_break_minutes,
        )
    )
    record.update(_transition_features(timestamps, labels, len(valid), f"{phase}_hr", gap_break_minutes))
    recovery_runs = _run_lengths(timestamps, labels, {"below_zone1"}, gap_break_minutes)
    record[f"{phase}_hr_longest_below_zone1_episode_minutes"] = (
        float(max(run[2] for run in recovery_runs)) if recovery_runs else 0.0
    )
    return record


def _window_signal_stats(
    valid: pd.DataFrame,
    value_col: str,
    prefix: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    min_valid_minutes: int,
) -> dict[str, float | int]:
    numeric = _numeric_values(valid[value_col] if value_col in valid.columns else pd.Series(dtype=float))
    record: dict[str, float | int] = {
        f"{prefix}_valid_count": int(len(numeric)),
        f"{prefix}_coverage_fraction": _coverage_fraction(len(numeric), start, end),
        f"{prefix}_mean": np.nan,
        f"{prefix}_std": np.nan,
        f"{prefix}_p90": np.nan,
    }
    if len(numeric) < min_valid_minutes:
        return record
    record.update(
        {
            f"{prefix}_mean": float(numeric.mean()),
            f"{prefix}_std": float(numeric.std(ddof=0)),
            f"{prefix}_p90": float(numeric.quantile(0.90)),
        }
    )
    return record


def _window_stress_raw_status_features(stress_subset: pd.DataFrame, window_prefix: str) -> dict[str, float]:
    raw = pd.to_numeric(
        stress_subset["stress_level_raw"] if "stress_level_raw" in stress_subset.columns else pd.Series(dtype=float),
        errors="coerce",
    )
    total = int(raw.notna().sum())
    if total == 0:
        return {
            f"{window_prefix}_stress_raw_valid_fraction": np.nan,
            f"{window_prefix}_stress_raw_minus_1_fraction": np.nan,
            f"{window_prefix}_stress_raw_minus_2_fraction": np.nan,
            f"{window_prefix}_stress_raw_negative_fraction": np.nan,
            f"{window_prefix}_stress_large_motion_proxy_fraction": np.nan,
        }
    return {
        f"{window_prefix}_stress_raw_valid_fraction": float(((raw >= 0) & (raw <= 100)).sum() / total),
        f"{window_prefix}_stress_raw_minus_1_fraction": float((raw == -1).sum() / total),
        f"{window_prefix}_stress_raw_minus_2_fraction": float((raw == -2).sum() / total),
        f"{window_prefix}_stress_raw_negative_fraction": float((raw < 0).sum() / total),
        f"{window_prefix}_stress_large_motion_proxy_fraction": float((raw == -2).sum() / total),
    }


def _window_features(
    window_prefix: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    hr: pd.DataFrame,
    stress: pd.DataFrame,
    min_valid_minutes: int,
) -> dict[str, float | int]:
    hr_subset = _time_slice(hr, start, end)
    stress_subset = _time_slice(stress, start, end)
    hr_valid = hr_subset.loc[hr_subset["heart_rate_status"] == "valid"]
    stress_valid = stress_subset.loc[stress_subset["stress_status"] == "valid"]

    record: dict[str, float | int] = {}
    record[f"{window_prefix}_duration_minutes"] = _duration_minutes(start, end)
    record.update(
        _window_signal_stats(
            hr_valid,
            "heart_rate",
            f"{window_prefix}_hr",
            start,
            end,
            min_valid_minutes,
        )
    )
    record.update(
        _window_signal_stats(
            stress_valid,
            "stress_level",
            f"{window_prefix}_stress",
            start,
            end,
            min_valid_minutes,
        )
    )
    stress_numeric = _numeric_values(stress_valid["stress_level"] if "stress_level" in stress_valid else pd.Series(dtype=float))
    if len(stress_numeric) >= min_valid_minutes:
        record[f"{window_prefix}_stress_medium_or_high_fraction"] = float((stress_numeric >= 51).sum() / len(stress_numeric))
        record[f"{window_prefix}_stress_high_fraction"] = float((stress_numeric >= 76).sum() / len(stress_numeric))
    else:
        record[f"{window_prefix}_stress_medium_or_high_fraction"] = np.nan
        record[f"{window_prefix}_stress_high_fraction"] = np.nan
    record.update(_window_stress_raw_status_features(stress_subset, window_prefix))
    return record


def _relative_window_features(
    phase: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    hr: pd.DataFrame,
    stress: pd.DataFrame,
    min_valid_minutes: int,
) -> dict[str, float | int]:
    record: dict[str, float | int] = {}
    duration = _duration_minutes(start, end)
    if duration <= 0:
        return record

    step = (end - start) / 4
    for idx in range(4):
        window_start = start + idx * step
        window_end = start + (idx + 1) * step
        record.update(
            _window_features(
                f"{phase}_q{idx + 1}",
                window_start,
                window_end,
                hr,
                stress,
                min_valid_minutes,
            )
        )
    return record


def _anchored_window_features(
    sleep_start: pd.Timestamp,
    sleep_end: pd.Timestamp,
    next_sleep_start: pd.Timestamp,
    hr: pd.DataFrame,
    stress: pd.DataFrame,
    min_valid_minutes: int,
) -> dict[str, float | int]:
    anchors = {
        "first_30m_after_wake": (
            sleep_end,
            min(sleep_end + pd.Timedelta(minutes=30), next_sleep_start),
        ),
        "first_2h_after_wake": (
            sleep_end,
            min(sleep_end + pd.Timedelta(hours=2), next_sleep_start),
        ),
        "last_2h_before_sleep": (
            max(sleep_end, next_sleep_start - pd.Timedelta(hours=2)),
            next_sleep_start,
        ),
        "last_4h_before_sleep": (
            max(sleep_end, next_sleep_start - pd.Timedelta(hours=4)),
            next_sleep_start,
        ),
        "first_60m_sleep": (
            sleep_start,
            min(sleep_start + pd.Timedelta(minutes=60), sleep_end),
        ),
        "last_60m_sleep": (
            max(sleep_start, sleep_end - pd.Timedelta(minutes=60)),
            sleep_end,
        ),
    }
    record: dict[str, float | int] = {}
    for prefix, (start, end) in anchors.items():
        record.update(_window_features(prefix, start, end, hr, stress, min_valid_minutes))
    return record


def _mean_in_window(
    df: pd.DataFrame,
    value_col: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    min_valid_minutes: int,
) -> float:
    subset = _time_slice(df, start, end)
    values = _numeric_values(subset[value_col] if value_col in subset.columns else pd.Series(dtype=float))
    if len(values) < min_valid_minutes:
        return np.nan
    return float(values.mean())


def _rolling_drop_from_start(
    df: pd.DataFrame,
    value_col: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    min_valid_minutes: int,
) -> float:
    subset = _sort_by_timestamp(_time_slice(df, start, end).dropna(subset=[value_col]))
    if len(subset) < min_valid_minutes:
        return np.nan
    start_mean = _mean_in_window(
        subset.set_index("timestamp_utc", drop=False),
        value_col,
        start,
        min(start + pd.Timedelta(minutes=30), end),
        min_valid_minutes,
    )
    rolling = (
        subset.set_index("timestamp_utc")[value_col]
        .astype(float)
        .rolling("30min", min_periods=min_valid_minutes)
        .mean()
        .dropna()
    )
    if pd.isna(start_mean) or rolling.empty:
        return np.nan
    return float(start_mean - rolling.min())


def _time_to_threshold(
    df: pd.DataFrame,
    value_col: str,
    start: pd.Timestamp,
    threshold: float,
) -> float:
    values = _sort_by_timestamp(df.dropna(subset=[value_col]))
    reached = values.loc[pd.to_numeric(values[value_col], errors="coerce") < threshold]
    if reached.empty:
        return np.nan
    return _duration_minutes(start, pd.Timestamp(reached.iloc[0]["timestamp_utc"]))


def _time_to_stable_low_stress(
    stress_valid: pd.DataFrame,
    start: pd.Timestamp,
    min_valid_minutes: int,
) -> float:
    if stress_valid.empty:
        return np.nan
    required = max(30, min_valid_minutes)
    indexed = stress_valid.dropna(subset=["stress_level"]).set_index("timestamp_utc").sort_index()
    if len(indexed) < required:
        return np.nan
    rolling_mean = indexed["stress_level"].astype(float).rolling("30min", min_periods=required).mean()
    stable = rolling_mean.loc[rolling_mean < 25].dropna()
    if stable.empty:
        return np.nan
    return _duration_minutes(start, pd.Timestamp(stable.index[0]))


def _sleep_recovery_features(
    sleep_start: pd.Timestamp,
    sleep_end: pd.Timestamp,
    hr: pd.DataFrame,
    stress: pd.DataFrame,
    min_valid_minutes: int,
) -> dict[str, float | int]:
    hr_sleep = _time_slice(hr, sleep_start, sleep_end)
    stress_sleep = _time_slice(stress, sleep_start, sleep_end)
    hr_valid = hr_sleep.loc[hr_sleep["heart_rate_status"] == "valid"]
    stress_valid = stress_sleep.loc[stress_sleep["stress_status"] == "valid"]

    first_60_end = min(sleep_start + pd.Timedelta(minutes=60), sleep_end)
    last_60_start = max(sleep_start, sleep_end - pd.Timedelta(minutes=60))
    q1_end = sleep_start + (sleep_end - sleep_start) / 4
    q4_start = sleep_start + 3 * (sleep_end - sleep_start) / 4

    record: dict[str, float | int] = {}
    for signal, frame, value_col in [
        ("hr", hr_valid, "heart_rate"),
        ("stress", stress_valid, "stress_level"),
    ]:
        indexed = frame.set_index("timestamp_utc", drop=False)
        first_60 = _mean_in_window(indexed, value_col, sleep_start, first_60_end, min_valid_minutes)
        last_60 = _mean_in_window(indexed, value_col, last_60_start, sleep_end, min_valid_minutes)
        q1 = _mean_in_window(indexed, value_col, sleep_start, q1_end, min_valid_minutes)
        q4 = _mean_in_window(indexed, value_col, q4_start, sleep_end, min_valid_minutes)
        record[f"sleep_{signal}_first_60m_mean"] = first_60
        record[f"sleep_{signal}_last_60m_mean"] = last_60
        record[f"sleep_{signal}_first_60m_minus_last_60m"] = (
            first_60 - last_60 if pd.notna(first_60) and pd.notna(last_60) else np.nan
        )
        record[f"sleep_{signal}_q1_mean"] = q1
        record[f"sleep_{signal}_q4_mean"] = q4
        record[f"sleep_{signal}_q1_minus_q4"] = q1 - q4 if pd.notna(q1) and pd.notna(q4) else np.nan
        record[f"sleep_{signal}_drop_from_start_to_min_rolling_30m"] = _rolling_drop_from_start(
            indexed,
            value_col,
            sleep_start,
            sleep_end,
            min_valid_minutes,
        )

    stress_indexed = stress_valid.set_index("timestamp_utc", drop=False)
    record["sleep_stress_time_to_low_stress_minutes"] = _time_to_threshold(
        stress_indexed,
        "stress_level",
        sleep_start,
        25,
    )
    record["sleep_stress_time_to_stable_low_stress_minutes"] = _time_to_stable_low_stress(
        stress_valid,
        sleep_start,
        min_valid_minutes,
    )
    return record


def _pre_sleep_features(
    wake_start: pd.Timestamp,
    next_sleep_start: pd.Timestamp,
    hr: pd.DataFrame,
    stress: pd.DataFrame,
    min_valid_minutes: int,
) -> dict[str, float | int]:
    pre2_start = max(wake_start, next_sleep_start - pd.Timedelta(hours=2))
    pre4_start = max(wake_start, next_sleep_start - pd.Timedelta(hours=4))
    first2_of_pre4_end = min(pre4_start + pd.Timedelta(hours=2), next_sleep_start)
    last1_start = max(wake_start, next_sleep_start - pd.Timedelta(hours=1))

    hr_valid = hr.loc[hr["heart_rate_status"] == "valid"].set_index("timestamp_utc", drop=False)
    stress_valid = stress.loc[stress["stress_status"] == "valid"].set_index("timestamp_utc", drop=False)
    record: dict[str, float | int] = {}
    for hours, start in [(2, pre2_start), (4, pre4_start)]:
        window_prefix = f"pre_sleep_{hours}h"
        stress_raw_subset = _time_slice(stress, start, next_sleep_start)
        record[f"{window_prefix}_duration_minutes"] = _duration_minutes(start, next_sleep_start)
        record[f"pre_sleep_{hours}h_hr_mean"] = _mean_in_window(
            hr_valid,
            "heart_rate",
            start,
            next_sleep_start,
            min_valid_minutes,
        )
        stress_subset = _time_slice(stress_valid, start, next_sleep_start)
        stress_values = _numeric_values(stress_subset["stress_level"] if "stress_level" in stress_subset else pd.Series(dtype=float))
        record[f"pre_sleep_{hours}h_stress_mean"] = (
            float(stress_values.mean()) if len(stress_values) >= min_valid_minutes else np.nan
        )
        record[f"pre_sleep_{hours}h_stress_high_fraction"] = (
            float((stress_values >= 76).sum() / len(stress_values))
            if len(stress_values) >= min_valid_minutes
            else np.nan
        )
        record.update(_window_stress_raw_status_features(stress_raw_subset, window_prefix))

    for signal, frame, value_col in [
        ("hr", hr_valid, "heart_rate"),
        ("stress", stress_valid, "stress_level"),
    ]:
        early = _mean_in_window(frame, value_col, pre4_start, first2_of_pre4_end, min_valid_minutes)
        late = _mean_in_window(frame, value_col, last1_start, next_sleep_start, min_valid_minutes)
        record[f"evening_deactivation_{signal}"] = (
            early - late if pd.notna(early) and pd.notna(late) else np.nan
        )
    return record


def _endpoint_band_summary(
    df: pd.DataFrame,
    value_col: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    side: str,
    band_minutes: float,
    search_horizon_minutes: float,
    min_valid_minutes: int,
) -> tuple[float, int, float]:
    duration = _duration_minutes(start, end)
    if duration <= 0:
        return np.nan, 0, np.nan

    band = min(float(band_minutes), duration)
    horizon = min(float(search_horizon_minutes), duration)
    max_offset = max(horizon - band, 0.0)
    offsets = range(0, int(np.floor(max_offset)) + 1)

    indexed = df.set_index("timestamp_utc", drop=False) if "timestamp_utc" in df.columns else df
    for offset in offsets:
        if side == "start":
            band_start = start + pd.Timedelta(minutes=offset)
            band_end = min(band_start + pd.Timedelta(minutes=band), end)
            reported_offset = float(offset)
        elif side == "end":
            band_end = end - pd.Timedelta(minutes=offset)
            band_start = max(start, band_end - pd.Timedelta(minutes=band))
            reported_offset = float(offset)
        else:
            raise ValueError("side must be 'start' or 'end'")

        subset = _time_slice(indexed, band_start, band_end)
        values = _numeric_values(subset[value_col] if value_col in subset.columns else pd.Series(dtype=float))
        if len(values) >= min_valid_minutes:
            return float(values.mean()), int(len(values)), reported_offset

    return np.nan, 0, np.nan


def _trend_features(
    df: pd.DataFrame,
    value_col: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    prefix: str,
    min_valid_minutes: int,
    endpoint_band_minutes: float,
    endpoint_search_horizon_minutes: float,
) -> dict[str, float]:
    record = {
        f"{prefix}_slope_per_hour": np.nan,
        f"{prefix}_trend_r2": np.nan,
        f"{prefix}_end_minus_start": np.nan,
        f"{prefix}_start_endpoint_valid_count": 0,
        f"{prefix}_end_endpoint_valid_count": 0,
        f"{prefix}_start_endpoint_offset_minutes": np.nan,
        f"{prefix}_end_endpoint_offset_minutes": np.nan,
        f"{prefix}_endpoint_contrast_defined": 0,
    }
    subset = _sort_by_timestamp(_time_slice(df, start, end).dropna(subset=[value_col]))
    if len(subset) < min_valid_minutes:
        return record

    x = (
        pd.to_datetime(subset["timestamp_utc"], errors="coerce", utc=True) - start
    ).dt.total_seconds().to_numpy(dtype=float) / 60.0
    y = pd.to_numeric(subset[value_col], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    if len(x) < min_valid_minutes or len(np.unique(x)) < 2:
        return record

    slope_per_minute, intercept = np.polyfit(x, y, 1)
    predicted = slope_per_minute * x + intercept
    total_ss = float(((y - y.mean()) ** 2).sum())
    residual_ss = float(((y - predicted) ** 2).sum())
    indexed = subset.set_index("timestamp_utc", drop=False)
    start_endpoint, start_count, start_offset = _endpoint_band_summary(
        indexed,
        value_col,
        start,
        end,
        side="start",
        band_minutes=endpoint_band_minutes,
        search_horizon_minutes=endpoint_search_horizon_minutes,
        min_valid_minutes=min_valid_minutes,
    )
    end_endpoint, end_count, end_offset = _endpoint_band_summary(
        subset.set_index("timestamp_utc", drop=False),
        value_col,
        start,
        end,
        side="end",
        band_minutes=endpoint_band_minutes,
        search_horizon_minutes=endpoint_search_horizon_minutes,
        min_valid_minutes=min_valid_minutes,
    )
    record[f"{prefix}_slope_per_hour"] = float(slope_per_minute * 60.0)
    record[f"{prefix}_trend_r2"] = float(1.0 - residual_ss / total_ss) if total_ss > 0 else np.nan
    record[f"{prefix}_start_endpoint_valid_count"] = start_count
    record[f"{prefix}_end_endpoint_valid_count"] = end_count
    record[f"{prefix}_start_endpoint_offset_minutes"] = start_offset
    record[f"{prefix}_end_endpoint_offset_minutes"] = end_offset
    record[f"{prefix}_endpoint_contrast_defined"] = _flag(pd.notna(start_endpoint) and pd.notna(end_endpoint))
    record[f"{prefix}_end_minus_start"] = (
        end_endpoint - start_endpoint
        if pd.notna(start_endpoint) and pd.notna(end_endpoint)
        else np.nan
    )
    return record


def _all_trend_features(
    sleep_start: pd.Timestamp,
    sleep_end: pd.Timestamp,
    next_sleep_start: pd.Timestamp,
    hr: pd.DataFrame,
    stress: pd.DataFrame,
    config: MonitoringFeaturesFullConfig,
) -> dict[str, float]:
    hr_valid = hr.loc[hr["heart_rate_status"] == "valid"]
    stress_valid = stress.loc[stress["stress_status"] == "valid"]
    pre4_start = max(sleep_end, next_sleep_start - pd.Timedelta(hours=4))
    record: dict[str, float] = {}
    for phase_prefix, start, end in [
        ("sleep", sleep_start, sleep_end),
        ("wake", sleep_end, next_sleep_start),
        ("pre_sleep_4h", pre4_start, next_sleep_start),
    ]:
        record.update(
            _trend_features(
                hr_valid,
                "heart_rate",
                start,
                end,
                f"{phase_prefix}_hr",
                config.min_valid_minutes,
                config.endpoint_band_minutes,
                config.endpoint_search_horizon_minutes,
            )
        )
        record.update(
            _trend_features(
                stress_valid,
                "stress_level",
                start,
                end,
                f"{phase_prefix}_stress",
                config.min_valid_minutes,
                config.endpoint_band_minutes,
                config.endpoint_search_horizon_minutes,
            )
        )
    return record


def _status_features(stress_subset: pd.DataFrame, phase: str) -> dict[str, float | int]:
    raw = pd.to_numeric(stress_subset["stress_level_raw"], errors="coerce")
    total = int(raw.notna().sum())
    minus_1 = int((raw == -1).sum())
    minus_2 = int((raw == -2).sum())
    negative = int((raw < 0).sum())
    valid = int(((raw >= 0) & (raw <= 100)).sum())
    denominator = total if total > 0 else np.nan
    return {
        f"{phase}_stress_raw_minus_1_count": minus_1,
        f"{phase}_stress_raw_minus_1_fraction": minus_1 / denominator if total else np.nan,
        f"{phase}_stress_raw_minus_2_count": minus_2,
        f"{phase}_stress_raw_minus_2_fraction": minus_2 / denominator if total else np.nan,
        f"{phase}_stress_raw_negative_count": negative,
        f"{phase}_stress_raw_negative_fraction": negative / denominator if total else np.nan,
        f"{phase}_stress_raw_valid_fraction": valid / denominator if total else np.nan,
        f"{phase}_stress_large_motion_proxy_minutes": minus_2,
        f"{phase}_stress_large_motion_proxy_fraction": minus_2 / denominator if total else np.nan,
    }


def _phase_advanced_features(
    phase: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    hr: pd.DataFrame,
    stress: pd.DataFrame,
    config: MonitoringFeaturesFullConfig,
) -> dict[str, float | int]:
    hr_subset = _time_slice(hr, start, end)
    stress_subset = _time_slice(stress, start, end)
    hr_valid = hr_subset.loc[hr_subset["heart_rate_status"] == "valid"].copy()
    stress_valid = stress_subset.loc[stress_subset["stress_status"] == "valid"].copy()

    record: dict[str, float | int] = {}
    record.update(
        _shape_stats(
            hr_valid["heart_rate"],
            f"{phase}_hr",
            signal="hr",
            max_hr_bpm=config.max_hr_bpm,
        )
    )
    record.update(
        _shape_stats(
            stress_valid["stress_level"],
            f"{phase}_stress",
            signal="stress",
            max_hr_bpm=config.max_hr_bpm,
        )
    )
    record.update(_hr_zone_features(hr_valid["heart_rate"], f"{phase}_hr", config.max_hr_bpm))
    record.update(_stress_state_features(stress_valid["stress_level"], f"{phase}_stress"))
    record.update(
        _diff_features(
            hr_valid,
            "heart_rate",
            f"{phase}_hr",
            config.gap_break_minutes,
        )
    )
    record.update(
        _diff_features(
            stress_valid,
            "stress_level",
            f"{phase}_stress",
            config.gap_break_minutes,
        )
    )
    record.update(
        _missing_gap_features(
            hr_valid["timestamp_utc"],
            start,
            end,
            f"{phase}_hr",
            config.gap_break_minutes,
        )
    )
    record.update(
        _missing_gap_features(
            stress_valid["timestamp_utc"],
            start,
            end,
            f"{phase}_stress",
            config.gap_break_minutes,
        )
    )
    record.update(
        _boundary_coverage_features(
            hr_valid,
            "heart_rate",
            phase,
            "hr",
            start,
            end,
            config.boundary_gap_tolerance_minutes,
        )
    )
    record.update(
        _boundary_coverage_features(
            stress_valid,
            "stress_level",
            phase,
            "stress",
            start,
            end,
            config.boundary_gap_tolerance_minutes,
        )
    )
    record.update(
        _stress_episode_features(
            stress_valid,
            phase,
            start,
            end,
            config.gap_break_minutes,
        )
    )
    record.update(
        _hr_episode_features(
            hr_valid,
            phase,
            start,
            end,
            config.max_hr_bpm,
            config.gap_break_minutes,
        )
    )
    record.update(_status_features(stress_subset, phase))
    return record


def _safe_diff(record: dict[str, Any], left: str, right: str) -> float:
    left_value = record.get(left, np.nan)
    right_value = record.get(right, np.nan)
    if pd.notna(left_value) and pd.notna(right_value):
        return float(left_value) - float(right_value)
    return np.nan


def _contrast_features(record: dict[str, Any]) -> dict[str, float]:
    return {
        "hr_wake_mean_minus_sleep_mean": _safe_diff(record, "wake_hr_mean", "sleep_hr_mean"),
        "hr_wake_median_minus_sleep_median": _safe_diff(record, "wake_hr_median", "sleep_hr_median"),
        "hr_wake_p90_minus_sleep_p90": _safe_diff(record, "wake_hr_p90", "sleep_hr_p90"),
        "hr_wake_std_minus_sleep_std": _safe_diff(record, "wake_hr_std", "sleep_hr_std"),
        "stress_wake_mean_minus_sleep_mean": _safe_diff(record, "wake_stress_mean", "sleep_stress_mean"),
        "stress_wake_median_minus_sleep_median": _safe_diff(record, "wake_stress_median", "sleep_stress_median"),
        "stress_wake_p90_minus_sleep_p90": _safe_diff(record, "wake_stress_p90", "sleep_stress_p90"),
        "stress_wake_medium_or_high_fraction_minus_sleep": _safe_diff(
            record,
            "wake_stress_frac_medium_or_high_51_100",
            "sleep_stress_frac_medium_or_high_51_100",
        ),
        "stress_wake_high_fraction_minus_sleep": _safe_diff(
            record,
            "wake_stress_frac_high_76_100",
            "sleep_stress_frac_high_76_100",
        ),
        "hr_sleep_reduction_from_wake": _safe_diff(record, "wake_hr_mean", "sleep_hr_mean"),
        "stress_sleep_reduction_from_wake": _safe_diff(record, "wake_stress_mean", "sleep_stress_mean"),
    }


def _correlation(x: pd.Series, y: pd.Series, min_count: int) -> float:
    if len(x) < min_count or len(y) < min_count:
        return np.nan
    x_values = pd.to_numeric(x, errors="coerce").to_numpy(dtype=float)
    y_values = pd.to_numeric(y, errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x_values) & np.isfinite(y_values)
    x_values = x_values[valid]
    y_values = y_values[valid]
    if len(x_values) < min_count or np.std(x_values) == 0 or np.std(y_values) == 0:
        return np.nan
    return float(np.corrcoef(x_values, y_values)[0, 1])


def _regression_slope_r2(x: pd.Series, y: pd.Series, min_count: int) -> tuple[float, float]:
    x_values = pd.to_numeric(x, errors="coerce").to_numpy(dtype=float)
    y_values = pd.to_numeric(y, errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x_values) & np.isfinite(y_values)
    x_values = x_values[valid]
    y_values = y_values[valid]
    if len(x_values) < min_count or np.var(x_values) == 0:
        return np.nan, np.nan
    slope, intercept = np.polyfit(x_values, y_values, 1)
    predicted = slope * x_values + intercept
    total_ss = float(((y_values - y_values.mean()) ** 2).sum())
    residual_ss = float(((y_values - predicted) ** 2).sum())
    r2 = float(1.0 - residual_ss / total_ss) if total_ss > 0 else np.nan
    return float(slope), r2


def _paired_diff_correlation(
    paired: pd.DataFrame,
    gap_break_minutes: float,
    min_paired_minutes: int,
) -> float:
    if len(paired) < min_paired_minutes:
        return np.nan
    ordered = _sort_by_timestamp(paired)
    gaps = pd.to_datetime(ordered["timestamp_utc"], errors="coerce", utc=True).diff().dt.total_seconds() / 60.0
    eligible = gaps <= gap_break_minutes
    eligible.iloc[0] = False
    hr_diff = ordered["heart_rate"].diff().loc[eligible]
    stress_diff = ordered["stress_level"].diff().loc[eligible]
    required = max(2, min_paired_minutes - 1)
    return _correlation(hr_diff, stress_diff, required)


def _coupling_features(
    phase: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    hr: pd.DataFrame,
    stress: pd.DataFrame,
    config: MonitoringFeaturesFullConfig,
) -> dict[str, float | int]:
    hr_valid = _time_slice(hr, start, end).loc[lambda df: df["heart_rate_status"] == "valid"]
    stress_valid = _time_slice(stress, start, end).loc[lambda df: df["stress_status"] == "valid"]
    hr_by_minute = (
        _sort_by_timestamp(hr_valid[["timestamp_utc", "heart_rate"]])
        .assign(heart_rate=lambda df: pd.to_numeric(df["heart_rate"], errors="coerce"))
        .dropna()
        .groupby("timestamp_utc", as_index=False)
        .mean()
    )
    stress_by_minute = (
        _sort_by_timestamp(stress_valid[["timestamp_utc", "stress_level"]])
        .assign(stress_level=lambda df: pd.to_numeric(df["stress_level"], errors="coerce"))
        .dropna()
        .groupby("timestamp_utc", as_index=False)
        .mean()
    )
    paired = _sort_by_timestamp(pd.merge(hr_by_minute, stress_by_minute, on="timestamp_utc", how="inner"))
    count = int(len(paired))
    record: dict[str, float | int] = {
        f"{phase}_paired_hr_stress_valid_minutes": count,
        f"{phase}_paired_hr_stress_coverage_fraction": _coverage_fraction(count, start, end),
        f"{phase}_hr_stress_corr": np.nan,
        f"{phase}_hr_diff_stress_diff_corr": np.nan,
        f"{phase}_stress_hr_slope": np.nan,
        f"{phase}_stress_hr_r2": np.nan,
        f"{phase}_frac_hr_zone1_plus_stress_elevated": np.nan,
        f"{phase}_frac_hr_zone1_plus_stress_low_or_resting": np.nan,
        f"{phase}_frac_hr_zone2_plus_stress_elevated": np.nan,
        f"{phase}_frac_hr_below_zone1_stress_high": np.nan,
    }
    if count == 0:
        return record

    hr_values = pd.to_numeric(paired["heart_rate"], errors="coerce")
    stress_values = pd.to_numeric(paired["stress_level"], errors="coerce")
    zone1_plus = hr_values >= 0.50 * config.max_hr_bpm
    zone2_plus = hr_values >= 0.60 * config.max_hr_bpm
    below_zone1 = hr_values < 0.50 * config.max_hr_bpm
    stress_elevated = stress_values >= 51
    stress_low_or_resting = stress_values <= 50
    stress_high = stress_values >= 76
    record.update(
        {
            f"{phase}_frac_hr_zone1_plus_stress_elevated": float((zone1_plus & stress_elevated).sum() / count),
            f"{phase}_frac_hr_zone1_plus_stress_low_or_resting": float(
                (zone1_plus & stress_low_or_resting).sum() / count
            ),
            f"{phase}_frac_hr_zone2_plus_stress_elevated": float((zone2_plus & stress_elevated).sum() / count),
            f"{phase}_frac_hr_below_zone1_stress_high": float((below_zone1 & stress_high).sum() / count),
        }
    )
    record[f"{phase}_hr_stress_corr"] = _correlation(
        paired["heart_rate"],
        paired["stress_level"],
        config.min_paired_minutes,
    )
    record[f"{phase}_hr_diff_stress_diff_corr"] = _paired_diff_correlation(
        paired,
        config.gap_break_minutes,
        config.min_paired_minutes,
    )
    slope, r2 = _regression_slope_r2(
        paired["heart_rate"],
        paired["stress_level"],
        config.min_paired_minutes,
    )
    record[f"{phase}_stress_hr_slope"] = slope
    record[f"{phase}_stress_hr_r2"] = r2
    return record


def _normalize_windows(semantic_windows_df: pd.DataFrame) -> pd.DataFrame:
    windows = semantic_windows_df.copy()
    if windows.empty:
        return windows
    for column in [
        "sleep_start_utc",
        "sleep_end_utc",
        "wake_start_utc",
        "wake_end_utc",
        "next_sleep_start_utc",
    ]:
        if column not in windows.columns:
            windows[column] = pd.NaT
        windows[column] = pd.to_datetime(windows[column], errors="coerce", utc=True)
    windows["calendarDate"] = pd.to_datetime(windows["calendarDate"], errors="coerce").dt.normalize()
    for column in SEMANTIC_WINDOW_COLUMNS:
        if column not in windows.columns:
            windows[column] = pd.NA
    windows["wake_start_utc"] = windows["wake_start_utc"].fillna(windows["sleep_end_utc"])
    windows["wake_end_utc"] = windows["wake_end_utc"].fillna(windows["next_sleep_start_utc"])
    if "sleep_duration_hours" not in windows or windows["sleep_duration_hours"].isna().all():
        windows["sleep_duration_hours"] = (
            windows["sleep_end_utc"] - windows["sleep_start_utc"]
        ).dt.total_seconds() / 3600.0
    else:
        windows["sleep_duration_hours"] = pd.to_numeric(windows["sleep_duration_hours"], errors="coerce")
    if "wake_duration_hours" not in windows or windows["wake_duration_hours"].isna().all():
        windows["wake_duration_hours"] = (
            windows["wake_end_utc"] - windows["wake_start_utc"]
        ).dt.total_seconds() / 3600.0
    else:
        windows["wake_duration_hours"] = pd.to_numeric(windows["wake_duration_hours"], errors="coerce")
    if "analysis_window_id" not in windows.columns:
        windows["analysis_window_id"] = windows["calendarDate"].dt.strftime("%Y-%m-%d")
    sort_columns = ["calendarDate", "analysis_window_id"]
    return windows.dropna(subset=["calendarDate"]).sort_values(sort_columns).reset_index(drop=True)


def _normalize_base_features(
    heart_rate_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    windows_df: pd.DataFrame,
    foundation_features_df: pd.DataFrame | None,
) -> pd.DataFrame:
    if foundation_features_df is None or foundation_features_df.empty:
        base = build_monitoring_daily_features(heart_rate_df, stress_df, windows_df)
    else:
        base = foundation_features_df.copy()
    if base.empty:
        return base
    base["calendarDate"] = pd.to_datetime(base["calendarDate"], errors="coerce").dt.normalize()
    return base.dropna(subset=["calendarDate"]).drop_duplicates("calendarDate", keep="last")


def _build_legacy_monitoring_features_full(
    heart_rate_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    analysis_windows_df: pd.DataFrame,
    foundation_features_df: pd.DataFrame | None = None,
    *,
    max_hr_bpm: float = 192.0,
    gap_break_minutes: float = 2.0,
    min_valid_minutes: int = 5,
    min_paired_minutes: int = 10,
    min_sleep_duration_hours: float = 2.0,
    max_sleep_duration_hours: float = 16.0,
    min_wake_duration_hours: float = 6.0,
    max_wake_duration_hours: float = 30.0,
    boundary_gap_tolerance_minutes: float = 60.0,
    endpoint_band_minutes: float = 30.0,
    endpoint_search_horizon_minutes: float = 90.0,
) -> pd.DataFrame:
    """Build a wide daily monitoring feature table.

    The preferred input is the quality-index analysis window table, so fused
    missed-sleep spans are handled before features are computed. Numeric stress
    features use only valid `0..100` stress values; raw negative stress values
    are exposed only as status/proxy features.
    """
    config = MonitoringFeaturesFullConfig(
        max_hr_bpm=float(max_hr_bpm),
        gap_break_minutes=float(gap_break_minutes),
        min_valid_minutes=int(min_valid_minutes),
        min_paired_minutes=int(min_paired_minutes),
        min_sleep_duration_hours=float(min_sleep_duration_hours),
        max_sleep_duration_hours=float(max_sleep_duration_hours),
        min_wake_duration_hours=float(min_wake_duration_hours),
        max_wake_duration_hours=float(max_wake_duration_hours),
        boundary_gap_tolerance_minutes=float(boundary_gap_tolerance_minutes),
        endpoint_band_minutes=float(endpoint_band_minutes),
        endpoint_search_horizon_minutes=float(endpoint_search_horizon_minutes),
    )
    if config.max_hr_bpm <= 0:
        raise ValueError("max_hr_bpm must be positive")
    if config.gap_break_minutes <= 0:
        raise ValueError("gap_break_minutes must be positive")
    if config.min_valid_minutes < 1:
        raise ValueError("min_valid_minutes must be at least 1")
    if config.min_paired_minutes < 2:
        raise ValueError("min_paired_minutes must be at least 2")
    if config.min_sleep_duration_hours < 0 or config.max_sleep_duration_hours <= config.min_sleep_duration_hours:
        raise ValueError("sleep duration plausibility bounds must satisfy 0 <= min < max")
    if config.min_wake_duration_hours < 0 or config.max_wake_duration_hours <= config.min_wake_duration_hours:
        raise ValueError("wake duration plausibility bounds must satisfy 0 <= min < max")
    if config.boundary_gap_tolerance_minutes < 0:
        raise ValueError("boundary_gap_tolerance_minutes must be non-negative")
    if config.endpoint_band_minutes <= 0:
        raise ValueError("endpoint_band_minutes must be positive")
    if config.endpoint_search_horizon_minutes <= 0:
        raise ValueError("endpoint_search_horizon_minutes must be positive")
    if config.endpoint_search_horizon_minutes < config.endpoint_band_minutes:
        raise ValueError("endpoint_search_horizon_minutes must be at least endpoint_band_minutes")

    windows = _normalize_windows(analysis_windows_df)
    if windows.empty:
        return pd.DataFrame()

    heart_rate = _indexed_by_timestamp(normalize_heart_rate_frame(heart_rate_df))
    stress = _indexed_by_timestamp(normalize_stress_frame(stress_df))
    base = _normalize_base_features(
        heart_rate_df,
        stress_df,
        windows,
        foundation_features_df,
    )
    base_by_date = (
        base.set_index("calendarDate", drop=False)
        if not base.empty and "calendarDate" in base.columns
        else pd.DataFrame()
    )

    records: list[dict[str, Any]] = []
    for window in windows.itertuples(index=False):
        calendar_date = pd.Timestamp(window.calendarDate).normalize()
        if not base_by_date.empty and calendar_date in base_by_date.index:
            base_row = base_by_date.loc[calendar_date]
            if isinstance(base_row, pd.DataFrame):
                base_row = base_row.iloc[-1]
            record: dict[str, Any] = base_row.to_dict()
        else:
            record = {}

        sleep_start = pd.Timestamp(window.sleep_start_utc)
        sleep_end = pd.Timestamp(window.sleep_end_utc)
        wake_start = pd.Timestamp(window.wake_start_utc)
        wake_end = pd.Timestamp(window.wake_end_utc)
        next_sleep_start = pd.Timestamp(window.next_sleep_start_utc)
        next_sleep_known = bool(
            getattr(window, "next_sleep_start_known", pd.notna(next_sleep_start)) == 1
            or pd.notna(next_sleep_start)
        )
        if pd.isna(next_sleep_start) and next_sleep_known and pd.notna(wake_end):
            next_sleep_start = wake_end

        record.update(
            {
                "analysis_window_id": getattr(window, "analysis_window_id", str(calendar_date.date())),
                "calendarDate": calendar_date,
                "sleep_duration_hours": getattr(window, "sleep_duration_hours", np.nan),
                "wake_duration_hours": getattr(window, "wake_duration_hours", np.nan),
            }
        )

        phase_specs = []
        if pd.notna(sleep_start) and pd.notna(sleep_end) and sleep_start < sleep_end:
            phase_specs.append(("sleep", sleep_start, sleep_end))
        if pd.notna(wake_start) and pd.notna(wake_end) and wake_start < wake_end:
            phase_specs.append(("wake", wake_start, wake_end))

        for phase, start, end in phase_specs:
            for key, value in _phase_advanced_features(phase, start, end, heart_rate, stress, config).items():
                record[key] = value
            for key, value in _relative_window_features(
                phase,
                start,
                end,
                heart_rate,
                stress,
                config.min_valid_minutes,
            ).items():
                record[key] = value
            for key, value in _coupling_features(phase, start, end, heart_rate, stress, config).items():
                record[key] = value

        if pd.notna(sleep_start) and pd.notna(sleep_end) and sleep_start < sleep_end:
            record.update(
                _sleep_recovery_features(
                    sleep_start,
                    sleep_end,
                    heart_rate,
                    stress,
                    config.min_valid_minutes,
                )
            )
        if (
            next_sleep_known
            and pd.notna(sleep_start)
            and pd.notna(sleep_end)
            and pd.notna(next_sleep_start)
            and sleep_start < sleep_end < next_sleep_start
        ):
            record.update(
                _anchored_window_features(
                    sleep_start,
                    sleep_end,
                    next_sleep_start,
                    heart_rate,
                    stress,
                    config.min_valid_minutes,
                )
            )
            record.update(
                _pre_sleep_features(
                    sleep_end,
                    next_sleep_start,
                    heart_rate,
                    stress,
                    config.min_valid_minutes,
                )
            )
            record.update(
                _all_trend_features(
                    sleep_start,
                    sleep_end,
                    next_sleep_start,
                    heart_rate,
                    stress,
                    config,
                )
            )
        record.update(_contrast_features(record))
        records.append(record)

    out = pd.DataFrame.from_records(records)
    out["calendarDate"] = pd.to_datetime(out["calendarDate"], errors="coerce").dt.normalize()
    return out.sort_values("calendarDate").reset_index(drop=True)


def _median_line(feature_df: pd.DataFrame, column: str) -> str | None:
    if column not in feature_df.columns or feature_df.empty:
        return None
    value = pd.to_numeric(feature_df[column], errors="coerce").median()
    if pd.isna(value):
        return f"- `{column}` median: `n/a`"
    return f"- `{column}` median: `{value:.3f}`"


def _date_range(feature_df: pd.DataFrame) -> str:
    if feature_df.empty or "calendarDate" not in feature_df.columns:
        return "n/a"
    dates = pd.to_datetime(feature_df["calendarDate"], errors="coerce").dropna()
    if dates.empty:
        return "n/a"
    return f"{dates.min().date()} to {dates.max().date()}"


def _starts_with_relative_window(column: str) -> bool:
    return any(column.startswith(f"{phase}_q{idx}_") for phase in PHASES for idx in range(1, 5))


def _starts_with_anchored_window(column: str) -> bool:
    anchored_prefixes = (
        "first_30m_after_wake_",
        "first_2h_after_wake_",
        "last_2h_before_sleep_",
        "last_4h_before_sleep_",
        "first_60m_sleep_",
        "last_60m_sleep_",
    )
    return column.startswith(anchored_prefixes)


def _foundation_coverage_column(column: str) -> bool:
    foundation_suffixes = (
        "_total_count",
        "_valid_count",
        "_coverage_fraction",
        "_unmeasurable_count",
        "_status_value_count",
        "_nonvalid_count",
        "_unmeasurable_fraction",
        "_status_value_fraction",
        "_nonvalid_fraction",
    )
    return column.startswith(("sleep_", "wake_")) and column.endswith(foundation_suffixes)


def _distribution_column(column: str) -> bool:
    distribution_suffixes = (
        "_mean",
        "_median",
        "_std",
        "_min",
        "_max",
        "_p05",
        "_p10",
        "_p25",
        "_p75",
        "_p90",
        "_p95",
        "_iqr",
        "_range",
        "_trimmed_mean",
        "_mad",
        "_skewness",
        "_kurtosis",
        "_histogram_entropy",
        "_coefficient_of_variation",
    )
    return column.endswith(distribution_suffixes)


def _infer_family(column: str) -> str:
    if column in SEMANTIC_WINDOW_COLUMNS or column in {"analysis_window_id", "source_calendarDate"}:
        return "identity/window metadata"
    if column in SEMANTIC_WINDOW_QUALITY_COLUMNS:
        return "semantic window quality"
    if "stress_raw_" in column or "large_motion_proxy" in column:
        return "raw stress status"
    if _starts_with_relative_window(column):
        return "relative windows"
    if _starts_with_anchored_window(column):
        return "anchored windows"
    if (
        "paired_hr_stress" in column
        or "_hr_stress_corr" in column
        or "_hr_diff_stress_diff_corr" in column
        or "_stress_hr_" in column
        or "_frac_hr_" in column
    ):
        return "HR/stress coupling"
    if (
        column.startswith(("hr_wake_", "stress_wake_"))
        or column in {"hr_sleep_reduction_from_wake", "stress_sleep_reduction_from_wake"}
    ):
        return "sleep-wake contrast"
    if column.endswith(
        (
            "_slope_per_hour",
            "_trend_r2",
            "_end_minus_start",
            "_start_endpoint_valid_count",
            "_end_endpoint_valid_count",
            "_start_endpoint_offset_minutes",
            "_end_endpoint_offset_minutes",
            "_endpoint_contrast_defined",
        )
    ):
        return "trends"
    if (
        "first_60m" in column
        or "last_60m" in column
        or "q1_minus_q4" in column
        or column.endswith(("_q1_mean", "_q4_mean"))
        or "drop_from_start_to_min_rolling_30m" in column
        or "time_to_min" in column
        or "time_to_low_stress" in column
        or "time_to_stable_low_stress" in column
        or column.startswith("pre_sleep_")
        or column.startswith("evening_deactivation_")
    ):
        return "recovery/deactivation"
    if (
        "episode" in column
        or "state_transition" in column
        or "transitions_per_valid_hour" in column
        or column.endswith("_has_event")
        or "time_to_first" in column
        or "time_since_last" in column
        or "fragmentation_index" in column
        or "duration_minutes" in column
        or column.endswith("_total_minutes")
    ):
        return "episodes/state structure"
    if (
        "diff_" in column
        or column.endswith(("_mean_abs_diff", "_median_abs_diff", "_std_diff", "_max_abs_jump", "_roughness"))
        or "longest_observed_gap" in column
    ):
        return "variability/gaps"
    if (
        "longest_missing_gap" in column
        or "missing_gap_count" in column
        or "small_gap_count" in column
        or "large_gap_count" in column
        or column.endswith("_minutes_to_first_valid")
        or column.endswith("_minutes_from_last_valid_to_end")
        or column.endswith("_start_boundary_covered")
        or column.endswith("_end_boundary_covered")
    ):
        return "missingness/coverage"
    if "_hr_frac_" in column and any(zone in column for zone in (*HR_ZONE_COLUMNS, "zone1_plus", "zone2_plus", "zone3_plus")):
        return "HR MHR zones"
    if "_stress_frac_" in column and (
        any(state in column for state in STRESS_STATE_COLUMNS) or "medium_or_high_51_100" in column
    ):
        return "stress state fractions"
    if _foundation_coverage_column(column):
        return "foundation coverage"
    if _distribution_column(column):
        return "distribution/shape"
    return "other"


def _infer_signal(column: str) -> str:
    padded = f"_{column}_"
    if (
        "paired_hr_stress" in column
        or "_hr_stress_" in column
        or "hr_diff_stress_diff" in column
        or "_stress_hr_" in column
        or "_frac_hr_" in column
    ):
        return "hr+stress"
    if padded.startswith("_hr_") or "_hr_" in padded:
        return "hr"
    if padded.startswith("_stress_") or "_stress_" in padded or "large_motion_proxy" in column:
        return "stress"
    return "metadata"


def _infer_phase(column: str) -> str:
    if column.startswith("sleep_") or column.startswith("first_60m_sleep_") or column.startswith("last_60m_sleep_"):
        return "sleep"
    if (
        column.startswith("wake_")
        or column.startswith("first_30m_after_wake_")
        or column.startswith("first_2h_after_wake_")
        or column.startswith("last_2h_before_sleep_")
        or column.startswith("last_4h_before_sleep_")
    ):
        return "wake"
    if column.startswith("pre_sleep_"):
        return "wake/pre-sleep"
    if column.startswith("evening_deactivation_"):
        return "wake/evening"
    if column.startswith(("hr_wake_", "stress_wake_")) or column.endswith("_reduction_from_wake"):
        return "sleep-wake"
    return "metadata"


def _infer_window(column: str) -> str:
    for phase in PHASES:
        for idx in range(1, 5):
            prefix = f"{phase}_q{idx}_"
            if column.startswith(prefix):
                return f"{phase}_q{idx}"
    anchored_prefixes = (
        "first_30m_after_wake",
        "first_2h_after_wake",
        "last_2h_before_sleep",
        "last_4h_before_sleep",
        "first_60m_sleep",
        "last_60m_sleep",
    )
    for prefix in anchored_prefixes:
        if column.startswith(f"{prefix}_"):
            return prefix
    if column.startswith("pre_sleep_2h_"):
        return "pre_sleep_2h"
    if column.startswith("pre_sleep_4h_") or column.startswith("pre_sleep_4h_"):
        return "pre_sleep_4h"
    if column.startswith("sleep_"):
        return "sleep_phase"
    if column.startswith("wake_"):
        return "wake_phase"
    return "not_windowed"


def _infer_metric(column: str) -> str:
    prefixes = []
    for phase in PHASES:
        prefixes.extend([f"{phase}_q{idx}_" for idx in range(1, 5)])
        prefixes.extend([f"{phase}_hr_", f"{phase}_stress_"])
    prefixes.extend(
        [
            "first_30m_after_wake_hr_",
            "first_30m_after_wake_stress_",
            "first_2h_after_wake_hr_",
            "first_2h_after_wake_stress_",
            "last_2h_before_sleep_hr_",
            "last_2h_before_sleep_stress_",
            "last_4h_before_sleep_hr_",
            "last_4h_before_sleep_stress_",
            "first_60m_sleep_hr_",
            "first_60m_sleep_stress_",
            "last_60m_sleep_hr_",
            "last_60m_sleep_stress_",
            "pre_sleep_2h_hr_",
            "pre_sleep_2h_stress_",
            "pre_sleep_4h_hr_",
            "pre_sleep_4h_stress_",
        ]
    )
    for prefix in sorted(prefixes, key=len, reverse=True):
        if column.startswith(prefix):
            return column.removeprefix(prefix)
    return column


def _infer_unit(column: str, signal: str) -> str:
    if column == "calendarDate":
        return "date"
    if column.endswith("_utc") or column.endswith("_local"):
        return "timestamp"
    if (
        column in SEMANTIC_WINDOW_QUALITY_COLUMNS - {"semantic_day_duration_hours"}
        or column.endswith("_has_event")
        or column.endswith("_boundary_covered")
        or column.endswith("_endpoint_contrast_defined")
    ):
        return "0/1 flag"
    if column.endswith("_hours"):
        return "hours"
    if column.endswith("_minutes") or "duration_minutes" in column or "time_to" in column or "time_since" in column:
        return "minutes"
    if column.endswith("_count") or column.endswith("_valid_minutes"):
        return "count"
    if column.endswith("_fraction") or "_frac_" in column or "coverage_fraction" in column:
        return "fraction 0..1"
    if column.endswith("_corr"):
        return "correlation -1..1"
    if column.endswith("_r2"):
        return "r2 0..1"
    if column.endswith("_histogram_entropy"):
        return "bits"
    if column.endswith("_slope_per_hour"):
        return "bpm/hour" if signal == "hr" else "stress points/hour"
    if signal == "hr":
        return "bpm"
    if signal == "stress":
        return "stress points"
    if signal == "hr+stress":
        return "mixed"
    return "metadata"


def _description_for(column: str, family: str, signal: str, phase: str, window: str, metric: str) -> str:
    base = f"{metric.replace('_', ' ')} for {signal} in {phase}"
    if window not in {"not_windowed", "sleep_phase", "wake_phase"}:
        base += f" during {window.replace('_', ' ')}"
    if family == "identity/window metadata":
        return "Identifier, UTC/local semantic-window timestamp, duration, or local offset metadata."
    if family == "semantic window quality":
        if column == "semantic_day_duration_hours":
            return "Total semantic-day duration from sleep start through the next sleep start."
        if column.endswith("_plausible"):
            return "Data-quality flag for whether semantic sleep/wake duration falls inside configured plausibility bounds."
        if column.endswith("_outlier"):
            return "Data-quality flag for semantic sleep/wake duration outside configured plausibility bounds."
        if column.endswith("_gt_24h") or column.endswith("_gt_48h"):
            return "Data-quality flag for very long wake windows, usually indicating a missing next sleep record rather than a normal wake phase."
        return "Semantic-window quality/filtering feature for downstream EDA."
    if family == "foundation coverage":
        return "Packet 02 baseline count, coverage, or stress status diagnostic carried into the feature library."
    if family == "distribution/shape":
        if column.endswith("_histogram_entropy"):
            if signal == "hr":
                return "Distribution entropy over fixed maximum-heart-rate zone bins derived from the configured max HR."
            return "Distribution entropy over fixed Garmin-like stress-state bins across valid stress values from 0 to 100."
        return base + "."
    if family == "stress state fractions":
        if column.endswith("_stress_frac_active"):
            return "Share of eligible stress-state minutes with raw `-2` and same-minute valid HR, treated as an active/large-motion proxy rather than numeric stress."
        return "Share of eligible raw stress minutes in a fixed Garmin-like numeric stress state; raw `-1` and raw `-2` without same-minute valid HR are excluded from the denominator."
    if family == "HR MHR zones":
        return "Share of valid HR minutes in a fixed maximum-heart-rate zone derived from the configured max HR."
    if family == "variability/gaps":
        return "Gap-aware minute-to-minute variability diagnostic; gaps beyond the configured threshold break segments."
    if family == "missingness/coverage":
        if column.endswith("_minutes_to_first_valid"):
            return "Minutes from the phase/window start to the first valid observation for the signal."
        if column.endswith("_minutes_from_last_valid_to_end"):
            return "Minutes from the last valid signal observation to the phase/window end."
        if column.endswith("_start_boundary_covered"):
            return "Flag for whether the first valid signal observation is within the configured boundary tolerance after phase/window start."
        if column.endswith("_end_boundary_covered"):
            return "Flag for whether the last valid signal observation is within the configured boundary tolerance before phase/window end."
        return "Missingness or paired coverage diagnostic for the semantic phase/window."
    if family == "episodes/state structure":
        if column.endswith("_has_event"):
            return "Flag for whether at least one matching state episode occurred; no-event cases keep duration summaries at zero."
        if column.endswith("_time_since_last_minutes"):
            return "Time from the end of the last matching event to the end of the phase/window; undefined when no event occurred."
        if column.endswith("_time_to_first_minutes"):
            return "Time from the phase/window start to the first matching event; undefined when no event occurred."
        if column.endswith("_fragmentation_index"):
            return "Episode count divided by total event minutes; high values imply many short bursts, and no-event cases are zero."
        return "Contiguous state-run feature; gaps beyond the configured threshold break episodes."
    if family == "recovery/deactivation":
        return "Sleep recovery or pre-sleep deactivation summary; positive deactivation means lower values closer to sleep."
    if family == "relative windows":
        if column.endswith("_duration_minutes"):
            return "Duration of the relative quarter-window, useful for interpreting coverage and long semantic windows."
        if "stress_raw_" in column or "large_motion_proxy" in column:
            return "Raw stress status fraction for the relative window; negative raw values are not treated as numeric stress."
        return "Compact summary for a relative quarter of the sleep or wake phase."
    if family == "anchored windows":
        if column.endswith("_duration_minutes"):
            return "Duration of the anchored window after wake or before sleep, useful for interpreting coverage."
        if "stress_raw_" in column or "large_motion_proxy" in column:
            return "Raw stress status fraction for the anchored window; raw `-2` requires same-minute valid HR before it is interpreted as active proxy."
        return "Compact summary for a fixed window anchored to wake or sleep boundaries."
    if family == "trends":
        if column.endswith("_endpoint_contrast_defined"):
            return "Flag for whether both robust endpoint bands had enough valid observations to define end-minus-start."
        if column.endswith("_endpoint_valid_count"):
            return "Valid observation count in the robust endpoint band chosen near the phase/window boundary."
        if column.endswith("_endpoint_offset_minutes"):
            return "Offset between the phase/window boundary and the robust endpoint band used for end-minus-start."
        if column.endswith("_end_minus_start"):
            return "Robust endpoint-band contrast: latest usable endpoint-band mean minus earliest usable endpoint-band mean."
        return "Simple linear trend or robust endpoint-band contrast in interpretable per-hour units."
    if family == "sleep-wake contrast":
        return "Difference between wake and sleep monitoring summaries."
    if family == "HR/stress coupling":
        return "Same-minute paired HR/stress feature using only valid HR and valid numeric stress rows."
    if family == "raw stress status":
        if "minus_2" in column or "large_motion_proxy" in column:
            return "Raw stress `-2` status diagnostic; only same-minute valid HR confirms active proxy, and it is not treated as numeric stress."
        if "minus_1" in column:
            return "Raw stress `-1` status fraction/count; not treated as numeric stress."
        return "Raw stress status/proxy feature; negative raw values are not treated as numeric stress."
    return "Monitoring feature column not matched to a more specific catalog family."


def _analysis_role(family: str) -> str:
    if family == "identity/window metadata":
        return "identifier"
    if family == "semantic window quality":
        return "quality_filter"
    if family in {"foundation coverage", "missingness/coverage", "raw stress status"}:
        return "diagnostic"
    return "feature"


def _format_example_values(values: pd.Series, max_examples: int = 3) -> str:
    examples = values.dropna().drop_duplicates().head(max_examples).tolist()
    rendered: list[str] = []
    for value in examples:
        if isinstance(value, pd.Timestamp):
            rendered.append(str(value))
        elif isinstance(value, float):
            rendered.append(f"{value:.4g}")
        else:
            rendered.append(str(value))
    return "; ".join(rendered)


def _numeric_summary(series: pd.Series) -> dict[str, float]:
    if not pd.api.types.is_numeric_dtype(series):
        return {key: np.nan for key in ["min", "p05", "p25", "median", "p75", "p95", "max", "mean", "std"]}
    numeric = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if numeric.empty:
        return {key: np.nan for key in ["min", "p05", "p25", "median", "p75", "p95", "max", "mean", "std"]}
    return {
        "min": float(numeric.min()),
        "p05": float(numeric.quantile(0.05)),
        "p25": float(numeric.quantile(0.25)),
        "median": float(numeric.median()),
        "p75": float(numeric.quantile(0.75)),
        "p95": float(numeric.quantile(0.95)),
        "max": float(numeric.max()),
        "mean": float(numeric.mean()),
        "std": float(numeric.std(ddof=0)),
    }


def _zero_pct(series: pd.Series) -> float:
    if not pd.api.types.is_numeric_dtype(series):
        return np.nan
    numeric = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if numeric.empty:
        return np.nan
    return float((numeric == 0).sum() / len(numeric) * 100.0)


def _caution_text(
    *,
    is_all_null: bool,
    is_constant_non_null: bool,
    is_mostly_missing: bool,
    is_sparse_or_rare: bool,
    family: str,
) -> str:
    notes: list[str] = []
    if is_all_null:
        notes.append("all values are missing")
    if is_constant_non_null:
        notes.append("constant among non-null values")
    if is_mostly_missing:
        notes.append("mostly missing; inspect before EDA/modeling")
    if is_sparse_or_rare and not is_mostly_missing:
        notes.append("sparse or rare-event style feature")
    if family == "semantic window quality":
        notes.append("data-quality filter; use before interpreting window-heavy features")
    if family == "raw stress status":
        notes.append("raw status/proxy only; not numeric stress")
    if family == "HR/stress coupling":
        notes.append("requires paired valid HR and stress minutes")
    return "; ".join(notes)


def _candidate_model_feature(
    *,
    role: str,
    is_all_null: bool,
    is_constant_non_null: bool,
    is_mostly_missing: bool,
    dtype: str,
) -> bool:
    if role in {"identifier", "quality_filter"} or is_all_null or is_constant_non_null or is_mostly_missing:
        return False
    return not dtype.startswith("datetime")


def build_monitoring_feature_catalog(
    feature_df: pd.DataFrame,
    *,
    mostly_missing_threshold: float = 90.0,
    sparse_zero_threshold: float = 95.0,
) -> pd.DataFrame:
    """Build a data dictionary/catalog for the monitoring feature library."""
    rows: list[dict[str, Any]] = []
    total_rows = len(feature_df)
    denominator = total_rows if total_rows else 1
    for column in feature_df.columns:
        series = feature_df[column]
        non_null_count = int(series.notna().sum())
        missing_count = total_rows - non_null_count
        non_null_pct = float(non_null_count / denominator * 100.0)
        missing_pct = float(missing_count / denominator * 100.0)
        n_unique = int(series.dropna().nunique())
        is_all_null = non_null_count == 0
        is_constant_non_null = non_null_count > 0 and n_unique == 1
        is_mostly_missing = missing_pct >= mostly_missing_threshold
        zero_pct = _zero_pct(series)
        is_sparse_or_rare = bool(is_mostly_missing or (pd.notna(zero_pct) and zero_pct >= sparse_zero_threshold))
        family = _infer_family(column)
        signal = _infer_signal(column)
        phase = _infer_phase(column)
        window = _infer_window(column)
        metric = _infer_metric(column)
        role = _analysis_role(family)
        dtype = str(series.dtype)
        candidate = _candidate_model_feature(
            role=role,
            is_all_null=is_all_null,
            is_constant_non_null=is_constant_non_null,
            is_mostly_missing=is_mostly_missing,
            dtype=dtype,
        )
        numeric_summary = _numeric_summary(series)
        caution = _caution_text(
            is_all_null=is_all_null,
            is_constant_non_null=is_constant_non_null,
            is_mostly_missing=is_mostly_missing,
            is_sparse_or_rare=is_sparse_or_rare,
            family=family,
        )
        rows.append(
            {
                "column": column,
                "family": family,
                "signal": signal,
                "phase": phase,
                "window": window,
                "metric": metric,
                "description": _description_for(column, family, signal, phase, window, metric),
                "unit": _infer_unit(column, signal),
                "dtype": dtype,
                "non_null_count": non_null_count,
                "non_null_pct": non_null_pct,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "n_unique": n_unique,
                "is_all_null": is_all_null,
                "is_constant_non_null": is_constant_non_null,
                "is_mostly_missing": is_mostly_missing,
                "is_sparse_or_rare": is_sparse_or_rare,
                "zero_pct": zero_pct,
                "example_values": _format_example_values(series),
                "analysis_role": role,
                "recommended_for_eda": bool(not is_all_null and role != "identifier"),
                "candidate_model_feature": candidate,
                "caution": caution,
                **numeric_summary,
            }
        )
    catalog = pd.DataFrame.from_records(rows)
    family_rank = {family: idx for idx, family in enumerate(FEATURE_FAMILY_ORDER)}
    catalog["_family_rank"] = catalog["family"].map(family_rank).fillna(len(family_rank))
    catalog = catalog.sort_values(["_family_rank", "column"]).drop(columns="_family_rank")
    return catalog.reindex(columns=CATALOG_COLUMNS).reset_index(drop=True)


def _markdown_table(df: pd.DataFrame, columns: list[str], *, max_rows: int = 20) -> list[str]:
    if df.empty:
        return ["No rows."]
    subset = df.loc[:, columns].head(max_rows).copy()
    for column in subset.columns:
        subset[column] = subset[column].map(lambda value: "" if pd.isna(value) else str(value).replace("|", "\\|"))
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in subset.itertuples(index=False):
        lines.append("| " + " | ".join(getattr(row, column) for column in columns) + " |")
    return lines


def build_monitoring_feature_catalog_markdown(
    catalog_df: pd.DataFrame,
    *,
    csv_path: str = "reports/monitoring_features_full_catalog.csv",
) -> str:
    """Build a compact human-readable catalog report for the wide feature table."""
    family_counts = catalog_df["family"].value_counts().reindex(FEATURE_FAMILY_ORDER).dropna()
    constant = catalog_df.loc[catalog_df["is_constant_non_null"] == True].sort_values(
        ["missing_pct", "column"],
        ascending=[False, True],
    )
    mostly_missing = catalog_df.loc[catalog_df["is_mostly_missing"] == True].sort_values(
        ["missing_pct", "column"],
        ascending=[False, True],
    )
    key_columns = (
        catalog_df.loc[
            (catalog_df["candidate_model_feature"] == True)
            & (catalog_df["recommended_for_eda"] == True)
        ]
        .sort_values(["family", "missing_pct", "column"])
        .groupby("family")
        .head(3)
    )
    family_explanations = {
        "identity/window metadata": "Semantic-day identifiers, UTC/local sleep and wake boundaries, durations, and local offset metadata.",
        "semantic window quality": "Plausibility and outlier flags for semantic sleep/wake windows; filter very long wake windows before interpreting window-heavy features.",
        "foundation coverage": "Phase-level counts, coverage fractions, and status diagnostics retained for filtering and audit.",
        "distribution/shape": "Robust and standard summaries of valid HR or numeric stress values; entropy uses fixed bins.",
        "stress state fractions": "Shares of eligible raw stress minutes in fixed Garmin-like states, including active proxy from raw `-2` only when same-minute valid HR confirms activity.",
        "HR MHR zones": "Shares of valid HR minutes in fixed zones derived from the configured maximum heart rate.",
        "variability/gaps": "Gap-aware first-difference roughness and jump diagnostics without interpolation.",
        "missingness/coverage": "Missing-gap, boundary-coverage, and paired-coverage diagnostics for data quality filtering.",
        "episodes/state structure": "Contiguous runs of stress or HR states with gap breaks; no-event cases have `has_event = 0` and zero duration summaries.",
        "recovery/deactivation": "Sleep decline and pre-sleep deactivation summaries.",
        "relative windows": "Compact summaries for sleep/wake quarters.",
        "anchored windows": "Compact summaries for fixed windows around wake and sleep boundaries.",
        "trends": "Simple linear slopes and trend fit quality computed over available valid points.",
        "sleep-wake contrast": "Direct wake-minus-sleep physiology and state-fraction differences.",
        "HR/stress coupling": "Same-minute paired HR and valid numeric stress relationships.",
        "raw stress status": "Raw stress status/proxy diagnostics, including compact window fractions; negative raw values are not stress scores.",
    }

    lines = [
        "# Monitoring Feature Catalog",
        "",
        "This catalog summarizes the columns in `data/processed/monitoring_features_full_v0.parquet`. The full row-level feature dictionary is in the CSV output.",
        "",
        "## Outputs",
        "",
        f"- Full CSV catalog: `{csv_path}`",
        "- Markdown summary: `reports/monitoring_features_full_catalog.md`",
        "",
        "## Feature Family Counts",
        "",
    ]
    for family, count in family_counts.items():
        lines.append(f"- {family}: `{int(count)}`")

    lines.extend(
        [
            "",
            "## Family Guide",
            "",
        ]
    )
    for family in FEATURE_FAMILY_ORDER:
        if family in family_explanations and int(family_counts.get(family, 0)) > 0:
            lines.append(f"- {family}: {family_explanations[family]}")

    lines.extend(
        [
            "",
            "## Constant Non-Null Columns",
            "",
            "Constant columns are diagnostics. Some are constant only because they have very few non-null values; modeling and first-pass EDA should filter/select features intentionally.",
            "",
        ]
    )
    lines.extend(
        _markdown_table(
            constant,
            ["column", "family", "missing_pct", "n_unique", "caution"],
            max_rows=20,
        )
    )
    lines.extend(
        [
            "",
            "## Mostly Missing Columns",
            "",
            "Columns below use `missing_pct >= 90` as the mostly-missing threshold.",
            "",
        ]
    )
    lines.extend(
        _markdown_table(
            mostly_missing,
            ["column", "family", "missing_pct", "non_null_count", "n_unique"],
            max_rows=20,
        )
    )
    lines.extend(
        [
            "",
            "## Useful Starting Columns By Family",
            "",
            "These are non-constant, not-mostly-missing catalog candidates, intended as a starting point rather than a final model feature set.",
            "",
        ]
    )
    lines.extend(
        _markdown_table(
            key_columns,
            ["column", "family", "signal", "phase", "window", "missing_pct"],
            max_rows=45,
        )
    )
    lines.extend(
        [
            "",
            "## Entropy Policy",
            "",
            "- Stress histogram entropy uses fixed Garmin-like stress-state bins across valid `0..100` stress values: `0..25`, `26..50`, `51..75`, and `76..100`.",
            "- HR histogram entropy uses fixed maximum-heart-rate zone bins derived from the configured `max_hr_bpm`: below 50%, 50..60%, 60..70%, 70..80%, 80..90%, 90..100%, and above 100% MHR.",
            "- Entropy is therefore comparable across days for a fixed `max_hr_bpm`; it is not computed from per-day dynamic min/max bin edges.",
            "",
            "## Notes",
            "",
            "- Numeric stress features use only valid `0..100` stress values.",
            "- Raw stress `-1` is excluded from feature-state denominators and remains a quality diagnostic.",
            "- Raw stress `-2` appears in feature-state fractions only through `stress_frac_active` when same-minute valid HR confirms activity.",
            "- Raw stress `-2` without same-minute valid HR remains an unmeasurable/status diagnostic, not activity.",
            "- When this table is joined to `monitoring_quality_index.parquet`, stress coverage counts raw `0..100` plus HR-confirmed raw `-2`; raw `-2` without valid HR remains unobserved for stress quality.",
            "- Baseline recovery eligibility does not require `pre_sleep_4h_usable`; filter on that quality flag for stricter pre-sleep sensitivity analyses.",
            "- Baseline usable flags allow max gaps up to `360` minutes; analysts can still filter `*_max_gap_minutes <= 180` for stricter gap sensitivity subsets.",
            "- Episode no-event cases are represented with `has_event = 0`, zero duration summaries, and undefined time-to-event fields.",
            "- Candidate model feature flags are first-pass guidance only; Modeling v2 should still apply leakage-safe feature selection.",
            "",
        ]
    )
    return "\n".join(lines)


def _fraction_coverage_outside_columns(feature_df: pd.DataFrame) -> list[str]:
    outside_columns: list[str] = []
    for column in feature_df.columns:
        lower = column.lower()
        is_fraction_or_coverage = (
            lower.endswith("_fraction")
            or "_frac_" in lower
            or lower.endswith("_coverage_fraction")
        )
        if not is_fraction_or_coverage or not pd.api.types.is_numeric_dtype(feature_df[column]):
            continue
        values = pd.to_numeric(feature_df[column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if not values.empty and bool(((values < 0) | (values > 1)).any()):
            outside_columns.append(column)
    return outside_columns


def _infinite_numeric_value_count(feature_df: pd.DataFrame) -> int:
    total = 0
    for column in feature_df.select_dtypes(include=["number"]).columns:
        values = pd.to_numeric(feature_df[column], errors="coerce")
        total += int(np.isinf(values).sum())
    return total


def _build_legacy_monitoring_features_full_summary_markdown(
    feature_df: pd.DataFrame,
    *,
    max_hr_bpm: float,
    gap_break_minutes: float,
    min_valid_minutes: int,
    min_paired_minutes: int,
    min_sleep_duration_hours: float = 2.0,
    max_sleep_duration_hours: float = 16.0,
    min_wake_duration_hours: float = 6.0,
    max_wake_duration_hours: float = 30.0,
    boundary_gap_tolerance_minutes: float = 60.0,
    endpoint_band_minutes: float = 30.0,
    endpoint_search_horizon_minutes: float = 90.0,
    catalog_df: pd.DataFrame | None = None,
    catalog_csv_path: str = "reports/monitoring_features_full_catalog.csv",
    catalog_md_path: str = "reports/monitoring_features_full_catalog.md",
) -> str:
    """Build a privacy-safe aggregate summary for the wide Packet 03 feature table."""
    if catalog_df is None:
        catalog_df = build_monitoring_feature_catalog(feature_df) if not feature_df.empty else pd.DataFrame(columns=CATALOG_COLUMNS)

    constant_non_null_count = (
        int((catalog_df["is_constant_non_null"] == True).sum()) if "is_constant_non_null" in catalog_df.columns else 0
    )
    mostly_missing_count = (
        int((catalog_df["missing_pct"] >= 90.0).sum()) if "missing_pct" in catalog_df.columns else 0
    )
    all_null_count = int((catalog_df["is_all_null"] == True).sum()) if "is_all_null" in catalog_df.columns else 0
    feature_family_count = int(catalog_df["family"].nunique()) if "family" in catalog_df.columns else 0
    numeric_column_count = int(feature_df.select_dtypes(include=["number"]).shape[1])
    fraction_coverage_outside_columns = _fraction_coverage_outside_columns(feature_df)
    duplicate_column_count = int(feature_df.columns.duplicated().sum())
    duplicate_date_count = (
        int(pd.to_datetime(feature_df["calendarDate"], errors="coerce").duplicated().sum())
        if "calendarDate" in feature_df.columns
        else 0
    )
    infinite_numeric_count = _infinite_numeric_value_count(feature_df)

    def flag_count(column: str) -> int:
        if column not in feature_df.columns:
            return 0
        return int((pd.to_numeric(feature_df[column], errors="coerce") == 1).sum())

    wake_gt_24_count = (
        flag_count("wake_duration_gt_24h")
        if "wake_duration_gt_24h" in feature_df.columns
        else int((pd.to_numeric(feature_df.get("wake_duration_hours", pd.Series(dtype=float)), errors="coerce") > 24).sum())
    )
    wake_gt_30_count = (
        flag_count("wake_duration_gt_30h")
        if "wake_duration_gt_30h" in feature_df.columns
        else int((pd.to_numeric(feature_df.get("wake_duration_hours", pd.Series(dtype=float)), errors="coerce") > 30).sum())
    )
    wake_gt_48_count = (
        flag_count("wake_duration_gt_48h")
        if "wake_duration_gt_48h" in feature_df.columns
        else int((pd.to_numeric(feature_df.get("wake_duration_hours", pd.Series(dtype=float)), errors="coerce") > 48).sum())
    )
    family_examples = {
        "Semantic window quality": [
            "sleep_duration_plausible",
            "wake_duration_plausible",
            "semantic_window_plausible",
            "wake_duration_gt_24h",
        ],
        "Distribution and shape": [
            "sleep_hr_p05",
            "wake_stress_iqr",
            "sleep_hr_histogram_entropy",
            "wake_stress_mad",
        ],
        "Stress states and HR zones": [
            "wake_stress_frac_high_76_100",
            "sleep_stress_frac_resting_0_25",
            "wake_hr_frac_zone2_60_70",
            "wake_hr_frac_above_mhr",
        ],
        "Gap-aware variability": [
            "wake_hr_mean_abs_diff",
            "wake_stress_roughness",
            "sleep_hr_diff_gap_break_count",
            "wake_stress_longest_missing_gap_minutes",
        ],
        "Episodes and state structure": [
            "wake_stress_high_episode_count",
            "wake_stress_elevated_total_minutes",
            "wake_hr_zone1_plus_episode_count",
            "sleep_stress_state_transition_count",
        ],
        "Recovery and windows": [
            "sleep_hr_first_60m_minus_last_60m",
            "pre_sleep_4h_stress_mean",
            "evening_deactivation_hr",
            "wake_q4_stress_high_fraction",
        ],
        "Trends and contrasts": [
            "wake_stress_slope_per_hour",
            "sleep_hr_end_minus_start",
            "wake_hr_endpoint_contrast_defined",
            "wake_stress_start_endpoint_offset_minutes",
            "hr_wake_mean_minus_sleep_mean",
        ],
        "HR/stress coupling": [
            "wake_paired_hr_stress_valid_minutes",
            "wake_hr_stress_corr",
            "wake_frac_hr_zone1_plus_stress_elevated",
            "sleep_stress_hr_slope",
        ],
        "Raw stress status": [
            "wake_stress_raw_minus_1_fraction",
            "wake_stress_raw_minus_2_fraction",
            "wake_stress_large_motion_proxy_fraction",
            "sleep_stress_raw_valid_fraction",
        ],
    }
    present_examples = {
        family: [column for column in examples if column in feature_df.columns]
        for family, examples in family_examples.items()
    }

    coverage_lines = [
        line
        for column in [
            "sleep_hr_coverage_fraction",
            "wake_hr_coverage_fraction",
            "sleep_stress_coverage_fraction",
            "wake_stress_coverage_fraction",
            "sleep_paired_hr_stress_coverage_fraction",
            "wake_paired_hr_stress_coverage_fraction",
        ]
        if (line := _median_line(feature_df, column)) is not None
    ]
    diagnostic_lines = [
        line
        for column in [
            "wake_stress_frac_high_76_100",
            "wake_hr_frac_zone2_plus",
            "wake_stress_raw_minus_1_fraction",
            "wake_stress_raw_minus_2_fraction",
            "wake_stress_large_motion_proxy_fraction",
            "wake_stress_high_episode_count",
            "wake_hr_mean_abs_diff",
            "stress_wake_mean_minus_sleep_mean",
        ]
        if (line := _median_line(feature_df, column)) is not None
    ]

    lines = [
        "# Monitoring Full Features Summary",
        "",
        "This report summarizes the local Packet 03 wide monitoring feature table built after semantic-window quality normalization. It contains aggregate diagnostics only.",
        "",
        "## Outputs",
        "",
        "- `data/processed/monitoring_features_full_v0.parquet`",
        f"- `{catalog_csv_path}`",
        f"- `{catalog_md_path}`",
        "",
        "## Build Parameters",
        "",
        f"- Maximum heart rate parameter: `{max_hr_bpm:g}` bpm",
        f"- Gap break threshold: `{gap_break_minutes:g}` minutes",
        f"- Minimum valid minutes for window/trend summaries: `{min_valid_minutes}`",
        f"- Minimum paired HR/stress minutes for correlation/regression: `{min_paired_minutes}`",
        f"- Sleep duration plausibility bounds: `{min_sleep_duration_hours:g}` to `{max_sleep_duration_hours:g}` hours",
        f"- Wake duration plausibility bounds: `{min_wake_duration_hours:g}` to `{max_wake_duration_hours:g}` hours",
        f"- Boundary coverage tolerance: `{boundary_gap_tolerance_minutes:g}` minutes",
        f"- Endpoint contrast band/search horizon: `{endpoint_band_minutes:g}` / `{endpoint_search_horizon_minutes:g}` minutes",
        "",
        "## Table Shape",
        "",
        f"- Rows: `{len(feature_df):,}`",
        f"- Columns: `{feature_df.shape[1]:,}`",
        f"- Calendar date range: `{_date_range(feature_df)}`",
        "",
        "## Catalog Diagnostics",
        "",
        f"- Feature families: `{feature_family_count}`",
        f"- Numeric columns: `{numeric_column_count}`",
        f"- Duplicate columns: `{duplicate_column_count}`",
        f"- Duplicate dates: `{duplicate_date_count}`",
        f"- Infinite numeric values: `{infinite_numeric_count}`",
        f"- Constant non-null columns: `{constant_non_null_count}`",
        f"- Mostly missing columns (`missing_pct >= 90`): `{mostly_missing_count}`",
        f"- All-null columns: `{all_null_count}`",
        f"- Fraction/coverage columns outside `0..1`: `{len(fraction_coverage_outside_columns)}`",
        "",
        "Constant columns are diagnostics and will be filtered or selected intentionally in later EDA/modeling steps.",
        "",
        "## Quality Join Policy",
        "",
        "- Row-level filtering and semantic-window quality live in `data/processed/monitoring_quality_index.parquet`.",
        "- Join this table to the quality index on `analysis_window_id` before modeling or final EDA filtering.",
        "- This full feature table does not duplicate `semantic_window_plausible` or coverage eligibility flags as model-candidate columns.",
        f"- Feature rows with wake duration `> 24h`: `{wake_gt_24_count:,}`",
        f"- Feature rows with wake duration `> 30h`: `{wake_gt_30_count:,}`",
        f"- Feature rows with wake duration `> 48h`: `{wake_gt_48_count:,}`",
        "- No-event episode cases are represented separately from missingness: `has_event = 0`, zero duration summaries, and undefined timing-to-event fields.",
        "- Raw stress `-2` is an active proxy only with same-minute valid HR; otherwise it remains unmeasurable/status, not numeric stress or high stress.",
        "- Very long wake windows are flagged as plausibility failures; they usually indicate a missing next sleep record, so wake-relative windows and trends should not be read as normal day structure.",
        "- Endpoint contrasts are robust endpoint-band contrasts that search near the boundary for usable data, not single boundary-point differences.",
        "- Downstream feature selection should filter by the semantic-window and boundary-quality flags before interpreting window-heavy features.",
        "",
        "## Entropy Policy",
        "",
        "- Stress histogram entropy uses fixed Garmin-like stress-state bins over valid `0..100` values: `0..25`, `26..50`, `51..75`, and `76..100`.",
        "- HR histogram entropy uses fixed maximum-heart-rate zone bins derived from `max_hr_bpm`: below 50%, 50..60%, 60..70%, 70..80%, 80..90%, 90..100%, and above 100% MHR.",
        "- Entropy is comparable across days for a fixed `max_hr_bpm`; it does not use per-day dynamic min/max bin edges.",
        "",
        "## Feature Families",
        "",
    ]
    for family, examples in present_examples.items():
        if not examples:
            continue
        rendered = ", ".join(f"`{column}`" for column in examples) if examples else "no example columns present"
        lines.append(f"- {family}: {rendered}")

    lines.extend(
        [
            "",
            "## Coverage Diagnostics",
            "",
        ]
    )
    lines.extend(coverage_lines or ["- No coverage diagnostics available."])
    lines.extend(
        [
            "",
            "## Selected Summary Diagnostics",
            "",
        ]
    )
    lines.extend(diagnostic_lines or ["- No summary diagnostics available."])
    lines.extend(
        [
            "",
            "## Scope Notes",
            "",
            "- Numeric stress features use only valid `0..100` stress values.",
            "- Raw stress `-1` and raw `-2` without same-minute valid HR are represented only as status/quality diagnostics.",
            "- The `-2` large-motion proxy is not treated as activity ground truth or high stress.",
            "- This packet does not add composite scores, bands, spectral features, SQL mart changes, or supervised modeling lag features.",
            "",
        ]
    )
    return "\n".join(lines)
