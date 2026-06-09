from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .prepare import build_recovery_modeling_frame, resolve_recovery_feature_columns

STAGE4_PRIMARY_TARGET = "target_avgSleepStress_next_sleep"
STAGE4_SPLIT_COLUMN = "split_past_random_valid_future_test"
STAGE4_MODELING_ROW_COLUMN = "stage4_primary_modeling_row"
STAGE4_NON_MODELING_LABEL = "not_eligible_or_missing_target"
STAGE4_SLEEP_START_CONTEXT_FEATURE = "next_sleep_start_hour_local_wrapped"

STAGE4_IDENTITY_COLUMNS: tuple[str, ...] = (
    "analysis_window_id",
    "calendarDate",
    "next_sleep_start_utc",
    "next_sleep_start_local",
    "boundary_confidence",
    "modeling_recovery_v0_eligible",
)

STAGE4_AUDIT_COLUMNS: tuple[str, ...] = (
    "next_sleep_status",
    "wake_end_source",
    "sleep_start_utc",
    "sleep_end_utc",
    "wake_start_utc",
    "wake_end_utc",
    "sleep_start_local",
    "wake_start_local",
    "sleep_duration_hours",
    "wake_duration_hours",
    "pre_sleep_4h_usable",
)

STAGE4_TARGET_COLUMNS: tuple[str, ...] = (
    STAGE4_PRIMARY_TARGET,
    "target_sleepRecoveryScore_next_sleep",
    "target_sleepOverallScore_next_sleep",
    "target_sleepQualityScore_next_sleep",
    "target_sleep_opportunity_hours_next_sleep",
    "target_sleep_start_hour_local_wrapped_next_sleep",
)

STAGE4_CONTEXT_FEATURES: tuple[str, ...] = (STAGE4_SLEEP_START_CONTEXT_FEATURE,)

STAGE4_PREVIOUS_SLEEP_CONTEXT_FEATURES: tuple[str, ...] = (
    "prev_sleep_hours",
    "prev_sleep_avg_stress",
    "prev_sleep_score",
    "prev_sleep_recovery",
    "prev_sleep_start_hour",
    "wake_start_hour",
    "prev_sleep_hr_mean",
    "prev_sleep_hr_std",
    "prev_sleep_stress_mean",
    "prev_sleep_stress_p90",
)

STAGE4_SLEEP_HISTORY_FEATURES: tuple[str, ...] = (
    "hist3_sleep_avg_stress",
    "hist7_sleep_avg_stress",
    "hist3_sleep_score",
    "hist7_sleep_score",
    "hist3_sleep_recovery",
    "hist7_sleep_recovery",
    "hist3_sleep_hours",
    "hist7_sleep_hours",
    "hist3_sleep_count",
    "hist7_sleep_count",
)

STAGE4_STATE_DEVIATION_FEATURES: tuple[str, ...] = (
    "dev7_wake_stress_mean",
    "dev7_presleep_stress_mean",
    "dev7_wake_hr_roughness",
    "dev7_wake_high_stress_min",
    "hist7_wake_count",
)

STAGE4_STATE_CONTEXT_FEATURES: tuple[str, ...] = (
    *STAGE4_PREVIOUS_SLEEP_CONTEXT_FEATURES,
    *STAGE4_SLEEP_HISTORY_FEATURES,
    *STAGE4_STATE_DEVIATION_FEATURES,
)

STAGE4_STATE_CONTEXT_FEATURE_METADATA: Mapping[str, Mapping[str, object]] = {
    "prev_sleep_hours": {
        "family": "previous sleep context",
        "phase": "sleep",
        "window": "previous_sleep",
        "metric": "duration_hours",
        "candidate_model_feature": True,
    },
    "prev_sleep_avg_stress": {
        "family": "previous sleep context",
        "phase": "sleep",
        "window": "previous_sleep",
        "metric": "avg_sleep_stress",
        "candidate_model_feature": True,
    },
    "prev_sleep_score": {
        "family": "previous sleep context",
        "phase": "sleep",
        "window": "previous_sleep",
        "metric": "overall_score",
        "candidate_model_feature": True,
    },
    "prev_sleep_recovery": {
        "family": "previous sleep context",
        "phase": "sleep",
        "window": "previous_sleep",
        "metric": "recovery_score",
        "candidate_model_feature": True,
    },
    "prev_sleep_start_hour": {
        "family": "previous sleep context",
        "phase": "sleep",
        "window": "previous_sleep",
        "metric": "start_hour_local_wrapped",
        "candidate_model_feature": True,
    },
    "wake_start_hour": {
        "family": "previous sleep context",
        "phase": "wake",
        "window": "wake_phase",
        "metric": "start_hour_local_wrapped",
        "candidate_model_feature": True,
    },
    "prev_sleep_hr_mean": {
        "family": "previous sleep context",
        "phase": "sleep",
        "window": "previous_sleep",
        "metric": "hr_mean",
        "candidate_model_feature": True,
    },
    "prev_sleep_hr_std": {
        "family": "previous sleep context",
        "phase": "sleep",
        "window": "previous_sleep",
        "metric": "hr_std",
        "candidate_model_feature": True,
    },
    "prev_sleep_stress_mean": {
        "family": "previous sleep context",
        "phase": "sleep",
        "window": "previous_sleep",
        "metric": "stress_mean",
        "candidate_model_feature": True,
    },
    "prev_sleep_stress_p90": {
        "family": "previous sleep context",
        "phase": "sleep",
        "window": "previous_sleep",
        "metric": "stress_p90",
        "candidate_model_feature": True,
    },
    "hist3_sleep_avg_stress": {
        "family": "recent sleep history",
        "phase": "sleep",
        "window": "prior_3_sleep_observations",
        "metric": "avg_sleep_stress_mean",
        "candidate_model_feature": True,
    },
    "hist7_sleep_avg_stress": {
        "family": "recent sleep history",
        "phase": "sleep",
        "window": "prior_7_sleep_observations",
        "metric": "avg_sleep_stress_mean",
        "candidate_model_feature": True,
    },
    "hist3_sleep_score": {
        "family": "recent sleep history",
        "phase": "sleep",
        "window": "prior_3_sleep_observations",
        "metric": "overall_score_mean",
        "candidate_model_feature": True,
    },
    "hist7_sleep_score": {
        "family": "recent sleep history",
        "phase": "sleep",
        "window": "prior_7_sleep_observations",
        "metric": "overall_score_mean",
        "candidate_model_feature": True,
    },
    "hist3_sleep_recovery": {
        "family": "recent sleep history",
        "phase": "sleep",
        "window": "prior_3_sleep_observations",
        "metric": "recovery_score_mean",
        "candidate_model_feature": True,
    },
    "hist7_sleep_recovery": {
        "family": "recent sleep history",
        "phase": "sleep",
        "window": "prior_7_sleep_observations",
        "metric": "recovery_score_mean",
        "candidate_model_feature": True,
    },
    "hist3_sleep_hours": {
        "family": "recent sleep history",
        "phase": "sleep",
        "window": "prior_3_sleep_observations",
        "metric": "duration_hours_mean",
        "candidate_model_feature": True,
    },
    "hist7_sleep_hours": {
        "family": "recent sleep history",
        "phase": "sleep",
        "window": "prior_7_sleep_observations",
        "metric": "duration_hours_mean",
        "candidate_model_feature": True,
    },
    "hist3_sleep_count": {
        "family": "recent sleep history",
        "phase": "sleep",
        "window": "prior_3_sleep_observations",
        "metric": "available_observation_count",
        "candidate_model_feature": True,
    },
    "hist7_sleep_count": {
        "family": "recent sleep history",
        "phase": "sleep",
        "window": "prior_7_sleep_observations",
        "metric": "available_observation_count",
        "candidate_model_feature": True,
    },
    "dev7_wake_stress_mean": {
        "family": "current day baseline deviation",
        "phase": "wake",
        "window": "wake_phase_minus_prior_7",
        "metric": "stress_mean_delta",
        "candidate_model_feature": True,
    },
    "dev7_presleep_stress_mean": {
        "family": "current day baseline deviation",
        "phase": "wake/pre-sleep",
        "window": "pre_sleep_4h_minus_prior_7",
        "metric": "stress_mean_delta",
        "candidate_model_feature": True,
    },
    "dev7_wake_hr_roughness": {
        "family": "current day baseline deviation",
        "phase": "wake",
        "window": "wake_phase_minus_prior_7",
        "metric": "hr_roughness_delta",
        "candidate_model_feature": True,
    },
    "dev7_wake_high_stress_min": {
        "family": "current day baseline deviation",
        "phase": "wake",
        "window": "wake_phase_minus_prior_7",
        "metric": "high_stress_minutes_delta",
        "candidate_model_feature": True,
    },
    "hist7_wake_count": {
        "family": "current day baseline deviation",
        "phase": "wake/pre-sleep",
        "window": "prior_7_wake_observations",
        "metric": "available_observation_count",
        "candidate_model_feature": True,
    },
}

