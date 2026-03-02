from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from ..eda.prepare import add_derived_features, load_daily_sanitized, load_quality

DEFAULT_LOW_RECOVERY_THRESHOLD = 70.0

RECOVERY_FEATURE_TIERS: dict[str, tuple[str, ...]] = {
    "tier1": (
        "totalSteps",
        "totalDistanceMeters",
        "activeKilocalories",
        "activeSeconds",
        "highlyActiveSeconds",
        "active_hours",
        "highly_active_hours",
        "restingHeartRate",
        "minHeartRate",
        "maxHeartRate",
        "bodyBatteryLowest",
        "bodyBatteryHighest",
        "bodyBattery_chargedValue",
        "bodyBattery_drainedValue",
        "bodyBatteryNetBalance",
        "floorsAscendedInMeters",
        "floorsDescendedInMeters",
        "dayofweek",
        "day_of_week",
        "weekday_name",
        "is_weekend",
    ),
    "tier2_compact": (
        "awakeAverageStressLevel",
        "awakeActivityHours",
        "awakeMeasuredHours",
        "awakeHighStressShare",
        "awakeRestShare",
    ),
    "tier2": (
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
    ),
    "tier3": (
        "allDayStress_AWAKE_averageStressLevelIntensity",
        "allDayStress_AWAKE_stressIntensityCount",
        "allDayStress_AWAKE_stressOffWristCount",
        "allDayStress_AWAKE_stressTooActiveCount",
        "allDayStress_AWAKE_totalStressCount",
        "allDayStress_AWAKE_totalStressIntensity",
    ),
}

RECOVERY_SCHEDULE_FEATURES: tuple[str, ...] = (
    "nextsleep_sleep_start_hour_local_wrapped",
    "nextsleep_sleep_opportunity_hours",
)

RECOVERY_SLEEP_TARGET_COLUMNS: tuple[str, ...] = (
    "sleepRecoveryScore",
    "sleepOverallScore",
    "sleepQualityScore",
    "avgSleepStress",
    "sleep_start_hour_local_wrapped",
    "sleep_opportunity_hours",
)

BINARY_TARGET_DIRECTIONS: frozenset[str] = frozenset({"lt", "le", "gt", "ge"})


