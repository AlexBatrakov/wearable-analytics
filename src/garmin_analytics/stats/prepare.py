from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..eda.prepare import build_eda_frames, load_daily_sanitized, load_quality
from ..modeling.prepare import add_modeling_features, prepare_day_to_next_sleep

WEEKDAY_ORDER_FULL: tuple[str, ...] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

NEXT_SLEEP_VALIDATION_COLUMNS: tuple[str, ...] = (
    "sleepRecoveryScore",
    "sleepAverageStressLevel",
    "avgSleepStress",
    "sleepOverallScore",
    "sleepQualityScore",
    "sleep_start_hour_local_wrapped",
    "sleep_opportunity_hours",
)


def add_sleep_onset_weekday(frame: pd.DataFrame) -> pd.DataFrame:
    """Anchor sleep rows to the sleep-onset day instead of the wake-up day calendarDate."""
    if "calendarDate" not in frame.columns:
        raise KeyError("frame missing calendarDate")

    out = frame.copy()
    out["sleep_onset_date"] = pd.to_datetime(out["calendarDate"], errors="coerce") - pd.Timedelta(days=1)
    out["sleep_onset_date"] = out["sleep_onset_date"].dt.normalize()
    out["sleep_onset_day_of_week"] = out["sleep_onset_date"].dt.dayofweek
    out["sleep_onset_weekday_name"] = pd.Categorical(
        out["sleep_onset_date"].dt.day_name(),
        categories=list(WEEKDAY_ORDER_FULL),
        ordered=True,
    )
    return out


def build_stat_validation_frames(
    daily_df: pd.DataFrame,
    quality_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build the canonical data slices used by Stage 3 statistical validation."""
    frames = build_eda_frames(daily_df, quality_df)

    day_strict = add_modeling_features(frames["df_strict"].copy())
    sleep = add_modeling_features(frames["df_sleep"].copy())
    sleep_onset = add_sleep_onset_weekday(sleep)
    day_nextsleep = prepare_day_to_next_sleep(day_strict, sleep, NEXT_SLEEP_VALIDATION_COLUMNS)

    return {
        "day_strict": day_strict.sort_values("calendarDate").reset_index(drop=True),
        "sleep_onset": sleep_onset.sort_values("calendarDate").reset_index(drop=True),
        "day_nextsleep": day_nextsleep.sort_values("calendarDate").reset_index(drop=True),
    }


def load_stat_validation_frames(
    daily_path: str | Path,
    quality_path: str | Path,
) -> dict[str, pd.DataFrame]:
    daily_df = load_daily_sanitized(daily_path)
    quality_df = load_quality(quality_path)
    return build_stat_validation_frames(daily_df, quality_df)