AGGREGATE_DIRECT_MONITORING_TOKENS: tuple[str, ...] = (
    "heartrate",
    "stress",
    "allDayStress",
    "awakeAverageStressLevel",
    "awakeActivityHours",
    "awakeLowStressHours",
    "awakeMediumStressHours",
    "awakeHighStressHours",
    "awakeRestHours",
    "awakeUncatHours",
    "awakeMeasuredHours",
    "awakeActivityShare",
    "awakeLowStressShare",
    "awakeMediumStressShare",
    "awakeHighStressShare",
    "awakeRestShare",
    "awakeUncatShare",
)

AGGREGATE_BASELINE_EXTRA_COLUMNS: tuple[str, ...] = (
    "moderateIntensityMinutes",
    "vigorousIntensityMinutes",
)

AGGREGATE_BASELINE_EXCLUDED_COLUMNS: frozenset[str] = frozenset(
    {
        "activeSeconds",
        "highlyActiveSeconds",
        "dayofweek",
        "day_of_week",
        "is_weekend",
        "allDayStress_AWAKE_activityDuration",
        "allDayStress_AWAKE_averageStressLevel",
        "allDayStress_AWAKE_highDuration",
        "allDayStress_AWAKE_lowDuration",
        "allDayStress_AWAKE_mediumDuration",
        "allDayStress_AWAKE_restDuration",
        "allDayStress_AWAKE_stressDuration",
        "allDayStress_AWAKE_maxStressLevel",
        "allDayStress_AWAKE_totalDuration",
        "allDayStress_AWAKE_uncategorizedDuration",
    }
)


@dataclass(frozen=True)
class Stage4ModelingFrameConfig:
    """Configuration for the Stage 4 sleep-outcome modeling frame."""

    aggregate_tiers: tuple[str, ...] = ("tier1", "tier2")
    current_day_quality: str = "strict"
    full_missing_pct_max: float = 30.0
    random_state: int = 42
    train_frac: float = 0.70
    valid_frac: float = 0.15
    test_frac: float = 0.15


@dataclass(frozen=True)
class FeatureSetDefinition:
    """Named feature set for Stage 4 downstream model notebooks."""

    name: str
    columns: tuple[str, ...]
    source: str
    description: str


@dataclass(frozen=True)
class Stage4ModelingFrameResult:
    """Stage 4 modeling frame plus reusable feature-set metadata."""

    frame: pd.DataFrame
    feature_sets: Mapping[str, FeatureSetDefinition]
    aggregate_candidate_review: pd.DataFrame
    split_policy: Mapping[str, Any]