def _normalize_calendar_date(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if isinstance(parsed.dtype, pd.DatetimeTZDtype):
        parsed = parsed.dt.tz_localize(None)
    return parsed.dt.normalize()


def _ensure_unique_calendar_date(df: pd.DataFrame, label: str) -> None:
    dupes = int(df["calendarDate"].duplicated().sum())
    if dupes > 0:
        raise ValueError(f"{label} has duplicate calendarDate rows: {dupes}")


def _join_daily_quality(daily_df: pd.DataFrame, quality_df: pd.DataFrame) -> pd.DataFrame:
    if "calendarDate" not in daily_df.columns:
        raise KeyError("daily_df is missing calendarDate")
    if "calendarDate" not in quality_df.columns:
        raise KeyError("quality_df is missing calendarDate")

    daily = daily_df.copy()
    quality = quality_df.copy()
    daily["calendarDate"] = _normalize_calendar_date(daily["calendarDate"])
    quality["calendarDate"] = _normalize_calendar_date(quality["calendarDate"])
    _ensure_unique_calendar_date(daily, "daily")
    _ensure_unique_calendar_date(quality, "quality")

    quality_cols = [c for c in quality.columns if c == "calendarDate" or c not in daily.columns]
    return daily.merge(quality[quality_cols], on="calendarDate", how="left")


def _ensure_activity_duration_hours(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "activeSeconds" in out.columns and "active_hours" not in out.columns:
        out["active_hours"] = pd.to_numeric(out["activeSeconds"], errors="coerce") / 3600.0
    if "highlyActiveSeconds" in out.columns and "highly_active_hours" not in out.columns:
        out["highly_active_hours"] = pd.to_numeric(out["highlyActiveSeconds"], errors="coerce") / 3600.0
    return out


def _ensure_step_length(frame: pd.DataFrame, *, min_steps: int = 1000) -> pd.DataFrame:
    out = frame.copy()
    if {"totalSteps", "totalDistanceMeters"}.issubset(out.columns) and "step_length_m" not in out.columns:
        steps = pd.to_numeric(out["totalSteps"], errors="coerce")
        dist = pd.to_numeric(out["totalDistanceMeters"], errors="coerce")
        out["step_length_m"] = np.where(steps >= min_steps, dist / steps, np.nan)
    return out


def _ensure_bodybattery_aliases(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "bodyBattery_chargedValue" in out.columns and "bodyBatteryCharged" not in out.columns:
        out["bodyBatteryCharged"] = pd.to_numeric(out["bodyBattery_chargedValue"], errors="coerce")
    if "bodyBattery_drainedValue" in out.columns and "bodyBatteryDrained" not in out.columns:
        out["bodyBatteryDrained"] = pd.to_numeric(out["bodyBattery_drainedValue"], errors="coerce")
    if "bodyBatteryCharged" in out.columns and "bodyBatteryDrained" in out.columns and "bodyBatteryNetBalance" not in out.columns:
        out["bodyBatteryNetBalance"] = (
            pd.to_numeric(out["bodyBatteryCharged"], errors="coerce")
            - pd.to_numeric(out["bodyBatteryDrained"], errors="coerce")
        )
    return out


def _ensure_stress_context_features(frame: pd.DataFrame, context: str, *, prefix: str) -> pd.DataFrame:
    """Create readable aliases plus hours/shares for Garmin allDayStress_<CONTEXT> fields."""
    out = frame.copy()
    base = f"allDayStress_{context}_"

    avg_col = base + "averageStressLevel"
    if avg_col in out.columns:
        out[f"{prefix}AverageStressLevel"] = pd.to_numeric(out[avg_col], errors="coerce")

    duration_alias = {
        "activityDuration": f"{prefix}ActivityHours",
        "lowDuration": f"{prefix}LowStressHours",
        "mediumDuration": f"{prefix}MediumStressHours",
        "highDuration": f"{prefix}HighStressHours",
        "restDuration": f"{prefix}RestHours",
        "uncategorizedDuration": f"{prefix}UncatHours",
        "totalDuration": f"{prefix}MeasuredHours",
    }
    for raw_suffix, alias in duration_alias.items():
        raw_col = base + raw_suffix
        if raw_col in out.columns:
            out[alias] = pd.to_numeric(out[raw_col], errors="coerce") / 3600.0

    total_col = f"{prefix}MeasuredHours"
    if total_col in out.columns:
        total = pd.to_numeric(out[total_col], errors="coerce")
        for stem in ["Activity", "LowStress", "MediumStress", "HighStress", "Rest", "Uncat"]:
            hcol = f"{prefix}{stem}Hours"
            scol = f"{prefix}{stem}Share"
            if hcol in out.columns:
                numer = pd.to_numeric(out[hcol], errors="coerce")
                out[scol] = np.nan
                mask = total.notna() & numer.notna() & (total > 0)
                if mask.any():
                    out.loc[mask, scol] = numer.loc[mask] / total.loc[mask]
    return out


def _row_garmin_offset_hours(frame: pd.DataFrame) -> pd.Series:
    out = pd.Series(np.nan, index=frame.index, dtype="float64")
    for gmt_col, local_col in [("wellnessStartTimeGmt", "wellnessStartTimeLocal"), ("wellnessEndTimeGmt", "wellnessEndTimeLocal")]:
        if gmt_col in frame.columns and local_col in frame.columns:
            gmt_ts = pd.to_datetime(frame[gmt_col], errors="coerce")
            local_ts = pd.to_datetime(frame[local_col], errors="coerce")
            delta_h = (local_ts - gmt_ts).dt.total_seconds() / 3600.0
            out = out.where(~out.isna(), delta_h)
    return out


def _ensure_sleep_local_time_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "sleepStartTimestampGMT" in out.columns and "sleep_start_hour_local" not in out.columns:
        sleep_start_utc = pd.to_datetime(
            pd.to_numeric(out["sleepStartTimestampGMT"], errors="coerce"),
            unit="s",
            utc=True,
            errors="coerce",
        )
        offset_h = _row_garmin_offset_hours(out)
        local_dt = sleep_start_utc.copy()
        mask = offset_h.notna() & sleep_start_utc.notna()
        if mask.any():
            local_dt.loc[mask] = sleep_start_utc.loc[mask] + pd.to_timedelta(offset_h.loc[mask], unit="h")
        out["sleep_start_hour_local"] = (
            local_dt.dt.hour.astype("float64")
            + local_dt.dt.minute.astype("float64") / 60.0
            + local_dt.dt.second.astype("float64") / 3600.0
        )
    return out


def _ensure_sleep_start_hour_wrapped(
    frame: pd.DataFrame,
    *,
    src_col: str = "sleep_start_hour_local",
    dst_col: str = "sleep_start_hour_local_wrapped",
    wrap_at: float = 18.0,
) -> pd.DataFrame:
    out = frame.copy()
    if src_col not in out.columns:
        return out
    h = pd.to_numeric(out[src_col], errors="coerce")
    out[dst_col] = np.where(h >= wrap_at, h - 24.0, h)
    return out


def _ensure_sleep_opportunity_hours(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    required = {"sleepStartTimestampGMT", "sleepEndTimestampGMT"}
    if required.issubset(out.columns) and "sleep_opportunity_hours" not in out.columns:
        start = pd.to_numeric(out["sleepStartTimestampGMT"], errors="coerce")
        end = pd.to_numeric(out["sleepEndTimestampGMT"], errors="coerce")
        duration_h = (end - start) / 3600.0
        out["sleep_opportunity_hours"] = duration_h.where(duration_h > 0)
    return out


def add_modeling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the shared Stage 3 feature layer from the joined daily dataset."""
    out = add_derived_features(df)
    out = _ensure_step_length(out, min_steps=1000)
    out = _ensure_activity_duration_hours(out)
    out = _ensure_bodybattery_aliases(out)
    out = _ensure_stress_context_features(out, "AWAKE", prefix="awake")
    out = _ensure_stress_context_features(out, "ASLEEP", prefix="sleep")
    out = _ensure_stress_context_features(out, "TOTAL", prefix="total")
    out = _ensure_sleep_local_time_features(out)
    out = _ensure_sleep_start_hour_wrapped(out)
    out = _ensure_sleep_opportunity_hours(out)

    if "calendarDate" in out.columns:
        out["calendarDate"] = _normalize_calendar_date(out["calendarDate"])
        out["day_of_week"] = out["calendarDate"].dt.dayofweek
        out["weekday_name"] = out["calendarDate"].dt.day_name()
        out["is_weekend"] = out["day_of_week"].isin([5, 6]).astype("boolean")

    return out


def prepare_day_to_next_sleep(
    day_frame: pd.DataFrame,
    sleep_frame: pd.DataFrame,
    next_sleep_cols: Sequence[str],
) -> pd.DataFrame:
    """Attach next-night sleep columns to the current day using the Stage 2 D -> D+1 contract."""
    day = day_frame.copy()
    day["calendarDate"] = _normalize_calendar_date(day["calendarDate"])
    day = day.dropna(subset=["calendarDate"])

    sleep = sleep_frame.copy()
    sleep["calendarDate"] = _normalize_calendar_date(sleep["calendarDate"])
    sleep = sleep.dropna(subset=["calendarDate"])
    keep_sleep = ["calendarDate"] + [c for c in next_sleep_cols if c in sleep.columns]
    sleep = sleep[keep_sleep].copy()
    sleep["day_date"] = sleep["calendarDate"] - pd.Timedelta(days=1)
    rename_map = {c: f"nextsleep_{c}" for c in sleep.columns if c not in {"calendarDate", "day_date"}}
    sleep = sleep.rename(columns=rename_map)

    merged = day.merge(
        sleep.drop(columns=["calendarDate"]),
        left_on="calendarDate",
        right_on="day_date",
        how="left",
    )
    if "day_date" in merged.columns:
        merged = merged.drop(columns=["day_date"])
    return merged


def resolve_recovery_feature_columns(
    frame: pd.DataFrame,
    *,
    tiers: Iterable[str] = ("tier1",),
    include_schedule: bool = False,
) -> list[str]:
    """Resolve a deduplicated list of feature columns that exist in the frame."""
    resolved: list[str] = []
    for tier in tiers:
        if tier not in RECOVERY_FEATURE_TIERS:
            raise KeyError(f"Unknown recovery feature tier: {tier}")
        resolved.extend(RECOVERY_FEATURE_TIERS[tier])
    if include_schedule:
        resolved.extend(RECOVERY_SCHEDULE_FEATURES)

    seen: set[str] = set()
    existing: list[str] = []
    for col in resolved:
        if col in frame.columns and col not in seen:
            existing.append(col)
            seen.add(col)
    return existing


def add_binary_threshold_target(
    frame: pd.DataFrame,
    *,
    source_col: str,
    target_col: str,
    threshold: float,
    direction: str = "lt",
) -> pd.DataFrame:
    """Add a binary Int64 target column from a numeric source column and fixed threshold."""
    if direction not in BINARY_TARGET_DIRECTIONS:
        raise ValueError(f"direction must be one of {sorted(BINARY_TARGET_DIRECTIONS)}")
    if source_col not in frame.columns:
        raise KeyError(f"frame missing source column: {source_col}")

    out = frame.copy()
    values = pd.to_numeric(out[source_col], errors="coerce")
    if direction == "lt":
        mask = values.lt(threshold)
    elif direction == "le":
        mask = values.le(threshold)
    elif direction == "gt":
        mask = values.gt(threshold)
    else:
        mask = values.ge(threshold)

    out[target_col] = mask.where(values.notna(), pd.NA).astype("Int64")
    return out


def add_binary_quantile_target(
    frame: pd.DataFrame,
    *,
    source_col: str,
    target_col: str,
    quantile: float,
    tail: str = "upper",
    inclusive: bool = True,
) -> tuple[pd.DataFrame, float]:
    """Add a binary target using an empirical quantile cutoff and return the cutoff."""
    if not 0 < quantile < 1:
        raise ValueError("quantile must be between 0 and 1")
    if tail not in {"lower", "upper"}:
        raise ValueError("tail must be 'lower' or 'upper'")
    if source_col not in frame.columns:
        raise KeyError(f"frame missing source column: {source_col}")

    values = pd.to_numeric(frame[source_col], errors="coerce")
    cutoff = float(values.dropna().quantile(quantile))

    if tail == "lower":
        direction = "le" if inclusive else "lt"
    else:
        direction = "ge" if inclusive else "gt"
    out = add_binary_threshold_target(
        frame,
        source_col=source_col,
        target_col=target_col,
        threshold=cutoff,
        direction=direction,
    )
    return out, cutoff


def build_recovery_modeling_frame(
    daily_df: pd.DataFrame,
    quality_df: pd.DataFrame,
    *,
    current_day_quality: str = "strict",
    low_recovery_threshold: float = DEFAULT_LOW_RECOVERY_THRESHOLD,
    include_schedule_targets: bool = True,
) -> pd.DataFrame:
    """Build a day-level modeling table for `day D -> next-night recovery` tasks."""
    if current_day_quality not in {"strict", "loose"}:
        raise ValueError("current_day_quality must be 'strict' or 'loose'")

    joined = _join_daily_quality(daily_df, quality_df)

    required_quality = {"corrupted_stress_only_day", "has_sleep"}
    missing_quality = [c for c in required_quality if c not in joined.columns]
    if missing_quality:
        raise KeyError(f"joined dataset missing required quality columns: {missing_quality}")

    day_flag_col = "valid_day_strict" if current_day_quality == "strict" else "valid_day_loose"
    if day_flag_col not in joined.columns:
        raise KeyError(f"joined dataset missing required quality column: {day_flag_col}")

    corrupted = joined["corrupted_stress_only_day"].fillna(False).astype(bool)
    current_ok = joined[day_flag_col].fillna(False).astype(bool)
    has_sleep = joined["has_sleep"].fillna(False).astype(bool)

    day_frame = add_modeling_features(joined[current_ok & ~corrupted].copy())
    sleep_frame = add_modeling_features(joined[has_sleep & ~corrupted].copy())

    next_sleep_cols = list(RECOVERY_SLEEP_TARGET_COLUMNS)
    if not include_schedule_targets:
        next_sleep_cols = [c for c in next_sleep_cols if c not in {"sleep_start_hour_local_wrapped", "sleep_opportunity_hours"}]

    modeled = prepare_day_to_next_sleep(day_frame, sleep_frame, next_sleep_cols)

    if "nextsleep_sleepRecoveryScore" in modeled.columns:
        score = pd.to_numeric(modeled["nextsleep_sleepRecoveryScore"], errors="coerce")
        modeled["target_sleepRecoveryScore_next_night"] = score
        modeled["target_low_recovery_next_night"] = (
            score.lt(low_recovery_threshold).where(score.notna(), pd.NA).astype("Int64")
        )

    if "nextsleep_sleepOverallScore" in modeled.columns:
        modeled["target_sleepOverallScore_next_night"] = pd.to_numeric(
            modeled["nextsleep_sleepOverallScore"],
            errors="coerce",
        )

    if "nextsleep_sleepQualityScore" in modeled.columns:
        modeled["target_sleepQualityScore_next_night"] = pd.to_numeric(
            modeled["nextsleep_sleepQualityScore"],
            errors="coerce",
        )

    if "nextsleep_avgSleepStress" in modeled.columns:
        modeled["target_avgSleepStress_next_night"] = pd.to_numeric(
            modeled["nextsleep_avgSleepStress"],
            errors="coerce",
        )

    modeled["model_row_current_quality"] = current_day_quality
    return modeled.sort_values("calendarDate").reset_index(drop=True)


def load_recovery_modeling_frame(
    daily_path: str | Path,
    quality_path: str | Path,
    *,
    current_day_quality: str = "strict",
    low_recovery_threshold: float = DEFAULT_LOW_RECOVERY_THRESHOLD,
    include_schedule_targets: bool = True,
) -> pd.DataFrame:
    """Load parquet inputs and build the Stage 3 recovery modeling frame."""
    daily_df = load_daily_sanitized(daily_path)
    quality_df = load_quality(quality_path)
    return build_recovery_modeling_frame(
        daily_df,
        quality_df,
        current_day_quality=current_day_quality,
        low_recovery_threshold=low_recovery_threshold,
        include_schedule_targets=include_schedule_targets,
    )
