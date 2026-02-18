from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


STRESS_TOTAL_ALIAS_MAP: dict[str, str] = {
    "stress_total_avg_level": "allDayStress_TOTAL_averageStressLevel",
    "stress_total_total_duration_s": "allDayStress_TOTAL_totalDuration",
    "stress_total_stress_duration_s": "allDayStress_TOTAL_stressDuration",
    "stress_total_rest_s": "allDayStress_TOTAL_restDuration",
    "stress_total_low_s": "allDayStress_TOTAL_lowDuration",
    "stress_total_med_s": "allDayStress_TOTAL_mediumDuration",
    "stress_total_high_s": "allDayStress_TOTAL_highDuration",
    "stress_total_activity_s": "allDayStress_TOTAL_activityDuration",
    "stress_total_uncat_s": "allDayStress_TOTAL_uncategorizedDuration",
}


def _normalize_calendar_date(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce")
    if isinstance(parsed.dtype, pd.DatetimeTZDtype):
        parsed = parsed.dt.tz_localize(None)
    return parsed.dt.normalize()


def _ensure_unique_calendar_date(df: pd.DataFrame, label: str) -> None:
    dupes = int(df["calendarDate"].duplicated().sum())
    if dupes > 0:
        raise ValueError(f"{label} has duplicate calendarDate rows: {dupes}")


def load_daily_sanitized(path: str | Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "calendarDate" not in df.columns:
        raise KeyError("daily dataset is missing calendarDate")
    out = df.copy()
    out["calendarDate"] = _normalize_calendar_date(out["calendarDate"])
    _ensure_unique_calendar_date(out, "daily")
    return out


def load_quality(path: str | Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "calendarDate" not in df.columns:
        raise KeyError("quality dataset is missing calendarDate")
    out = df.copy()
    out["calendarDate"] = _normalize_calendar_date(out["calendarDate"])
    _ensure_unique_calendar_date(out, "quality")
    return out


def build_eda_frames(
    daily_df: pd.DataFrame,
    quality_df: pd.DataFrame,
    strict_min_score: int = 4,
    loose_min_score: int = 3,
) -> dict[str, pd.DataFrame]:
    _ = strict_min_score
    _ = loose_min_score

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
    joined = daily.merge(quality[quality_cols], on="calendarDate", how="left")

    required = ["valid_day_strict", "corrupted_stress_only_day", "has_sleep"]
    missing = [c for c in required if c not in joined.columns]
    if missing:
        raise KeyError(f"joined dataset missing required quality columns: {missing}")

    corrupted = joined["corrupted_stress_only_day"].fillna(False).astype(bool)
    strict = joined["valid_day_strict"].fillna(False).astype(bool)
    has_sleep = joined["has_sleep"].fillna(False).astype(bool)

    frames = {
        "df_all": joined,
        "df_strict": joined[strict & ~corrupted].copy(),
        "df_sleep": joined[has_sleep & ~corrupted].copy(),
    }
    return frames


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "calendarDate" not in out.columns:
        raise KeyError("DataFrame is missing calendarDate")

    out["calendarDate"] = _normalize_calendar_date(out["calendarDate"])
    out["date"] = out["calendarDate"]
    out["year"] = out["calendarDate"].dt.year
    out["month"] = out["calendarDate"].dt.month
    out["week"] = out["calendarDate"].dt.isocalendar().week.astype("Int64")
    out["dayofweek"] = out["calendarDate"].dt.dayofweek

    # Readability aliases for stress TOTAL breakdown (keep originals untouched).
    for alias, original in STRESS_TOTAL_ALIAS_MAP.items():
        if original in out.columns and alias not in out.columns:
            out[alias] = out[original]

    if "stressTotalDurationSeconds" in out.columns:
        out["stress_hours"] = pd.to_numeric(out["stressTotalDurationSeconds"], errors="coerce") / 3600.0
    if "stressAwakeDurationSeconds" in out.columns:
        out["awake_stress_hours"] = pd.to_numeric(out["stressAwakeDurationSeconds"], errors="coerce") / 3600.0
    if "totalSteps" in out.columns:
        out["steps_k"] = pd.to_numeric(out["totalSteps"], errors="coerce") / 1000.0
    if "totalDistanceMeters" in out.columns:
        out["distance_km"] = pd.to_numeric(out["totalDistanceMeters"], errors="coerce") / 1000.0
    if "activeSeconds" in out.columns:
        out["active_hours"] = pd.to_numeric(out["activeSeconds"], errors="coerce") / 3600.0

    if "bodyBatteryEndOfDay" in out.columns and "bodyBatteryStartOfDay" in out.columns:
        bb_end = pd.to_numeric(out["bodyBatteryEndOfDay"], errors="coerce")
        bb_start = pd.to_numeric(out["bodyBatteryStartOfDay"], errors="coerce")
        out["bb_delta"] = bb_end - bb_start

    sleep_parts = [
        c
        for c in ["deepSleepSeconds", "lightSleepSeconds", "remSleepSeconds", "awakeSleepSeconds"]
        if c in out.columns
    ]
    if sleep_parts:
        sleep_df = out[sleep_parts].apply(pd.to_numeric, errors="coerce")
        out["sleep_total_seconds"] = sleep_df.sum(axis=1, min_count=1)
        out["sleep_total_hours"] = out["sleep_total_seconds"] / 3600.0

        core_cols = [c for c in ["deepSleepSeconds", "lightSleepSeconds", "remSleepSeconds"] if c in sleep_df.columns]
        core_sum = sleep_df[core_cols].sum(axis=1, min_count=1) if core_cols else pd.Series(np.nan, index=out.index)

        total = out["sleep_total_seconds"]
        valid_total = total.where(total > 0)
        out["sleep_efficiency"] = core_sum / valid_total

        if "deepSleepSeconds" in sleep_df.columns:
            out["deep_pct"] = sleep_df["deepSleepSeconds"] / valid_total
        if "remSleepSeconds" in sleep_df.columns:
            out["rem_pct"] = sleep_df["remSleepSeconds"] / valid_total
        if "lightSleepSeconds" in sleep_df.columns:
            out["light_pct"] = sleep_df["lightSleepSeconds"] / valid_total
        if "awakeSleepSeconds" in sleep_df.columns:
            out["awake_pct"] = sleep_df["awakeSleepSeconds"] / valid_total

    if "latestSpo2Value" in out.columns and "lowestSpo2Value" in out.columns:
        latest = pd.to_numeric(out["latestSpo2Value"], errors="coerce")
        lowest = pd.to_numeric(out["lowestSpo2Value"], errors="coerce")
        out["spo2_gap"] = latest - lowest

    return out


def eda_readiness_summary(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    required = ["df_all", "df_strict", "df_sleep"]
    missing = [name for name in required if name not in frames]
    if missing:
        raise KeyError(f"frames missing required keys: {missing}")

    df_all = frames["df_all"]
    df_strict = frames["df_strict"]
    df_sleep = frames["df_sleep"]

    rows_all = len(df_all)
    rows_strict = len(df_strict)
    rows_sleep = len(df_sleep)

    strict_good_pct = float(rows_strict / rows_all * 100.0) if rows_all else 0.0
    sleep_present_pct = float(rows_sleep / rows_all * 100.0) if rows_all else 0.0

    corrupted_pct = np.nan
    if "corrupted_stress_only_day" in df_all.columns:
        corrupted_pct = float(df_all["corrupted_stress_only_day"].fillna(False).astype(bool).mean() * 100.0)

    return pd.DataFrame(
        [
            {
                "rows_all": rows_all,
                "rows_strict": rows_strict,
                "rows_sleep": rows_sleep,
                "strict_good_pct": strict_good_pct,
                "sleep_present_pct": sleep_present_pct,
                "corrupted_pct": corrupted_pct,
            }
        ]
    )