def _normalize_calendar_date(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if isinstance(parsed.dtype, pd.DatetimeTZDtype):
        parsed = parsed.dt.tz_localize(None)
    return parsed.dt.normalize()


def _ensure_unique(df: pd.DataFrame, column: str, label: str) -> None:
    if column not in df.columns:
        raise KeyError(f"{label} is missing required column: {column}")
    dupes = int(df[column].duplicated().sum())
    if dupes > 0:
        raise ValueError(f"{label} has duplicate {column} rows: {dupes}")


def _truthy(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False).astype(bool)
    return series.astype(str).str.lower().isin({"true", "1", "yes", "y"})


def _coerce_timestamp_utc(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if int(numeric.notna().sum()) > 0:
        return pd.to_datetime(numeric, unit="s", errors="coerce", utc=True)
    return pd.to_datetime(series, errors="coerce", utc=True)


def _sleep_target_table(sleep_df: pd.DataFrame) -> pd.DataFrame:
    required = {"sleepStartTimestampGMT", "sleepEndTimestampGMT"}
    missing = sorted(required - set(sleep_df.columns))
    if missing:
        raise KeyError(f"sleep_df missing required columns: {missing}")

    sleep = sleep_df.copy()
    sleep["sleep_start_utc"] = _coerce_timestamp_utc(sleep["sleepStartTimestampGMT"])
    sleep["sleep_end_utc"] = _coerce_timestamp_utc(sleep["sleepEndTimestampGMT"])
    sleep = sleep.dropna(subset=["sleep_start_utc"]).copy()
    _ensure_unique(sleep, "sleep_start_utc", "sleep")

    start = sleep["sleep_start_utc"]
    end = sleep["sleep_end_utc"]
    sleep["target_sleep_opportunity_hours_next_sleep"] = (
        (end - start).dt.total_seconds() / 3600.0
    ).where(end.notna() & (end > start))

    rename = {
        "avgSleepStress": STAGE4_PRIMARY_TARGET,
        "sleepRecoveryScore": "target_sleepRecoveryScore_next_sleep",
        "sleepOverallScore": "target_sleepOverallScore_next_sleep",
        "sleepQualityScore": "target_sleepQualityScore_next_sleep",
    }
    keep = ["sleep_start_utc", "target_sleep_opportunity_hours_next_sleep"]
    for source_col, target_col in rename.items():
        if source_col in sleep.columns:
            sleep[target_col] = pd.to_numeric(sleep[source_col], errors="coerce")
            keep.append(target_col)

    return sleep[keep].copy()


def _sleep_previous_context_table(sleep_df: pd.DataFrame) -> pd.DataFrame:
    required = {"sleepStartTimestampGMT", "sleepEndTimestampGMT"}
    missing = sorted(required - set(sleep_df.columns))
    if missing:
        raise KeyError(f"sleep_df missing required columns: {missing}")

    sleep = sleep_df.copy()
    sleep["sleep_start_utc"] = _coerce_timestamp_utc(sleep["sleepStartTimestampGMT"])
    sleep["sleep_end_utc"] = _coerce_timestamp_utc(sleep["sleepEndTimestampGMT"])
    sleep = sleep.dropna(subset=["sleep_start_utc"]).copy()
    _ensure_unique(sleep, "sleep_start_utc", "sleep")

    start = sleep["sleep_start_utc"]
    end = sleep["sleep_end_utc"]
    sleep["prev_sleep_hours"] = ((end - start).dt.total_seconds() / 3600.0).where(end.notna() & (end > start))

    rename = {
        "avgSleepStress": "prev_sleep_avg_stress",
        "sleepOverallScore": "prev_sleep_score",
        "sleepRecoveryScore": "prev_sleep_recovery",
    }
    keep = ["sleep_start_utc", "prev_sleep_hours"]
    for source_col, target_col in rename.items():
        sleep[target_col] = (
            pd.to_numeric(sleep[source_col], errors="coerce")
            if source_col in sleep.columns
            else pd.Series(np.nan, index=sleep.index, dtype="float64")
        )
        keep.append(target_col)

    return sleep[keep].copy()


def _wrapped_local_hour(series: pd.Series, *, wrap_at: float = 18.0) -> pd.Series:
    local = pd.to_datetime(series, errors="coerce")
    hour = (
        local.dt.hour.astype("float64")
        + local.dt.minute.astype("float64") / 60.0
        + local.dt.second.astype("float64") / 3600.0
    )
    return pd.Series(np.where(hour >= wrap_at, hour - 24.0, hour), index=series.index)


def _prepare_monitoring_identity(quality_df: pd.DataFrame) -> pd.DataFrame:
    quality = quality_df.copy()
    for column in [*STAGE4_IDENTITY_COLUMNS, *STAGE4_AUDIT_COLUMNS]:
        if column not in quality.columns:
            quality[column] = pd.NA

    quality["calendarDate"] = _normalize_calendar_date(quality["calendarDate"])
    for column in ["next_sleep_start_utc", "sleep_start_utc", "sleep_end_utc", "wake_start_utc", "wake_end_utc"]:
        if column in quality.columns:
            quality[column] = pd.to_datetime(quality[column], errors="coerce", utc=True)
    for column in ["next_sleep_start_local", "sleep_start_local", "wake_start_local"]:
        if column in quality.columns:
            quality[column] = pd.to_datetime(quality[column], errors="coerce")
    if "modeling_recovery_v0_eligible" in quality.columns:
        quality["modeling_recovery_v0_eligible"] = (
            pd.to_numeric(quality["modeling_recovery_v0_eligible"], errors="coerce").fillna(0).astype("int64")
        )

    keep = [c for c in [*STAGE4_IDENTITY_COLUMNS, *STAGE4_AUDIT_COLUMNS] if c in quality.columns]
    out = quality[keep].dropna(subset=["analysis_window_id", "calendarDate"]).copy()
    _ensure_unique(out, "analysis_window_id", "monitoring_quality_index")
    return out.sort_values(["calendarDate", "analysis_window_id"]).reset_index(drop=True)


def _prepare_feature_frame(feature_df: pd.DataFrame, *, label: str) -> pd.DataFrame:
    out = feature_df.copy()
    if "analysis_window_id" not in out.columns:
        raise KeyError(f"{label} is missing required column: analysis_window_id")
    _ensure_unique(out, "analysis_window_id", label)
    return out.drop(columns=[c for c in ["calendarDate"] if c in out.columns]).copy()


def _aggregate_modeling_features(
    daily_df: pd.DataFrame | None,
    daily_quality_df: pd.DataFrame | None,
    *,
    config: Stage4ModelingFrameConfig,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    if daily_df is None or daily_quality_df is None:
        return pd.DataFrame(columns=["calendarDate"]), ()

    aggregate = build_recovery_modeling_frame(
        daily_df,
        daily_quality_df,
        current_day_quality=config.current_day_quality,
        include_schedule_targets=False,
    )
    aggregate["calendarDate"] = _normalize_calendar_date(aggregate["calendarDate"])
    columns = resolve_recovery_feature_columns(
        aggregate,
        tiers=config.aggregate_tiers,
        include_schedule=False,
    )
    columns = [*columns, *[column for column in AGGREGATE_BASELINE_EXTRA_COLUMNS if column in aggregate.columns]]
    columns = list(dict.fromkeys(column for column in columns if column not in AGGREGATE_BASELINE_EXCLUDED_COLUMNS))
    prefixed = aggregate[["calendarDate", *columns]].copy()
    rename = {column: f"agg__{column}" for column in columns}
    prefixed = prefixed.rename(columns=rename)
    _ensure_unique(prefixed, "calendarDate", "aggregate modeling frame")
    return prefixed, tuple(rename.values())


def _append_context_features(columns: Sequence[str], frame: pd.DataFrame) -> tuple[str, ...]:
    return tuple(dict.fromkeys([*columns, *[column for column in STAGE4_CONTEXT_FEATURES if column in frame.columns]]))


def _existing_feature_columns(columns: Sequence[str], frame: pd.DataFrame) -> tuple[str, ...]:
    return tuple(column for column in columns if column in frame.columns)


def _wrapped_hour_with_fallback(
    frame: pd.DataFrame,
    preferred_col: str,
    fallback_col: str,
) -> pd.Series:
    preferred = (
        _wrapped_local_hour(frame[preferred_col])
        if preferred_col in frame.columns
        else pd.Series(np.nan, index=frame.index, dtype="float64")
    )
    fallback = (
        _wrapped_local_hour(frame[fallback_col])
        if fallback_col in frame.columns
        else pd.Series(np.nan, index=frame.index, dtype="float64")
    )
    return preferred.combine_first(fallback)


def _prior_rolling_mean(series: pd.Series, window: int) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return values.shift(1).rolling(window=window, min_periods=1).mean()


def _prior_rolling_count(series: pd.Series, window: int) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return values.shift(1).rolling(window=window, min_periods=1).count().fillna(0).astype("int64")


def _add_previous_sleep_context_features(frame: pd.DataFrame, sleep_df: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "sleep_start_utc" in out.columns:
        previous_sleep = _sleep_previous_context_table(sleep_df)
        out = out.merge(previous_sleep, on="sleep_start_utc", how="left")
    else:
        for column in ["prev_sleep_hours", "prev_sleep_avg_stress", "prev_sleep_score", "prev_sleep_recovery"]:
            out[column] = np.nan

    if "sleep_duration_hours" in out.columns:
        out["prev_sleep_hours"] = pd.to_numeric(out["prev_sleep_hours"], errors="coerce").combine_first(
            pd.to_numeric(out["sleep_duration_hours"], errors="coerce")
        )

    out["prev_sleep_start_hour"] = _wrapped_hour_with_fallback(out, "sleep_start_local", "sleep_start_utc")
    out["wake_start_hour"] = _wrapped_hour_with_fallback(out, "wake_start_local", "wake_start_utc")

    sleep_monitoring_sources = {
        "sleep_hr_mean": "prev_sleep_hr_mean",
        "sleep_hr_std": "prev_sleep_hr_std",
        "sleep_stress_mean": "prev_sleep_stress_mean",
        "sleep_stress_p90": "prev_sleep_stress_p90",
    }
    for source_col, target_col in sleep_monitoring_sources.items():
        out[target_col] = (
            pd.to_numeric(out[source_col], errors="coerce")
            if source_col in out.columns
            else pd.Series(np.nan, index=out.index, dtype="float64")
        )

    return out


def _add_recent_sleep_history_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.sort_values(["calendarDate", "analysis_window_id"]).copy()
    source_to_prefix = {
        "prev_sleep_avg_stress": "sleep_avg_stress",
        "prev_sleep_score": "sleep_score",
        "prev_sleep_recovery": "sleep_recovery",
        "prev_sleep_hours": "sleep_hours",
    }
    for source_col, prefix in source_to_prefix.items():
        source = (
            out[source_col]
            if source_col in out.columns
            else pd.Series(np.nan, index=out.index, dtype="float64")
        )
        out[f"hist3_{prefix}"] = _prior_rolling_mean(source, 3)
        out[f"hist7_{prefix}"] = _prior_rolling_mean(source, 7)

    count_source = (
        out["prev_sleep_hours"]
        if "prev_sleep_hours" in out.columns
        else pd.Series(np.nan, index=out.index, dtype="float64")
    )
    out["hist3_sleep_count"] = _prior_rolling_count(count_source, 3)
    out["hist7_sleep_count"] = _prior_rolling_count(count_source, 7)
    return out.sort_index()


def _add_state_deviation_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.sort_values(["calendarDate", "analysis_window_id"]).copy()
    source_to_target = {
        "wake_stress_mean": "dev7_wake_stress_mean",
        "pre_sleep_4h_stress_mean": "dev7_presleep_stress_mean",
        "wake_hr_roughness": "dev7_wake_hr_roughness",
        "wake_stress_high_total_minutes": "dev7_wake_high_stress_min",
    }
    count_frames: list[pd.Series] = []
    for source_col, target_col in source_to_target.items():
        source = (
            pd.to_numeric(out[source_col], errors="coerce")
            if source_col in out.columns
            else pd.Series(np.nan, index=out.index, dtype="float64")
        )
        baseline = _prior_rolling_mean(source, 7)
        out[target_col] = source - baseline
        count_frames.append(_prior_rolling_count(source, 7))

    out["hist7_wake_count"] = (
        pd.concat(count_frames, axis=1).min(axis=1).fillna(0).astype("int64")
        if count_frames
        else pd.Series(0, index=out.index, dtype="int64")
    )
    return out.sort_index()


def _add_state_context_features(frame: pd.DataFrame, sleep_df: pd.DataFrame) -> pd.DataFrame:
    out = _add_previous_sleep_context_features(frame, sleep_df)
    out = _add_recent_sleep_history_features(out)
    return _add_state_deviation_features(out)


def _monitoring_core_wake_pre_sleep_columns(core_df: pd.DataFrame, frame: pd.DataFrame) -> tuple[str, ...]:
    identity = {"analysis_window_id", "calendarDate"}
    columns = [
        column
        for column in core_df.columns
        if column not in identity
        and column in frame.columns
        and (column.startswith("wake_") or column.startswith("pre_sleep_4h_"))
    ]
    return _append_context_features(columns, frame)


def _monitoring_full_wake_pre_sleep_columns(
    full_df: pd.DataFrame,
    full_catalog_df: pd.DataFrame,
    frame: pd.DataFrame,
    *,
    missing_pct_max: float,
) -> tuple[str, ...]:
    if full_catalog_df.empty:
        return _append_context_features(
            [
            column
            for column in full_df.columns
            if column in frame.columns
            and column not in {"analysis_window_id", "calendarDate"}
            and (column.startswith("wake_") or column.startswith("pre_sleep_4h_"))
            ],
            frame,
        )

    catalog = full_catalog_df.copy()
    required = {"column", "candidate_model_feature", "missing_pct", "is_constant_non_null"}
    missing = sorted(required - set(catalog.columns))
    if missing:
        raise KeyError(f"full_catalog_df missing required columns: {missing}")

    phase = catalog["phase"].astype(str) if "phase" in catalog.columns else pd.Series("", index=catalog.index)
    wake_or_presleep = phase.isin(["wake", "wake/pre-sleep"]) | catalog["column"].astype(str).str.startswith(
        ("wake_", "pre_sleep_4h_")
    )
    candidate = _truthy(catalog["candidate_model_feature"])
    constant = _truthy(catalog["is_constant_non_null"])
    missing_pct = pd.to_numeric(catalog["missing_pct"], errors="coerce").fillna(100.0)
    selected = catalog.loc[
        candidate
        & wake_or_presleep
        & ~constant
        & missing_pct.le(missing_pct_max),
        "column",
    ]
    selected_columns = tuple(
        column for column in dict.fromkeys(selected.astype(str)) if column in full_df.columns and column in frame.columns
    )
    return _append_context_features(selected_columns, frame)


def classify_aggregate_feature_for_combined_set(feature: str) -> dict[str, object]:
    """Classify an aggregate feature for the monitoring-plus-aggregate set."""
    base = feature.removeprefix("agg__")
    base_lower = base.lower()
    token_overlap = any(token.lower() in base_lower for token in AGGREGATE_DIRECT_MONITORING_TOKENS)
    if base.startswith("nextsleep_"):
        return {
            "review_group": "next_sleep_schedule_or_target_side",
            "include_in_aggregate_plus_monitoring_full": False,
            "note": "Excluded from the combined predictor set because it belongs to the next sleep side.",
        }
    if token_overlap:
        return {
            "review_group": "direct_monitoring_overlap",
            "include_in_aggregate_plus_monitoring_full": False,
            "note": "Kept in the aggregate baseline, but excluded from the combined set to avoid duplicating wake HR/stress monitoring too directly.",
        }
    return {
        "review_group": "non_overlapping_day_context",
        "include_in_aggregate_plus_monitoring_full": True,
        "note": "Included as aggregate day context alongside monitoring features.",
    }


def build_aggregate_candidate_review(aggregate_columns: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for column in aggregate_columns:
        classification = classify_aggregate_feature_for_combined_set(column)
        rows.append(
            {
                "aggregate_feature": column,
                "source_feature": column.removeprefix("agg__"),
                **classification,
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "aggregate_feature",
            "source_feature",
            "review_group",
            "include_in_aggregate_plus_monitoring_full",
            "note",
        ],
    )


def assign_past_random_valid_future_test(
    frame: pd.DataFrame,
    *,
    date_col: str = "calendarDate",
    eligible_col: str | None = None,
    target_col: str | None = None,
    train_frac: float = 0.70,
    valid_frac: float = 0.15,
    test_frac: float = 0.15,
    random_state: int = 42,
    non_modeling_label: str = STAGE4_NON_MODELING_LABEL,
) -> pd.Series:
    """Assign train/validation/test with a future test block and random past validation."""
    if date_col not in frame.columns:
        raise KeyError(f"frame is missing date column: {date_col}")
    if eligible_col is not None and eligible_col not in frame.columns:
        raise KeyError(f"frame is missing eligibility column: {eligible_col}")
    if target_col is not None and target_col not in frame.columns:
        raise KeyError(f"frame is missing target column: {target_col}")
    if min(train_frac, valid_frac, test_frac) <= 0:
        raise ValueError("train_frac, valid_frac, and test_frac must all be positive")
    if not np.isclose(train_frac + valid_frac + test_frac, 1.0):
        raise ValueError("train_frac + valid_frac + test_frac must equal 1.0")

    dates = pd.to_datetime(frame[date_col], errors="coerce")
    modeling_mask = dates.notna()
    if eligible_col is not None:
        modeling_mask &= pd.to_numeric(frame[eligible_col], errors="coerce").fillna(0).astype(int).eq(1)
    if target_col is not None:
        modeling_mask &= pd.to_numeric(frame[target_col], errors="coerce").notna()

    eligible = frame.loc[modeling_mask].copy()
    eligible[date_col] = dates.loc[modeling_mask]
    eligible = eligible.sort_values([date_col]).reset_index().rename(columns={"index": "_source_index"})
    n_rows = len(eligible)
    if n_rows < 3:
        raise ValueError("need at least 3 modeling rows for past-random/future-test split")

    test_n = max(1, int(round(n_rows * test_frac)))
    valid_n = max(1, int(round(n_rows * valid_frac)))
    if test_n + valid_n >= n_rows:
        overflow = test_n + valid_n - (n_rows - 1)
        valid_n = max(1, valid_n - overflow)

    test_source_indices = eligible.tail(test_n)["_source_index"].to_numpy()
    past = eligible.iloc[: n_rows - test_n].copy()
    if len(past) <= valid_n:
        valid_n = max(1, len(past) - 1)

    rng = np.random.default_rng(random_state)
    valid_positions = set(rng.choice(len(past), size=valid_n, replace=False).tolist())
    valid_source_indices = past.iloc[sorted(valid_positions)]["_source_index"].to_numpy()
    train_source_indices = past.drop(past.index[list(valid_positions)])["_source_index"].to_numpy()

    split = pd.Series(non_modeling_label, index=frame.index, dtype="object")
    split.loc[train_source_indices] = "train"
    split.loc[valid_source_indices] = "valid"
    split.loc[test_source_indices] = "test"
    return split


def build_stage4_sleep_modeling_frame(
    *,
    monitoring_quality_df: pd.DataFrame,
    monitoring_core_df: pd.DataFrame,
    monitoring_full_df: pd.DataFrame,
    sleep_df: pd.DataFrame,
    full_catalog_df: pd.DataFrame | None = None,
    daily_df: pd.DataFrame | None = None,
    daily_quality_df: pd.DataFrame | None = None,
    config: Stage4ModelingFrameConfig | None = None,
) -> Stage4ModelingFrameResult:
    """Build the canonical Stage 4 `day D -> next sleep` modeling frame."""
    config = config or Stage4ModelingFrameConfig()
    full_catalog_df = full_catalog_df if full_catalog_df is not None else pd.DataFrame()

    frame = _prepare_monitoring_identity(monitoring_quality_df)
    sleep_targets = _sleep_target_table(sleep_df).rename(columns={"sleep_start_utc": "_target_sleep_start_utc"})
    frame = frame.merge(
        sleep_targets,
        left_on="next_sleep_start_utc",
        right_on="_target_sleep_start_utc",
        how="left",
    ).drop(columns=["_target_sleep_start_utc"])
    frame[STAGE4_SLEEP_START_CONTEXT_FEATURE] = _wrapped_local_hour(
        frame["next_sleep_start_local"]
    )
    frame["target_sleep_start_hour_local_wrapped_next_sleep"] = frame[STAGE4_SLEEP_START_CONTEXT_FEATURE]

    full_features = _prepare_feature_frame(monitoring_full_df, label="monitoring full features")
    core_features = _prepare_feature_frame(monitoring_core_df, label="monitoring core features")
    frame = frame.merge(full_features, on="analysis_window_id", how="left")
    core_only_columns = [
        column
        for column in core_features.columns
        if column != "analysis_window_id" and column not in frame.columns
    ]
    if core_only_columns:
        frame = frame.merge(core_features[["analysis_window_id", *core_only_columns]], on="analysis_window_id", how="left")

    aggregate_features, aggregate_columns = _aggregate_modeling_features(
        daily_df,
        daily_quality_df,
        config=config,
    )
    if aggregate_columns:
        frame = frame.merge(aggregate_features, on="calendarDate", how="left")

    frame = frame.sort_values(["calendarDate", "analysis_window_id"]).reset_index(drop=True)
    frame = _add_state_context_features(frame, sleep_df)
    frame[STAGE4_MODELING_ROW_COLUMN] = (
        pd.to_numeric(frame["modeling_recovery_v0_eligible"], errors="coerce").fillna(0).astype(int).eq(1)
        & pd.to_numeric(frame[STAGE4_PRIMARY_TARGET], errors="coerce").notna()
    ).astype("int64")
    frame[STAGE4_SPLIT_COLUMN] = assign_past_random_valid_future_test(
        frame,
        eligible_col="modeling_recovery_v0_eligible",
        target_col=STAGE4_PRIMARY_TARGET,
        train_frac=config.train_frac,
        valid_frac=config.valid_frac,
        test_frac=config.test_frac,
        random_state=config.random_state,
    )

    core_columns = _monitoring_core_wake_pre_sleep_columns(monitoring_core_df, frame)
    full_columns = _monitoring_full_wake_pre_sleep_columns(
        monitoring_full_df,
        full_catalog_df,
        frame,
        missing_pct_max=config.full_missing_pct_max,
    )
    aggregate_review = build_aggregate_candidate_review(aggregate_columns)
    combined_aggregate_columns = tuple(
        aggregate_review.loc[
            aggregate_review["include_in_aggregate_plus_monitoring_full"].astype(bool),
            "aggregate_feature",
        ]
    )
    combined_columns = tuple(dict.fromkeys([*full_columns, *combined_aggregate_columns]))
    prev_sleep_columns = _existing_feature_columns(STAGE4_PREVIOUS_SLEEP_CONTEXT_FEATURES, frame)
    history_columns = _existing_feature_columns(STAGE4_SLEEP_HISTORY_FEATURES, frame)
    state_deviation_columns = _existing_feature_columns(STAGE4_STATE_DEVIATION_FEATURES, frame)
    full_plus_prev_sleep_columns = tuple(dict.fromkeys([*full_columns, *prev_sleep_columns]))
    full_plus_history_columns = tuple(dict.fromkeys([*full_columns, *history_columns]))
    full_plus_state_columns = tuple(
        dict.fromkeys([*full_columns, *prev_sleep_columns, *history_columns, *state_deviation_columns])
    )
    aggregate_baseline_columns = _append_context_features(
        tuple(column for column in aggregate_columns if column in frame.columns),
        frame,
    )
    full_plus_state_plus_aggregate_columns = tuple(
        dict.fromkeys([*full_plus_state_columns, *aggregate_baseline_columns])
    )

    feature_sets: dict[str, FeatureSetDefinition] = {
        "aggregate_stage3_baseline": FeatureSetDefinition(
            name="aggregate_stage3_baseline",
            columns=aggregate_baseline_columns,
            source="aggregate Stage 3",
            description="Day-D aggregate JSON-derived features from the existing Stage 3 recovery baseline, prefixed with agg__, plus sleep-start context.",
        ),
        "monitoring_core_wake_pre_sleep": FeatureSetDefinition(
            name="monitoring_core_wake_pre_sleep",
            columns=core_columns,
            source="monitoring core v0",
            description="Compact wake and pre-sleep monitoring features, excluding sleep-phase and quality/debug columns.",
        ),
        "monitoring_full_wake_pre_sleep": FeatureSetDefinition(
            name="monitoring_full_wake_pre_sleep",
            columns=full_columns,
            source="monitoring full v0 catalog",
            description="Catalog-filtered wake and pre-sleep monitoring candidates with missingness and constant-column filters.",
        ),
        "monitoring_full_wake_pre_sleep_plus_prev_sleep": FeatureSetDefinition(
            name="monitoring_full_wake_pre_sleep_plus_prev_sleep",
            columns=full_plus_prev_sleep_columns,
            source="monitoring full v0 plus previous sleep context",
            description="Full monitoring wake/pre-sleep candidates plus compact context from the sleep episode before the wake window.",
        ),
        "monitoring_full_wake_pre_sleep_plus_history": FeatureSetDefinition(
            name="monitoring_full_wake_pre_sleep_plus_history",
            columns=full_plus_history_columns,
            source="monitoring full v0 plus recent sleep history",
            description="Full monitoring wake/pre-sleep candidates plus prior-only rolling sleep history over recent observations.",
        ),
        "monitoring_full_wake_pre_sleep_plus_state": FeatureSetDefinition(
            name="monitoring_full_wake_pre_sleep_plus_state",
            columns=full_plus_state_columns,
            source="monitoring full v0 plus state context",
            description="Full monitoring wake/pre-sleep candidates plus previous-sleep context, recent sleep history, and current-day deviations from prior baselines.",
        ),
        "aggregate_plus_monitoring_full": FeatureSetDefinition(
            name="aggregate_plus_monitoring_full",
            columns=combined_columns,
            source="monitoring full v0 plus aggregate context",
            description="Full monitoring wake/pre-sleep candidates plus non-overlapping aggregate day-context features.",
        ),
        "monitoring_full_wake_pre_sleep_plus_state_plus_aggregate": FeatureSetDefinition(
            name="monitoring_full_wake_pre_sleep_plus_state_plus_aggregate",
            columns=full_plus_state_plus_aggregate_columns,
            source="monitoring full v0 plus state and aggregate context",
            description="Widest legal Stage 4 candidate pool: full monitoring wake/pre-sleep, state-context features, and aggregate Stage 3 baseline columns.",
        ),
    }

    split_policy = {
        "strategy": "past_random_valid_future_test",
        "train_frac": config.train_frac,
        "valid_frac": config.valid_frac,
        "test_frac": config.test_frac,
        "random_state": config.random_state,
        "target_col": STAGE4_PRIMARY_TARGET,
        "eligible_col": "modeling_recovery_v0_eligible",
        "non_modeling_label": STAGE4_NON_MODELING_LABEL,
    }
    return Stage4ModelingFrameResult(
        frame=frame,
        feature_sets=feature_sets,
        aggregate_candidate_review=aggregate_review,
        split_policy=split_policy,
    )


def _markdown_table(rows: Sequence[Mapping[str, object]], columns: Sequence[str]) -> str:
    def fmt(value: object) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, float):
            return f"{value:.3f}"
        return str(value)

    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def split_summary(frame: pd.DataFrame, *, split_col: str = STAGE4_SPLIT_COLUMN) -> pd.DataFrame:
    if split_col not in frame.columns:
        raise KeyError(f"frame is missing split column: {split_col}")
    rows: list[dict[str, object]] = []
    order = ["train", "valid", "test", STAGE4_NON_MODELING_LABEL]
    for split in order:
        subset = frame.loc[frame[split_col] == split].copy()
        if subset.empty:
            continue
        dates = pd.to_datetime(subset["calendarDate"], errors="coerce")
        rows.append(
            {
                "split": split,
                "rows": len(subset),
                "eligible_rows": int(
                    pd.to_numeric(subset.get("modeling_recovery_v0_eligible", 0), errors="coerce")
                    .fillna(0)
                    .astype(int)
                    .sum()
                ),
                "primary_target_rows": int(pd.to_numeric(subset.get(STAGE4_PRIMARY_TARGET), errors="coerce").notna().sum()),
                "start_date": dates.min().date() if dates.notna().any() else pd.NA,
                "end_date": dates.max().date() if dates.notna().any() else pd.NA,
            }
        )
    return pd.DataFrame(rows)


def feature_set_summary(
    frame: pd.DataFrame,
    feature_sets: Mapping[str, FeatureSetDefinition],
    *,
    modeling_mask: pd.Series | None = None,
) -> pd.DataFrame:
    if modeling_mask is None:
        modeling_mask = frame[STAGE4_SPLIT_COLUMN].isin(["train", "valid", "test"]) if STAGE4_SPLIT_COLUMN in frame.columns else pd.Series(True, index=frame.index)

    rows: list[dict[str, object]] = []
    for feature_set in feature_sets.values():
        columns = [column for column in feature_set.columns if column in frame.columns]
        numeric_count = sum(pd.api.types.is_numeric_dtype(frame[column]) or pd.api.types.is_bool_dtype(frame[column]) for column in columns)
        complete_rows = int(frame.loc[modeling_mask, columns].notna().all(axis=1).sum()) if columns else 0
        missing_values = (
            frame.loc[modeling_mask, columns].isna().mean().mul(100.0)
            if columns and bool(modeling_mask.any())
            else pd.Series(dtype="float64")
        )
        rows.append(
            {
                "feature_set": feature_set.name,
                "features": len(columns),
                "numeric_features": int(numeric_count),
                "categorical_features": int(len(columns) - numeric_count),
                "complete_modeling_rows": complete_rows,
                "median_missing_pct_modeling_rows": float(missing_values.median()) if not missing_values.empty else np.nan,
                "max_missing_pct_modeling_rows": float(missing_values.max()) if not missing_values.empty else np.nan,
                "source": feature_set.source,
            }
        )
    return pd.DataFrame(rows)


def build_stage4_feature_set_catalog(
    frame: pd.DataFrame,
    feature_sets: Mapping[str, FeatureSetDefinition],
    *,
    full_catalog_df: pd.DataFrame | None = None,
    aggregate_candidate_review: pd.DataFrame | None = None,
) -> pd.DataFrame:
    full_catalog_df = full_catalog_df if full_catalog_df is not None else pd.DataFrame()
    aggregate_candidate_review = (
        aggregate_candidate_review if aggregate_candidate_review is not None else pd.DataFrame()
    )

    full_lookup = full_catalog_df.set_index("column").to_dict("index") if "column" in full_catalog_df.columns else {}
    aggregate_lookup = (
        aggregate_candidate_review.set_index("aggregate_feature").to_dict("index")
        if "aggregate_feature" in aggregate_candidate_review.columns
        else {}
    )
    modeling_mask = frame[STAGE4_SPLIT_COLUMN].isin(["train", "valid", "test"]) if STAGE4_SPLIT_COLUMN in frame.columns else pd.Series(True, index=frame.index)

    rows: list[dict[str, object]] = []
    for feature_set in feature_sets.values():
        for position, feature in enumerate(feature_set.columns, start=1):
            if feature not in frame.columns:
                continue
            values = frame[feature]
            model_values = frame.loc[modeling_mask, feature]
            full_meta = full_lookup.get(feature, {})
            aggregate_meta = aggregate_lookup.get(feature, {})
            state_context_meta = STAGE4_STATE_CONTEXT_FEATURE_METADATA.get(feature, {})
            context_meta = {
                "family": "schedule/context",
                "phase": "wake/pre-sleep",
                "window": "next_sleep_boundary",
                "metric": "start_hour_local_wrapped",
                "candidate_model_feature": True,
            } if feature in STAGE4_CONTEXT_FEATURES else {}
            rows.append(
                {
                    "feature_set": feature_set.name,
                    "feature_order": position,
                    "feature": feature,
                    "source": feature_set.source,
                    "dtype": str(values.dtype),
                    "non_null_count": int(values.notna().sum()),
                    "missing_pct": float(values.isna().mean() * 100.0),
                    "modeling_non_null_count": int(model_values.notna().sum()),
                    "modeling_missing_pct": float(model_values.isna().mean() * 100.0) if len(model_values) else np.nan,
                    "family": context_meta.get(
                        "family",
                        state_context_meta.get(
                            "family",
                            full_meta.get("family", aggregate_meta.get("review_group", "aggregate")),
                        ),
                    ),
                    "phase": context_meta.get("phase", state_context_meta.get("phase", full_meta.get("phase", "aggregate"))),
                    "window": context_meta.get("window", state_context_meta.get("window", full_meta.get("window", "day_D"))),
                    "metric": context_meta.get(
                        "metric",
                        state_context_meta.get("metric", full_meta.get("metric", feature.removeprefix("agg__"))),
                    ),
                    "candidate_model_feature": context_meta.get(
                        "candidate_model_feature",
                        state_context_meta.get("candidate_model_feature", full_meta.get("candidate_model_feature", True)),
                    ),
                    "aggregate_review_group": aggregate_meta.get("review_group", ""),
                    "included_in_aggregate_plus_monitoring_full": aggregate_meta.get(
                        "include_in_aggregate_plus_monitoring_full",
                        feature in feature_sets.get("aggregate_plus_monitoring_full", FeatureSetDefinition("", (), "", "")).columns,
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_stage4_feature_sets_markdown(
    frame: pd.DataFrame,
    feature_sets: Mapping[str, FeatureSetDefinition],
    feature_catalog_df: pd.DataFrame,
    aggregate_candidate_review: pd.DataFrame,
) -> str:
    summary = feature_set_summary(frame, feature_sets)
    lines = [
        "# Stage 4 Sleep Modeling Feature Sets",
        "",
        "This catalog defines the reusable feature spaces for the Stage 4 sleep-outcome modeling frame. It defines inputs only; no models are fit here.",
        "",
        "## Feature Set Sizes",
        "",
        _markdown_table(summary.to_dict("records"), list(summary.columns)),
        "",
        "## Aggregate Candidate Review",
        "",
        "Aggregate columns are prefixed with `agg__` in the modeling frame. Sleep-start local time is included as schedule context. Direct wake HR/stress overlaps remain available in the aggregate-only baseline, while the combined feature set adds only non-overlapping aggregate day context. The monitoring state-context variants add previous sleep, prior-only sleep history, and prior-baseline deviation features without changing the original feature sets. `hist3_*` and `hist7_*` use prior analysis observations rather than literal calendar-day windows.",
        "",
    ]
    if aggregate_candidate_review.empty:
        lines.append("No aggregate feature columns were available.")
    else:
        review_counts = (
            aggregate_candidate_review.groupby(["review_group", "include_in_aggregate_plus_monitoring_full"], as_index=False)
            .size()
            .rename(columns={"size": "features"})
        )
        lines.append(_markdown_table(review_counts.to_dict("records"), list(review_counts.columns)))

    lines.extend(["", "## Feature Family Counts", ""])
    if feature_catalog_df.empty:
        lines.append("No feature catalog rows were available.")
    else:
        family_counts = (
            feature_catalog_df.groupby(["feature_set", "family"], as_index=False)
            .size()
            .rename(columns={"size": "features"})
            .sort_values(["feature_set", "features", "family"], ascending=[True, False, True])
        )
        lines.append(_markdown_table(family_counts.to_dict("records"), list(family_counts.columns)))
    lines.append("")
    return "\n".join(lines)


def build_stage4_modeling_frame_summary_markdown(
    result: Stage4ModelingFrameResult,
    *,
    output_path: str | Path = "data/processed/stage4_sleep_modeling_frame.parquet",
    feature_catalog_path: str | Path = "reports/stage4_sleep_modeling_feature_sets.csv",
    feature_sets_md_path: str | Path = "reports/stage4_sleep_modeling_feature_sets.md",
) -> str:
    frame = result.frame
    modeling_mask = frame[STAGE4_SPLIT_COLUMN].isin(["train", "valid", "test"])
    eligibility_rows = [
        {
            "metric": "analysis_rows",
            "rows": len(frame),
        },
        {
            "metric": "modeling_recovery_v0_eligible",
            "rows": int(pd.to_numeric(frame["modeling_recovery_v0_eligible"], errors="coerce").fillna(0).astype(int).sum()),
        },
        {
            "metric": "primary_target_available",
            "rows": int(pd.to_numeric(frame[STAGE4_PRIMARY_TARGET], errors="coerce").notna().sum()),
        },
        {
            "metric": "eligible_with_primary_target",
            "rows": int(modeling_mask.sum()),
        },
    ]
    target_rows = [
        {
            "target": target,
            "available_rows": int(pd.to_numeric(frame[target], errors="coerce").notna().sum()) if target in frame.columns else 0,
        }
        for target in STAGE4_TARGET_COLUMNS
    ]
    split_df = split_summary(frame)
    feature_df = feature_set_summary(frame, result.feature_sets, modeling_mask=modeling_mask)

    lines = [
        "# Stage 4 Sleep Outcome Modeling Frame",
        "",
        "This report documents the reusable Stage 4 `day D -> next sleep` modeling frame. It covers row construction, target alignment, feature-set definitions, and the default split contract. It does not fit models or make final predictive claims.",
        "",
        "## Outputs",
        "",
        f"- `{output_path}`",
        f"- `{feature_catalog_path}`",
        f"- `{feature_sets_md_path}`",
        "",
        "## Frame Shape",
        "",
        f"- Rows: `{frame.shape[0]}`",
        f"- Columns: `{frame.shape[1]}`",
        f"- Date range: `{pd.to_datetime(frame['calendarDate']).min().date()} to {pd.to_datetime(frame['calendarDate']).max().date()}`",
        "",
        "## Row And Target Availability",
        "",
        _markdown_table(eligibility_rows, ["metric", "rows"]),
        "",
        "## Target Columns",
        "",
        _markdown_table(target_rows, ["target", "available_rows"]),
        "",
        "Targets are aligned by exact next-sleep start timestamp from the monitoring quality index to the sleep table. The primary target is next-sleep `avgSleepStress`; opportunity and local start-hour targets are retained for audit and future sensitivity work.",
        "",
        "## Default Split",
        "",
        f"- Strategy: `{result.split_policy['strategy']}`",
        f"- Fractions: `{result.split_policy['train_frac']:.2f}/{result.split_policy['valid_frac']:.2f}/{result.split_policy['test_frac']:.2f}`",
        f"- Random seed for past train/validation split: `{result.split_policy['random_state']}`",
        "",
        _markdown_table(split_df.to_dict("records"), list(split_df.columns)),
        "",
        "The test split is the final time block among eligible rows with the primary target. Train and validation rows are assigned randomly inside the earlier history with the fixed seed.",
        "",
        "## Feature Sets",
        "",
        _markdown_table(feature_df.to_dict("records"), list(feature_df.columns)),
        "",
        "## Leakage Controls",
        "",
        "- Monitoring predictors are limited to wake and pre-sleep columns.",
        "- Sleep-phase monitoring columns remain out of the predictor feature sets in this frame.",
        "- Previous-sleep context features use the completed sleep before the wake window, not the modeled next sleep.",
        "- Recent-history and current-day deviation features use prior rows only, with partial windows allowed and first-observation means left missing. `hist3_*` and `hist7_*` refer to prior analysis rows, not fixed calendar-day windows.",
        "- Quality and boundary diagnostics are retained for audit, not as ordinary predictors.",
        "- Sleep-start local time is included as schedule context because the wake/pre-sleep feature window is defined at sleep onset.",
        "- Next-sleep duration/opportunity remains target/audit context, not an ordinary predictor.",
        "- The combined monitoring-plus-aggregate set excludes aggregate wake HR/stress features that duplicate monitoring signals too directly.",
        "",
        "## Limitations",
        "",
        "This is a single-subject observational wearable dataset. The frame is a reproducible modeling input contract, not evidence of final model performance.",
        "",
    ]
    return "\n".join(lines)
