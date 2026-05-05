from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .foundation import (
    NEXT_SLEEP_MISSING_AFTER_CUTOFF,
    NEXT_SLEEP_NO_FOLLOWING_OBSERVED,
    NEXT_SLEEP_OBSERVED_WITHIN_CUTOFF,
    SEMANTIC_WINDOW_COLUMNS,
    normalize_heart_rate_frame,
    normalize_stress_frame,
)


@dataclass(frozen=True)
class MonitoringCoreConfig:
    """Configuration for monitoring quality and cleaned feature outputs."""

    max_hr_bpm: float = 192.0
    gap_break_minutes: float = 2.0
    min_valid_minutes: int = 5
    min_paired_minutes: int = 10
    sleep_min_hours: float = 2.0
    sleep_max_hours: float = 16.0
    wake_min_hours: float = 6.0
    wake_max_hours: float = 30.0
    noon_cutoff_hour: int = 12
    max_synthetic_split_gap_hours: float = 60.0
    boundary_gap_tolerance_minutes: float = 60.0
    usable_coverage_fraction: float = 0.50
    usable_max_gap_minutes: float = 360.0


ANALYSIS_WINDOW_COLUMNS = [
    "analysis_window_id",
    "calendarDate",
    "source_calendarDate",
    "local_utc_offset_minutes",
    "local_utc_offset_source",
    "sleep_start_utc",
    "sleep_end_utc",
    "wake_start_utc",
    "wake_end_utc",
    "next_observed_sleep_start_utc",
    "next_sleep_start_utc",
    "sleep_start_local",
    "sleep_end_local",
    "wake_start_local",
    "wake_end_local",
    "next_observed_sleep_start_local",
    "next_sleep_start_local",
    "next_sleep_status",
    "sleep_start_known",
    "sleep_end_known",
    "wake_start_known",
    "wake_end_known",
    "next_sleep_start_known",
    "boundary_confidence",
    "wake_end_source",
    "synthetic_wake_split_utc",
    "synthetic_wake_split_local",
    "unsupported_multi_day_gap",
    "sleep_duration_hours",
    "wake_duration_hours",
    "observed_wake_duration_hours",
]


QUALITY_INDEX_COLUMNS = [
    *ANALYSIS_WINDOW_COLUMNS,
    "sleep_duration_plausible",
    "wake_duration_plausible",
    "semantic_window_plausible",
    "wake_duration_gt_24h",
    "wake_duration_gt_30h",
    "wake_duration_gt_48h",
    "sleep_hr_coverage_fraction",
    "sleep_hr_max_gap_minutes",
    "sleep_hr_start_boundary_covered",
    "sleep_hr_end_boundary_covered",
    "sleep_stress_coverage_fraction",
    "sleep_stress_max_gap_minutes",
    "sleep_stress_start_boundary_covered",
    "sleep_stress_end_boundary_covered",
    "sleep_stress_raw_minus_1_fraction",
    "sleep_stress_raw_minus_2_fraction",
    "sleep_stress_raw_minus_2_with_hr_fraction",
    "sleep_stress_raw_minus_2_without_hr_fraction",
    "sleep_stress_raw_valid_fraction",
    "sleep_stress_active_proxy_fraction",
    "wake_hr_coverage_fraction",
    "wake_hr_max_gap_minutes",
    "wake_hr_start_boundary_covered",
    "wake_hr_end_boundary_covered",
    "wake_stress_coverage_fraction",
    "wake_stress_max_gap_minutes",
    "wake_stress_start_boundary_covered",
    "wake_stress_end_boundary_covered",
    "wake_stress_raw_minus_1_fraction",
    "wake_stress_raw_minus_2_fraction",
    "wake_stress_raw_minus_2_with_hr_fraction",
    "wake_stress_raw_minus_2_without_hr_fraction",
    "wake_stress_raw_valid_fraction",
    "wake_stress_active_proxy_fraction",
    "pre_sleep_4h_hr_coverage_fraction",
    "pre_sleep_4h_hr_max_gap_minutes",
    "pre_sleep_4h_hr_start_boundary_covered",
    "pre_sleep_4h_hr_end_boundary_covered",
    "pre_sleep_4h_stress_coverage_fraction",
    "pre_sleep_4h_stress_max_gap_minutes",
    "pre_sleep_4h_stress_start_boundary_covered",
    "pre_sleep_4h_stress_end_boundary_covered",
    "pre_sleep_4h_stress_raw_minus_1_fraction",
    "pre_sleep_4h_stress_raw_minus_2_fraction",
    "pre_sleep_4h_stress_raw_minus_2_with_hr_fraction",
    "pre_sleep_4h_stress_raw_minus_2_without_hr_fraction",
    "pre_sleep_4h_stress_raw_valid_fraction",
    "pre_sleep_4h_stress_active_proxy_fraction",
    "wake_quarters_hr_min_coverage_fraction",
    "wake_quarters_stress_min_coverage_fraction",
    "wake_quarters_usable",
    "sleep_hr_usable",
    "sleep_stress_usable",
    "wake_hr_usable",
    "wake_stress_usable",
    "pre_sleep_4h_usable",
    "modeling_recovery_v0_eligible",
]


FORBIDDEN_FEATURE_TOKENS = [
    "p05",
    "p95",
    "trimmed_mean",
    "medium_or_high",
    "first_30m_after_wake",
    "first_2h_after_wake",
    "last_2h_before_sleep",
    "last_4h_before_sleep",
    "endpoint",
    "end_minus_start",
    "coverage_fraction",
    "valid_count",
    "total_count",
    "max_gap_minutes",
    "minutes_to_first_valid",
    "minutes_from_last_valid_to_end",
    "raw_minus_1",
    "raw_minus_2",
    "large_motion_proxy",
    "activation_" + "score",
    "activation_" + "band",
    "wake_" + "activation",
    "dominant_" + "frequency",
    "dominant_" + "period",
]


def _flag(value: bool) -> int:
    return int(bool(value))


def _coerce_utc(value: Any) -> pd.Timestamp:
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(ts):
        return pd.NaT
    return pd.Timestamp(ts)


def _offset_minutes(value: Any) -> float:
    if pd.isna(value):
        return 0.0
    return float(value)


def _duration_minutes(start: Any, end: Any) -> float:
    start_ts = _coerce_utc(start)
    end_ts = _coerce_utc(end)
    if pd.isna(start_ts) or pd.isna(end_ts) or start_ts > end_ts:
        return np.nan
    return float((end_ts - start_ts).total_seconds() / 60.0)


def _duration_hours(start: Any, end: Any) -> float:
    minutes = _duration_minutes(start, end)
    return minutes / 60.0 if pd.notna(minutes) else np.nan


def _utc_to_local(ts: Any, offset_minutes: float) -> pd.Timestamp:
    ts = _coerce_utc(ts)
    if pd.isna(ts):
        return pd.NaT
    return pd.Timestamp(ts + pd.Timedelta(minutes=offset_minutes)).tz_localize(None)


def _local_to_utc(local_ts: Any, offset_minutes: float) -> pd.Timestamp:
    ts = pd.to_datetime(local_ts, errors="coerce")
    if pd.isna(ts):
        return pd.NaT
    if getattr(ts, "tzinfo", None) is not None:
        ts = ts.tz_localize(None)
    return pd.Timestamp(ts - pd.Timedelta(minutes=offset_minutes), tz="UTC")


def _normalize_window_frame(semantic_windows_df: pd.DataFrame) -> pd.DataFrame:
    windows = semantic_windows_df.copy()
    for column in SEMANTIC_WINDOW_COLUMNS:
        if column not in windows.columns:
            windows[column] = pd.NA

    for column in ["sleep_start_utc", "sleep_end_utc", "next_observed_sleep_start_utc", "next_sleep_start_utc"]:
        windows[column] = pd.to_datetime(windows[column], errors="coerce", utc=True)
    for column in [
        "calendarDate",
        "sleep_start_local",
        "sleep_end_local",
        "next_observed_sleep_start_local",
        "next_sleep_start_local",
    ]:
        windows[column] = pd.to_datetime(windows[column], errors="coerce")

    windows["calendarDate"] = windows["calendarDate"].dt.normalize()
    windows["local_utc_offset_minutes"] = pd.to_numeric(
        windows["local_utc_offset_minutes"], errors="coerce"
    )
    windows["sleep_duration_hours"] = pd.to_numeric(windows["sleep_duration_hours"], errors="coerce")
    windows["observed_wake_duration_hours"] = pd.to_numeric(
        windows["observed_wake_duration_hours"], errors="coerce"
    )
    windows["wake_duration_hours"] = pd.to_numeric(windows["wake_duration_hours"], errors="coerce")

    missing_observed = windows["next_observed_sleep_start_utc"].isna() & windows["next_sleep_start_utc"].notna()
    windows.loc[missing_observed, "next_observed_sleep_start_utc"] = windows.loc[
        missing_observed, "next_sleep_start_utc"
    ]
    if "next_sleep_status" not in windows.columns:
        windows["next_sleep_status"] = pd.NA
    status_missing = windows["next_sleep_status"].isna()
    windows.loc[status_missing & windows["next_sleep_start_utc"].notna(), "next_sleep_status"] = (
        NEXT_SLEEP_OBSERVED_WITHIN_CUTOFF
    )
    windows.loc[status_missing & windows["next_sleep_start_utc"].isna(), "next_sleep_status"] = (
        NEXT_SLEEP_NO_FOLLOWING_OBSERVED
    )

    observed_missing = windows["observed_wake_duration_hours"].isna()
    observed_duration = (
        windows["next_observed_sleep_start_utc"] - windows["sleep_end_utc"]
    ).dt.total_seconds() / 3600.0
    windows.loc[observed_missing, "observed_wake_duration_hours"] = observed_duration.loc[observed_missing]

    return (
        windows.dropna(subset=["calendarDate", "sleep_start_utc", "sleep_end_utc"])
        .sort_values(["sleep_start_utc", "calendarDate"])
        .reset_index(drop=True)
    )


def _normalize_hr(heart_rate_df: pd.DataFrame | None) -> pd.DataFrame:
    return normalize_heart_rate_frame(heart_rate_df if heart_rate_df is not None else pd.DataFrame())


def _normalize_stress(stress_df: pd.DataFrame | None) -> pd.DataFrame:
    return normalize_stress_frame(stress_df if stress_df is not None else pd.DataFrame())


def _indexed_by_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "timestamp_utc" not in out.columns:
        return out
    out["timestamp_utc"] = pd.to_datetime(out["timestamp_utc"], errors="coerce", utc=True)
    out = out.dropna(subset=["timestamp_utc"]).sort_values("timestamp_utc")
    return out.set_index("timestamp_utc", drop=False)


def _time_slice(df: pd.DataFrame, start: Any, end: Any) -> pd.DataFrame:
    start_ts = _coerce_utc(start)
    end_ts = _coerce_utc(end)
    if df.empty or pd.isna(start_ts) or pd.isna(end_ts) or start_ts >= end_ts:
        return df.iloc[0:0].copy()
    indexed = df if isinstance(df.index, pd.DatetimeIndex) else _indexed_by_timestamp(df)
    subset = indexed.loc[start_ts:end_ts]
    if subset.empty:
        return subset.copy()
    return subset.loc[(subset.index >= start_ts) & (subset.index < end_ts)].copy()


def _noon_cutoff_utc(wake_start_utc: pd.Timestamp, offset_minutes: float, config: MonitoringCoreConfig) -> pd.Timestamp:
    wake_start_local = _utc_to_local(wake_start_utc, offset_minutes)
    cutoff_local = (
        wake_start_local.normalize()
        + pd.Timedelta(days=1)
        + pd.Timedelta(hours=config.noon_cutoff_hour)
    )
    return _local_to_utc(cutoff_local, offset_minutes)


def _has_monitoring_rows(
    heart_rate: pd.DataFrame,
    stress: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> bool:
    return bool(len(_time_slice(heart_rate, start, end)) + len(_time_slice(stress, start, end)))


def _calendar_date_for(local_ts: pd.Timestamp, fallback_utc: pd.Timestamp) -> pd.Timestamp:
    if pd.notna(local_ts):
        return pd.Timestamp(local_ts).normalize()
    return pd.Timestamp(fallback_utc).tz_convert(None).normalize()


def _assert_unique_calendar_dates(frame: pd.DataFrame, *, label: str) -> None:
    if frame.empty or "calendarDate" not in frame.columns:
        return
    dates = pd.to_datetime(frame["calendarDate"], errors="coerce").dt.normalize()
    duplicated = dates[dates.duplicated(keep=False)]
    if duplicated.empty:
        return
    examples = sorted(str(ts.date()) for ts in duplicated.dropna().drop_duplicates().head(5))
    raise ValueError(f"{label} has duplicate calendarDate rows after analysis-window construction: {examples}")


def _analysis_row(
    *,
    idx: int,
    segment: str,
    calendar_date: pd.Timestamp,
    source_row: pd.Series,
    sleep_start_utc: pd.Timestamp,
    sleep_end_utc: pd.Timestamp,
    wake_start_utc: pd.Timestamp,
    wake_end_utc: pd.Timestamp,
    next_observed_sleep_start_utc: pd.Timestamp,
    next_sleep_start_utc: pd.Timestamp,
    sleep_start_known: bool,
    sleep_end_known: bool,
    wake_start_known: bool,
    wake_end_known: bool,
    next_sleep_start_known: bool,
    boundary_confidence: str,
    wake_end_source: str,
    synthetic_wake_split_utc: pd.Timestamp = pd.NaT,
    unsupported_multi_day_gap: bool = False,
) -> dict[str, Any]:
    offset = _offset_minutes(source_row.get("local_utc_offset_minutes", np.nan))
    source_calendar_date = pd.Timestamp(source_row.get("calendarDate")).normalize()
    calendar_date = pd.Timestamp(calendar_date).normalize()
    synthetic_local = _utc_to_local(synthetic_wake_split_utc, offset)
    observed_wake_duration = source_row.get("observed_wake_duration_hours", np.nan)
    if pd.isna(observed_wake_duration):
        observed_wake_duration = _duration_hours(source_row.get("sleep_end_utc"), next_observed_sleep_start_utc)

    return {
        "analysis_window_id": f"{source_calendar_date.date()}_{idx:04d}_{segment}",
        "calendarDate": calendar_date,
        "source_calendarDate": source_calendar_date,
        "local_utc_offset_minutes": source_row.get("local_utc_offset_minutes", pd.NA),
        "local_utc_offset_source": source_row.get("local_utc_offset_source", "missing"),
        "sleep_start_utc": sleep_start_utc,
        "sleep_end_utc": sleep_end_utc,
        "wake_start_utc": wake_start_utc,
        "wake_end_utc": wake_end_utc,
        "next_observed_sleep_start_utc": next_observed_sleep_start_utc,
        "next_sleep_start_utc": next_sleep_start_utc,
        "sleep_start_local": _utc_to_local(sleep_start_utc, offset),
        "sleep_end_local": _utc_to_local(sleep_end_utc, offset),
        "wake_start_local": _utc_to_local(wake_start_utc, offset),
        "wake_end_local": _utc_to_local(wake_end_utc, offset),
        "next_observed_sleep_start_local": _utc_to_local(next_observed_sleep_start_utc, offset),
        "next_sleep_start_local": _utc_to_local(next_sleep_start_utc, offset),
        "next_sleep_status": source_row.get("next_sleep_status", pd.NA),
        "sleep_start_known": _flag(sleep_start_known),
        "sleep_end_known": _flag(sleep_end_known),
        "wake_start_known": _flag(wake_start_known),
        "wake_end_known": _flag(wake_end_known),
        "next_sleep_start_known": _flag(next_sleep_start_known),
        "boundary_confidence": boundary_confidence,
        "wake_end_source": wake_end_source,
        "synthetic_wake_split_utc": synthetic_wake_split_utc,
        "synthetic_wake_split_local": synthetic_local,
        "unsupported_multi_day_gap": _flag(unsupported_multi_day_gap),
        "sleep_duration_hours": _duration_hours(sleep_start_utc, sleep_end_utc),
        "wake_duration_hours": _duration_hours(wake_start_utc, wake_end_utc),
        "observed_wake_duration_hours": observed_wake_duration,
    }


def build_monitoring_analysis_windows(
    semantic_windows_df: pd.DataFrame,
    heart_rate_df: pd.DataFrame | None = None,
    stress_df: pd.DataFrame | None = None,
    *,
    config: MonitoringCoreConfig | None = None,
) -> pd.DataFrame:
    """Build explicit analysis windows without treating missed sleep as normal wake."""
    config = config or MonitoringCoreConfig()
    windows = _normalize_window_frame(semantic_windows_df)
    heart_rate = _indexed_by_timestamp(_normalize_hr(heart_rate_df))
    stress = _indexed_by_timestamp(_normalize_stress(stress_df))
    source_calendar_dates = set(pd.to_datetime(windows["calendarDate"], errors="coerce").dt.normalize().dropna())
    rows: list[dict[str, Any]] = []

    for idx, source in enumerate(windows.itertuples(index=False), start=1):
        row = pd.Series(source._asdict())
        offset = _offset_minutes(row.get("local_utc_offset_minutes", np.nan))
        sleep_start = _coerce_utc(row["sleep_start_utc"])
        sleep_end = _coerce_utc(row["sleep_end_utc"])
        wake_start = sleep_end
        accepted_next = _coerce_utc(row.get("next_sleep_start_utc"))
        observed_next = _coerce_utc(row.get("next_observed_sleep_start_utc"))
        status = str(row.get("next_sleep_status", ""))
        original_date = pd.Timestamp(row["calendarDate"]).normalize()

        is_observed = status == NEXT_SLEEP_OBSERVED_WITHIN_CUTOFF or (
            pd.notna(accepted_next) and status not in {NEXT_SLEEP_MISSING_AFTER_CUTOFF, NEXT_SLEEP_NO_FOLLOWING_OBSERVED}
        )
        if is_observed and pd.notna(accepted_next) and accepted_next > wake_start:
            rows.append(
                _analysis_row(
                    idx=idx,
                    segment="observed",
                    calendar_date=original_date,
                    source_row=row,
                    sleep_start_utc=sleep_start,
                    sleep_end_utc=sleep_end,
                    wake_start_utc=wake_start,
                    wake_end_utc=accepted_next,
                    next_observed_sleep_start_utc=observed_next,
                    next_sleep_start_utc=accepted_next,
                    sleep_start_known=True,
                    sleep_end_known=True,
                    wake_start_known=True,
                    wake_end_known=True,
                    next_sleep_start_known=True,
                    boundary_confidence="observed",
                    wake_end_source="observed_next_sleep",
                )
            )
            continue

        if pd.isna(observed_next) or status == NEXT_SLEEP_NO_FOLLOWING_OBSERVED:
            rows.append(
                _analysis_row(
                    idx=idx,
                    segment="missing_next",
                    calendar_date=original_date,
                    source_row=row,
                    sleep_start_utc=sleep_start,
                    sleep_end_utc=sleep_end,
                    wake_start_utc=wake_start,
                    wake_end_utc=pd.NaT,
                    next_observed_sleep_start_utc=observed_next,
                    next_sleep_start_utc=pd.NaT,
                    sleep_start_known=True,
                    sleep_end_known=True,
                    wake_start_known=True,
                    wake_end_known=False,
                    next_sleep_start_known=False,
                    boundary_confidence="missing_next_sleep",
                    wake_end_source="no_following_observed_sleep",
                )
            )
            continue

        gap_hours = row.get("observed_wake_duration_hours", np.nan)
        if pd.isna(gap_hours):
            gap_hours = _duration_hours(wake_start, observed_next)

        if pd.notna(gap_hours) and 0 < gap_hours <= config.wake_max_hours:
            rows.append(
                _analysis_row(
                    idx=idx,
                    segment="late_observed",
                    calendar_date=original_date,
                    source_row=row,
                    sleep_start_utc=sleep_start,
                    sleep_end_utc=sleep_end,
                    wake_start_utc=wake_start,
                    wake_end_utc=observed_next,
                    next_observed_sleep_start_utc=observed_next,
                    next_sleep_start_utc=observed_next,
                    sleep_start_known=True,
                    sleep_end_known=True,
                    wake_start_known=True,
                    wake_end_known=True,
                    next_sleep_start_known=True,
                    boundary_confidence="observed_late_within_duration",
                    wake_end_source="observed_next_sleep_after_cutoff_within_duration",
                )
            )
            continue

        split_utc = wake_start + (observed_next - wake_start) / 2 if pd.notna(observed_next) else pd.NaT
        split_local = _utc_to_local(split_utc, offset)
        split_calendar = _calendar_date_for(split_local, split_utc) if pd.notna(split_utc) else pd.NaT
        split_calendar_collides = (
            pd.notna(split_calendar)
            and split_calendar in source_calendar_dates
            and split_calendar != original_date
        )
        can_split = (
            pd.notna(gap_hours)
            and gap_hours > config.wake_max_hours
            and gap_hours <= config.max_synthetic_split_gap_hours
            and not split_calendar_collides
            and _has_monitoring_rows(heart_rate, stress, wake_start, observed_next)
        )
        if can_split:
            rows.append(
                _analysis_row(
                    idx=idx,
                    segment="split_a",
                    calendar_date=original_date,
                    source_row=row,
                    sleep_start_utc=sleep_start,
                    sleep_end_utc=sleep_end,
                    wake_start_utc=wake_start,
                    wake_end_utc=split_utc,
                    next_observed_sleep_start_utc=observed_next,
                    next_sleep_start_utc=pd.NaT,
                    sleep_start_known=True,
                    sleep_end_known=True,
                    wake_start_known=True,
                    wake_end_known=False,
                    next_sleep_start_known=False,
                    boundary_confidence="synthetic_split",
                    wake_end_source="synthetic_midpoint_split",
                    synthetic_wake_split_utc=split_utc,
                )
            )
            rows.append(
                _analysis_row(
                    idx=idx,
                    segment="split_b",
                    calendar_date=_calendar_date_for(split_local, split_utc),
                    source_row=row,
                    sleep_start_utc=pd.NaT,
                    sleep_end_utc=pd.NaT,
                    wake_start_utc=split_utc,
                    wake_end_utc=observed_next,
                    next_observed_sleep_start_utc=observed_next,
                    next_sleep_start_utc=observed_next,
                    sleep_start_known=False,
                    sleep_end_known=False,
                    wake_start_known=False,
                    wake_end_known=True,
                    next_sleep_start_known=True,
                    boundary_confidence="synthetic_split",
                    wake_end_source="observed_next_sleep_after_split",
                    synthetic_wake_split_utc=split_utc,
                )
            )
            continue

        unsupported = bool(pd.notna(gap_hours) and gap_hours > config.max_synthetic_split_gap_hours)
        if split_calendar_collides:
            wake_end_source = "split_collision_existing_calendarDate"
            boundary_confidence = "missing_next_sleep"
        else:
            wake_end_source = "unsupported_multi_day_gap" if unsupported else "missing_after_cutoff_no_split"
            boundary_confidence = "unsupported_multi_day_gap" if unsupported else "missing_next_sleep"
        rows.append(
            _analysis_row(
                idx=idx,
                segment="unsupported_gap" if unsupported else "missing_after_cutoff",
                calendar_date=original_date,
                source_row=row,
                sleep_start_utc=sleep_start,
                sleep_end_utc=sleep_end,
                wake_start_utc=wake_start,
                wake_end_utc=pd.NaT,
                next_observed_sleep_start_utc=observed_next,
                next_sleep_start_utc=pd.NaT,
                sleep_start_known=True,
                sleep_end_known=True,
                wake_start_known=True,
                wake_end_known=False,
                next_sleep_start_known=False,
                boundary_confidence=boundary_confidence,
                wake_end_source=wake_end_source,
                unsupported_multi_day_gap=unsupported,
            )
        )

    out = pd.DataFrame.from_records(rows)
    for column in ANALYSIS_WINDOW_COLUMNS:
        if column not in out.columns:
            out[column] = np.nan
    out = out.reindex(columns=ANALYSIS_WINDOW_COLUMNS).reset_index(drop=True)
    _assert_unique_calendar_dates(out, label="monitoring analysis windows")
    return out


def _numeric(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().astype(float)


def _sort_by_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "timestamp_utc" not in df.columns:
        return df.reset_index(drop=True).copy()
    out = df.reset_index(drop=True).copy()
    out["timestamp_utc"] = pd.to_datetime(out["timestamp_utc"], errors="coerce", utc=True)
    return out.dropna(subset=["timestamp_utc"]).sort_values("timestamp_utc").reset_index(drop=True)


def _valid_signal_subset(subset: pd.DataFrame, signal: str) -> pd.DataFrame:
    if signal == "hr":
        return subset.loc[subset["heart_rate_status"] == "valid"].copy()
    return subset.loc[subset["stress_status"] == "valid"].copy()


def _valid_hr_timestamps(heart_rate_subset: pd.DataFrame) -> set[pd.Timestamp]:
    if heart_rate_subset.empty or "timestamp_utc" not in heart_rate_subset.columns:
        return set()
    valid = heart_rate_subset.loc[heart_rate_subset["heart_rate_status"] == "valid"]
    return set(pd.to_datetime(valid["timestamp_utc"], errors="coerce", utc=True).dropna())


def _stress_minus_2_with_valid_hr_mask(stress_subset: pd.DataFrame, heart_rate_subset: pd.DataFrame) -> pd.Series:
    if stress_subset.empty:
        return pd.Series(dtype=bool, index=stress_subset.index)
    raw = pd.to_numeric(
        stress_subset["stress_level_raw"] if "stress_level_raw" in stress_subset else pd.Series(dtype=float),
        errors="coerce",
    )
    stress_timestamps = pd.to_datetime(
        stress_subset["timestamp_utc"] if "timestamp_utc" in stress_subset else pd.Series(dtype="datetime64[ns, UTC]"),
        errors="coerce",
        utc=True,
    )
    valid_hr = _valid_hr_timestamps(heart_rate_subset)
    return (raw == -2) & stress_timestamps.isin(valid_hr)


def _semantic_stress_observed_subset(stress_subset: pd.DataFrame, heart_rate_subset: pd.DataFrame) -> pd.DataFrame:
    if stress_subset.empty:
        return stress_subset.copy()
    raw = pd.to_numeric(
        stress_subset["stress_level_raw"] if "stress_level_raw" in stress_subset else pd.Series(dtype=float),
        errors="coerce",
    )
    active_mask = _stress_minus_2_with_valid_hr_mask(stress_subset, heart_rate_subset)
    observed_mask = ((raw >= 0) & (raw <= 100)) | active_mask
    return stress_subset.loc[observed_mask].copy()


def _observed_timestamp_count(subset: pd.DataFrame) -> int:
    if subset.empty or "timestamp_utc" not in subset.columns:
        return 0
    timestamps = pd.to_datetime(subset["timestamp_utc"], errors="coerce", utc=True).dropna().drop_duplicates()
    return int(len(timestamps))


def _signal_value_col(signal: str) -> str:
    return "heart_rate" if signal == "hr" else "stress_level"


def _max_gap_minutes(valid_timestamps: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> float:
    expected = _duration_minutes(start, end)
    if pd.isna(expected):
        return np.nan
    timestamps = (
        pd.to_datetime(valid_timestamps, errors="coerce", utc=True)
        .dropna()
        .drop_duplicates()
        .sort_values()
    )
    if timestamps.empty:
        return float(expected)
    gaps = [
        max(_duration_minutes(start, timestamps.iloc[0]), 0.0),
        max(_duration_minutes(timestamps.iloc[-1], end) - 1.0, 0.0),
    ]
    for previous, current in zip(timestamps.iloc[:-1], timestamps.iloc[1:], strict=False):
        gaps.append(max(_duration_minutes(previous, current) - 1.0, 0.0))
    return float(max(gaps))


def _quality_label(coverage: float, max_gap: float, usable: bool, signal: str, active_proxy_fraction: float) -> str:
    if usable:
        return "usable"
    if signal == "stress" and pd.notna(active_proxy_fraction) and active_proxy_fraction >= 0.50:
        return "active_proxy_dominant"
    if pd.isna(coverage) or coverage == 0:
        return "empty"
    if coverage >= 0.25:
        return "partial"
    if pd.notna(max_gap) and max_gap > 0:
        return "gappy"
    return "sparse"


def _quality_window_record(
    *,
    analysis_window_id: str,
    calendar_date: pd.Timestamp,
    window_name: str,
    phase: str,
    signal: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    heart_rate: pd.DataFrame,
    stress: pd.DataFrame,
    config: MonitoringCoreConfig,
) -> dict[str, Any]:
    source = heart_rate if signal == "hr" else stress
    subset = _time_slice(source, start, end)
    valid = _valid_signal_subset(subset, signal)
    value_col = _signal_value_col(signal)
    expected = _duration_minutes(start, end)
    values = _numeric(valid[value_col] if value_col in valid else pd.Series(dtype=float))
    valid_numeric_minutes = int(values.count())

    raw_minus_1_fraction = np.nan
    raw_minus_2_fraction = np.nan
    raw_minus_2_with_hr_fraction = np.nan
    raw_minus_2_without_hr_fraction = np.nan
    raw_valid_fraction = np.nan
    active_proxy_fraction = np.nan
    observed = valid
    if signal == "stress":
        hr_subset = _time_slice(heart_rate, start, end)
        observed = _semantic_stress_observed_subset(subset, hr_subset)
        raw = pd.to_numeric(
            subset["stress_level_raw"] if "stress_level_raw" in subset else pd.Series(dtype=float),
            errors="coerce",
        )
        raw_denominator = int(raw.notna().sum())
        if raw_denominator > 0:
            raw_minus_2_with_hr = _stress_minus_2_with_valid_hr_mask(subset, hr_subset)
            raw_minus_2 = raw == -2
            raw_minus_1_fraction = float((raw == -1).sum() / raw_denominator)
            raw_minus_2_fraction = float(raw_minus_2.sum() / raw_denominator)
            raw_minus_2_with_hr_fraction = float(raw_minus_2_with_hr.sum() / raw_denominator)
            raw_minus_2_without_hr_fraction = float((raw_minus_2 & ~raw_minus_2_with_hr).sum() / raw_denominator)
            raw_valid_fraction = float(((raw >= 0) & (raw <= 100)).sum() / raw_denominator)
            active_proxy_fraction = raw_minus_2_with_hr_fraction

    observed_minutes = _observed_timestamp_count(observed)
    coverage = min(observed_minutes / expected, 1.0) if pd.notna(expected) and expected > 0 else np.nan
    observed_timestamps = (
        observed["timestamp_utc"] if "timestamp_utc" in observed else pd.Series(dtype="datetime64[ns, UTC]")
    )
    max_gap = _max_gap_minutes(observed_timestamps, start, end)
    if observed.empty:
        minutes_to_first = np.nan
        minutes_from_last = np.nan
    else:
        ordered = _sort_by_timestamp(observed)
        minutes_to_first = _duration_minutes(start, pd.Timestamp(ordered.iloc[0]["timestamp_utc"]))
        minutes_from_last = _duration_minutes(pd.Timestamp(ordered.iloc[-1]["timestamp_utc"]), end)

    start_covered = pd.notna(minutes_to_first) and minutes_to_first <= config.boundary_gap_tolerance_minutes
    end_covered = pd.notna(minutes_from_last) and minutes_from_last <= config.boundary_gap_tolerance_minutes
    usable = bool(
        pd.notna(coverage)
        and coverage >= config.usable_coverage_fraction
        and pd.notna(max_gap)
        and max_gap <= config.usable_max_gap_minutes
        and start_covered
        and end_covered
    )
    return {
        "analysis_window_id": analysis_window_id,
        "calendarDate": calendar_date,
        "window_name": window_name,
        "phase": phase,
        "signal": signal,
        "window_start_utc": start,
        "window_end_utc": end,
        "expected_minutes": expected,
        "observed_raw_minutes": int(len(subset)),
        "valid_numeric_minutes": valid_numeric_minutes,
        "observed_semantic_minutes": observed_minutes,
        "coverage_fraction": coverage,
        "max_gap_minutes": max_gap,
        "minutes_to_first_valid": minutes_to_first,
        "minutes_from_last_valid_to_end": minutes_from_last,
        "start_boundary_covered": _flag(start_covered),
        "end_boundary_covered": _flag(end_covered),
        "raw_minus_1_fraction": raw_minus_1_fraction,
        "raw_minus_2_fraction": raw_minus_2_fraction,
        "raw_minus_2_with_hr_fraction": raw_minus_2_with_hr_fraction,
        "raw_minus_2_without_hr_fraction": raw_minus_2_without_hr_fraction,
        "raw_valid_fraction": raw_valid_fraction,
        "active_proxy_fraction": active_proxy_fraction,
        "usable_basic": _flag(usable),
        "quality_label": _quality_label(coverage, max_gap, usable, signal, active_proxy_fraction),
    }


def _window_specs(row: pd.Series, config: MonitoringCoreConfig) -> list[tuple[str, str, pd.Timestamp, pd.Timestamp]]:
    specs: list[tuple[str, str, pd.Timestamp, pd.Timestamp]] = []
    if pd.notna(row.get("sleep_start_utc")) and pd.notna(row.get("sleep_end_utc")):
        specs.append(("sleep", "sleep", row["sleep_start_utc"], row["sleep_end_utc"]))

    wake_start = row.get("wake_start_utc")
    wake_end = row.get("wake_end_utc")
    wake_available = (
        pd.notna(wake_start)
        and pd.notna(wake_end)
        and wake_start < wake_end
        and row.get("unsupported_multi_day_gap", 0) == 0
    )
    if wake_available:
        specs.append(("wake", "wake", wake_start, wake_end))

    if row.get("next_sleep_start_known", 0) == 1 and wake_available:
        start = max(wake_start, wake_end - pd.Timedelta(hours=4))
        specs.append(("pre_sleep_4h", "wake/pre-sleep", start, wake_end))

    if wake_available and pd.notna(row.get("wake_duration_hours")) and row.get("wake_duration_hours") <= config.wake_max_hours:
        step = (wake_end - wake_start) / 4
        for idx in range(4):
            specs.append((f"wake_q{idx + 1}", "wake", wake_start + idx * step, wake_start + (idx + 1) * step))
    return specs


def build_monitoring_quality_windows(
    heart_rate_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    analysis_windows_df: pd.DataFrame,
    *,
    config: MonitoringCoreConfig | None = None,
) -> pd.DataFrame:
    """Build long-format window quality diagnostics used internally by reports."""
    config = config or MonitoringCoreConfig()
    heart_rate = _indexed_by_timestamp(_normalize_hr(heart_rate_df))
    stress = _indexed_by_timestamp(_normalize_stress(stress_df))
    rows: list[dict[str, Any]] = []
    for _, analysis_row in analysis_windows_df.iterrows():
        for window_name, phase, start, end in _window_specs(analysis_row, config):
            for signal in ["hr", "stress"]:
                rows.append(
                    _quality_window_record(
                        analysis_window_id=str(analysis_row["analysis_window_id"]),
                        calendar_date=pd.Timestamp(analysis_row["calendarDate"]).normalize(),
                        window_name=window_name,
                        phase=phase,
                        signal=signal,
                        start=pd.Timestamp(start),
                        end=pd.Timestamp(end),
                        heart_rate=heart_rate,
                        stress=stress,
                        config=config,
                    )
                )
    return pd.DataFrame.from_records(rows)


def _quality_lookup(quality_windows_df: pd.DataFrame) -> dict[tuple[str, str, str], pd.Series]:
    if quality_windows_df.empty:
        return {}
    return {
        (str(row.analysis_window_id), str(row.window_name), str(row.signal)): pd.Series(row._asdict())
        for row in quality_windows_df.itertuples(index=False)
    }


def _quality_value(
    lookup: dict[tuple[str, str, str], pd.Series],
    analysis_window_id: str,
    window_name: str,
    signal: str,
    metric: str,
) -> Any:
    quality = lookup.get((analysis_window_id, window_name, signal))
    return quality.get(metric, np.nan) if quality is not None else np.nan


def build_monitoring_quality_index(
    analysis_windows_df: pd.DataFrame,
    quality_windows_df: pd.DataFrame,
    *,
    config: MonitoringCoreConfig | None = None,
) -> pd.DataFrame:
    """Build one human-facing quality row per analysis window."""
    config = config or MonitoringCoreConfig()
    lookup = _quality_lookup(quality_windows_df)
    rows: list[dict[str, Any]] = []
    for _, source in analysis_windows_df.iterrows():
        row = source.to_dict()
        analysis_id = str(row["analysis_window_id"])
        sleep_duration = pd.to_numeric(pd.Series([row.get("sleep_duration_hours")]), errors="coerce").iloc[0]
        wake_duration = pd.to_numeric(pd.Series([row.get("wake_duration_hours")]), errors="coerce").iloc[0]
        observed_wake_duration = pd.to_numeric(
            pd.Series([row.get("observed_wake_duration_hours")]), errors="coerce"
        ).iloc[0]
        duration_for_long_flags = observed_wake_duration if pd.notna(observed_wake_duration) else wake_duration
        sleep_plausible = pd.notna(sleep_duration) and config.sleep_min_hours <= sleep_duration <= config.sleep_max_hours
        wake_plausible = pd.notna(wake_duration) and config.wake_min_hours <= wake_duration <= config.wake_max_hours
        row.update(
            {
                "sleep_duration_plausible": _flag(sleep_plausible),
                "wake_duration_plausible": _flag(wake_plausible),
                "semantic_window_plausible": _flag(sleep_plausible and wake_plausible),
                "wake_duration_gt_24h": _flag(pd.notna(duration_for_long_flags) and duration_for_long_flags > 24),
                "wake_duration_gt_30h": _flag(pd.notna(duration_for_long_flags) and duration_for_long_flags > 30),
                "wake_duration_gt_48h": _flag(pd.notna(duration_for_long_flags) and duration_for_long_flags > 48),
            }
        )

        for window_name in ["sleep", "wake", "pre_sleep_4h"]:
            for signal in ["hr", "stress"]:
                prefix = f"{window_name}_{signal}"
                row[f"{prefix}_coverage_fraction"] = _quality_value(
                    lookup, analysis_id, window_name, signal, "coverage_fraction"
                )
                row[f"{prefix}_max_gap_minutes"] = _quality_value(
                    lookup, analysis_id, window_name, signal, "max_gap_minutes"
                )
                row[f"{prefix}_start_boundary_covered"] = _quality_value(
                    lookup, analysis_id, window_name, signal, "start_boundary_covered"
                )
                row[f"{prefix}_end_boundary_covered"] = _quality_value(
                    lookup, analysis_id, window_name, signal, "end_boundary_covered"
                )
                if signal == "stress":
                    row[f"{prefix}_raw_minus_1_fraction"] = _quality_value(
                        lookup, analysis_id, window_name, signal, "raw_minus_1_fraction"
                    )
                    row[f"{prefix}_raw_minus_2_fraction"] = _quality_value(
                        lookup, analysis_id, window_name, signal, "raw_minus_2_fraction"
                    )
                    row[f"{prefix}_raw_minus_2_with_hr_fraction"] = _quality_value(
                        lookup, analysis_id, window_name, signal, "raw_minus_2_with_hr_fraction"
                    )
                    row[f"{prefix}_raw_minus_2_without_hr_fraction"] = _quality_value(
                        lookup, analysis_id, window_name, signal, "raw_minus_2_without_hr_fraction"
                    )
                    row[f"{prefix}_raw_valid_fraction"] = _quality_value(
                        lookup, analysis_id, window_name, signal, "raw_valid_fraction"
                    )
                    row[f"{prefix}_active_proxy_fraction"] = _quality_value(
                        lookup, analysis_id, window_name, signal, "active_proxy_fraction"
                    )

        def usable(window_name: str, signal: str) -> bool:
            return _quality_value(lookup, analysis_id, window_name, signal, "usable_basic") == 1

        row["sleep_hr_usable"] = _flag(usable("sleep", "hr"))
        row["sleep_stress_usable"] = _flag(usable("sleep", "stress"))
        row["wake_hr_usable"] = _flag(usable("wake", "hr"))
        row["wake_stress_usable"] = _flag(usable("wake", "stress"))
        row["pre_sleep_4h_usable"] = _flag(usable("pre_sleep_4h", "hr") and usable("pre_sleep_4h", "stress"))

        quarter_hr = [
            _quality_value(lookup, analysis_id, f"wake_q{idx}", "hr", "coverage_fraction")
            for idx in range(1, 5)
        ]
        quarter_stress = [
            _quality_value(lookup, analysis_id, f"wake_q{idx}", "stress", "coverage_fraction")
            for idx in range(1, 5)
        ]
        row["wake_quarters_hr_min_coverage_fraction"] = (
            float(np.nanmin(quarter_hr)) if any(pd.notna(value) for value in quarter_hr) else np.nan
        )
        row["wake_quarters_stress_min_coverage_fraction"] = (
            float(np.nanmin(quarter_stress)) if any(pd.notna(value) for value in quarter_stress) else np.nan
        )
        row["wake_quarters_usable"] = _flag(
            all(
                _quality_value(lookup, analysis_id, f"wake_q{idx}", signal, "usable_basic") == 1
                for idx in range(1, 5)
                for signal in ["hr", "stress"]
            )
        )
        row["modeling_recovery_v0_eligible"] = _flag(
            bool(row["semantic_window_plausible"])
            and row.get("unsupported_multi_day_gap", 0) == 0
            and row.get("next_sleep_start_known", 0) == 1
            and row["sleep_hr_usable"] == 1
            and row["sleep_stress_usable"] == 1
            and row["wake_hr_usable"] == 1
            and row["wake_stress_usable"] == 1
        )
        rows.append(row)

    out = pd.DataFrame.from_records(rows)
    for column in QUALITY_INDEX_COLUMNS:
        if column not in out.columns:
            out[column] = np.nan
    return out.reindex(columns=QUALITY_INDEX_COLUMNS).reset_index(drop=True)


def _entropy_from_counts(counts: list[int]) -> float:
    total = int(sum(counts))
    if total <= 0:
        return np.nan
    probabilities = np.asarray([count / total for count in counts if count > 0], dtype=float)
    return float(-(probabilities * np.log2(probabilities)).sum())


def _hr_zone(value: float, max_hr_bpm: float) -> str | None:
    if pd.isna(value) or max_hr_bpm <= 0:
        return None
    ratio = float(value) / float(max_hr_bpm)
    if ratio < 0.50:
        return "below_zone1"
    if ratio < 0.60:
        return "zone1"
    if ratio < 0.70:
        return "zone2"
    if ratio < 0.80:
        return "zone3"
    if ratio < 0.90:
        return "zone4"
    if ratio <= 1.0:
        return "zone5"
    return "above_mhr"


def _hr_entropy(values: pd.Series, max_hr_bpm: float) -> float:
    numeric = _numeric(values)
    if numeric.empty:
        return np.nan
    zones = ["below_zone1", "zone1", "zone2", "zone3", "zone4", "zone5", "above_mhr"]
    labels = numeric.map(lambda value: _hr_zone(value, max_hr_bpm))
    return _entropy_from_counts([int((labels == zone).sum()) for zone in zones])


def _stress_entropy(values: pd.Series) -> float:
    numeric = _numeric(values)
    valid = numeric.loc[(numeric >= 0) & (numeric <= 100)]
    if valid.empty:
        return np.nan
    counts = [
        int(((valid >= 0) & (valid <= 25)).sum()),
        int(((valid >= 26) & (valid <= 50)).sum()),
        int(((valid >= 51) & (valid <= 75)).sum()),
        int(((valid >= 76) & (valid <= 100)).sum()),
    ]
    return _entropy_from_counts(counts)


def _shape_stats(values: pd.Series, prefix: str, signal: str, config: MonitoringCoreConfig) -> dict[str, float]:
    metrics = [
        "mean",
        "median",
        "std",
        "min",
        "max",
        "p10",
        "p25",
        "p75",
        "p90",
        "iqr",
        "range",
        "mad",
        "skewness",
        "kurtosis",
        "histogram_entropy",
    ]
    record = {f"{prefix}_{metric}": np.nan for metric in metrics}
    numeric = _numeric(values)
    if len(numeric) < config.min_valid_minutes:
        return record
    p25 = float(numeric.quantile(0.25))
    p75 = float(numeric.quantile(0.75))
    median = float(numeric.median())
    record.update(
        {
            f"{prefix}_mean": float(numeric.mean()),
            f"{prefix}_median": median,
            f"{prefix}_std": float(numeric.std(ddof=0)),
            f"{prefix}_min": float(numeric.min()),
            f"{prefix}_max": float(numeric.max()),
            f"{prefix}_p10": float(numeric.quantile(0.10)),
            f"{prefix}_p25": p25,
            f"{prefix}_p75": p75,
            f"{prefix}_p90": float(numeric.quantile(0.90)),
            f"{prefix}_iqr": p75 - p25,
            f"{prefix}_range": float(numeric.max() - numeric.min()),
            f"{prefix}_mad": float((numeric - median).abs().median()),
            f"{prefix}_skewness": float(numeric.skew()) if len(numeric) >= 3 else np.nan,
            f"{prefix}_kurtosis": float(numeric.kurt()) if len(numeric) >= 4 else np.nan,
            f"{prefix}_histogram_entropy": _hr_entropy(numeric, config.max_hr_bpm)
            if signal == "hr"
            else _stress_entropy(numeric),
        }
    )
    return record


def _stress_state_fractions(stress_subset: pd.DataFrame, heart_rate_subset: pd.DataFrame, prefix: str) -> dict[str, float]:
    raw = pd.to_numeric(
        stress_subset["stress_level_raw"] if "stress_level_raw" in stress_subset else pd.Series(dtype=float),
        errors="coerce",
    )
    active_mask = _stress_minus_2_with_valid_hr_mask(stress_subset, heart_rate_subset)
    denominator_mask = ((raw >= 0) & (raw <= 100)) | active_mask
    denominator = int(denominator_mask.sum())
    record = {
        f"{prefix}_stress_frac_resting": np.nan,
        f"{prefix}_stress_frac_low": np.nan,
        f"{prefix}_stress_frac_medium": np.nan,
        f"{prefix}_stress_frac_high": np.nan,
        f"{prefix}_stress_frac_active": np.nan,
    }
    if denominator == 0:
        return record
    eligible = raw.loc[denominator_mask]
    eligible_active = active_mask.loc[denominator_mask]
    record.update(
        {
            f"{prefix}_stress_frac_resting": float(((eligible >= 0) & (eligible <= 25)).sum() / denominator),
            f"{prefix}_stress_frac_low": float(((eligible >= 26) & (eligible <= 50)).sum() / denominator),
            f"{prefix}_stress_frac_medium": float(((eligible >= 51) & (eligible <= 75)).sum() / denominator),
            f"{prefix}_stress_frac_high": float(((eligible >= 76) & (eligible <= 100)).sum() / denominator),
            f"{prefix}_stress_frac_active": float(eligible_active.sum() / denominator),
        }
    )
    return record


def _hr_zone_fractions(hr_values: pd.Series, prefix: str, max_hr_bpm: float) -> dict[str, float]:
    zones = ["below_zone1", "zone1", "zone2", "zone3", "zone4", "zone5", "above_mhr"]
    numeric = _numeric(hr_values)
    record = {f"{prefix}_hr_frac_{zone}": np.nan for zone in zones}
    if numeric.empty:
        return record
    labels = numeric.map(lambda value: _hr_zone(value, max_hr_bpm))
    denominator = len(labels)
    for zone in zones:
        record[f"{prefix}_hr_frac_{zone}"] = float((labels == zone).sum() / denominator)
    return record


def _variability(values_df: pd.DataFrame, value_col: str, prefix: str, config: MonitoringCoreConfig) -> dict[str, float]:
    record = {
        f"{prefix}_mean_abs_diff": np.nan,
        f"{prefix}_median_abs_diff": np.nan,
        f"{prefix}_std_diff": np.nan,
        f"{prefix}_roughness": np.nan,
        f"{prefix}_max_abs_jump": np.nan,
    }
    if values_df.empty:
        return record
    ordered = _sort_by_timestamp(values_df.dropna(subset=[value_col]))
    if len(ordered) < 2:
        return record
    timestamps = pd.to_datetime(ordered["timestamp_utc"], errors="coerce", utc=True)
    values = pd.to_numeric(ordered[value_col], errors="coerce")
    gaps = timestamps.diff().dt.total_seconds() / 60.0
    diffs = values.diff()
    eligible = gaps <= config.gap_break_minutes
    eligible.iloc[0] = False
    valid_diffs = diffs.loc[eligible].dropna().astype(float)
    if valid_diffs.empty:
        return record
    record.update(
        {
            f"{prefix}_mean_abs_diff": float(valid_diffs.abs().mean()),
            f"{prefix}_median_abs_diff": float(valid_diffs.abs().median()),
            f"{prefix}_std_diff": float(valid_diffs.std(ddof=0)),
            f"{prefix}_roughness": float((valid_diffs**2).mean()),
            f"{prefix}_max_abs_jump": float(valid_diffs.abs().max()),
        }
    )
    return record


def _trend(
    values_df: pd.DataFrame,
    value_col: str,
    start: pd.Timestamp,
    prefix: str,
    config: MonitoringCoreConfig,
) -> dict[str, float]:
    record = {f"{prefix}_slope_per_hour": np.nan, f"{prefix}_trend_r2": np.nan}
    ordered = _sort_by_timestamp(values_df.dropna(subset=[value_col]))
    if len(ordered) < config.min_valid_minutes:
        return record
    x = (pd.to_datetime(ordered["timestamp_utc"], errors="coerce", utc=True) - start).dt.total_seconds() / 60.0
    y = pd.to_numeric(ordered[value_col], errors="coerce")
    valid = x.notna() & y.notna()
    x_values = x.loc[valid].to_numpy(dtype=float)
    y_values = y.loc[valid].to_numpy(dtype=float)
    if len(x_values) < config.min_valid_minutes or len(np.unique(x_values)) < 2:
        return record
    slope_per_minute, intercept = np.polyfit(x_values, y_values, 1)
    predicted = slope_per_minute * x_values + intercept
    total_ss = float(((y_values - y_values.mean()) ** 2).sum())
    residual_ss = float(((y_values - predicted) ** 2).sum())
    record[f"{prefix}_slope_per_hour"] = float(slope_per_minute * 60.0)
    record[f"{prefix}_trend_r2"] = float(1.0 - residual_ss / total_ss) if total_ss > 0 else np.nan
    return record


def _mean_in_window(indexed: pd.DataFrame, value_col: str, start: pd.Timestamp, end: pd.Timestamp, min_valid: int) -> float:
    values = _numeric(_time_slice(indexed, start, end)[value_col] if value_col in indexed.columns else pd.Series(dtype=float))
    if len(values) < min_valid:
        return np.nan
    return float(values.mean())


def _summary_in_window(
    indexed: pd.DataFrame,
    value_col: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    min_valid: int,
) -> dict[str, float]:
    values = _numeric(_time_slice(indexed, start, end)[value_col] if value_col in indexed.columns else pd.Series(dtype=float))
    if len(values) < min_valid:
        return {"mean": np.nan, "std": np.nan, "p90": np.nan}
    return {
        "mean": float(values.mean()),
        "std": float(values.std(ddof=0)),
        "p90": float(values.quantile(0.90)),
    }


def _event_episode_features(
    event_timestamps: pd.Series,
    start: pd.Timestamp,
    prefix: str,
    config: MonitoringCoreConfig,
) -> dict[str, float | int]:
    record: dict[str, float | int] = {
        f"{prefix}_has_event": 0,
        f"{prefix}_episode_count": 0,
        f"{prefix}_total_minutes": 0,
        f"{prefix}_mean_duration_minutes": 0.0,
        f"{prefix}_max_duration_minutes": 0.0,
        f"{prefix}_fragmentation_index": 0.0,
        f"{prefix}_time_to_first_minutes": np.nan,
    }
    timestamps = pd.to_datetime(event_timestamps, errors="coerce", utc=True).dropna().drop_duplicates().sort_values()
    if timestamps.empty:
        return record

    durations: list[int] = []
    current_count = 1
    previous = timestamps.iloc[0]
    for current in timestamps.iloc[1:]:
        gap_minutes = (current - previous).total_seconds() / 60.0
        if gap_minutes <= config.gap_break_minutes:
            current_count += 1
        else:
            durations.append(current_count)
            current_count = 1
        previous = current
    durations.append(current_count)

    total_minutes = int(sum(durations))
    episode_count = int(len(durations))
    record.update(
        {
            f"{prefix}_has_event": 1,
            f"{prefix}_episode_count": episode_count,
            f"{prefix}_total_minutes": total_minutes,
            f"{prefix}_mean_duration_minutes": float(np.mean(durations)),
            f"{prefix}_max_duration_minutes": float(np.max(durations)),
            f"{prefix}_fragmentation_index": float(episode_count / total_minutes) if total_minutes > 0 else 0.0,
            f"{prefix}_time_to_first_minutes": _duration_minutes(start, timestamps.iloc[0]),
        }
    )
    return record


def _phase_relative_windows(
    phase: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    heart_rate: pd.DataFrame,
    stress: pd.DataFrame,
    config: MonitoringCoreConfig,
) -> dict[str, float]:
    record: dict[str, float] = {}
    if pd.isna(start) or pd.isna(end) or start >= end:
        return record
    step = (end - start) / 4
    for idx in range(4):
        q_start = start + idx * step
        q_end = start + (idx + 1) * step
        prefix = f"{phase}_q{idx + 1}"
        hr_valid = _time_slice(heart_rate, q_start, q_end).loc[lambda df: df["heart_rate_status"] == "valid"]
        stress_valid = _time_slice(stress, q_start, q_end).loc[lambda df: df["stress_status"] == "valid"]
        hr_values = _numeric(hr_valid["heart_rate"] if "heart_rate" in hr_valid else pd.Series(dtype=float))
        stress_values = _numeric(stress_valid["stress_level"] if "stress_level" in stress_valid else pd.Series(dtype=float))
        record[f"{prefix}_hr_mean"] = float(hr_values.mean()) if len(hr_values) >= config.min_valid_minutes else np.nan
        record[f"{prefix}_hr_std"] = float(hr_values.std(ddof=0)) if len(hr_values) >= config.min_valid_minutes else np.nan
        record[f"{prefix}_hr_p90"] = float(hr_values.quantile(0.90)) if len(hr_values) >= config.min_valid_minutes else np.nan
        record[f"{prefix}_stress_mean"] = (
            float(stress_values.mean()) if len(stress_values) >= config.min_valid_minutes else np.nan
        )
        record[f"{prefix}_stress_std"] = (
            float(stress_values.std(ddof=0)) if len(stress_values) >= config.min_valid_minutes else np.nan
        )
        record[f"{prefix}_stress_p90"] = (
            float(stress_values.quantile(0.90)) if len(stress_values) >= config.min_valid_minutes else np.nan
        )
        record[f"{prefix}_stress_high_fraction"] = (
            float((stress_values >= 76).sum() / len(stress_values))
            if len(stress_values) >= config.min_valid_minutes
            else np.nan
        )
    return record


def _phase_features(
    phase: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    heart_rate: pd.DataFrame,
    stress: pd.DataFrame,
    config: MonitoringCoreConfig,
) -> dict[str, float | int]:
    record: dict[str, float | int] = {}
    hr_subset = _time_slice(heart_rate, start, end)
    stress_subset = _time_slice(stress, start, end)
    hr_valid = hr_subset.loc[hr_subset["heart_rate_status"] == "valid"]
    stress_valid = stress_subset.loc[stress_subset["stress_status"] == "valid"]
    record.update(_shape_stats(hr_valid["heart_rate"], f"{phase}_hr", "hr", config))
    record.update(_shape_stats(stress_valid["stress_level"], f"{phase}_stress", "stress", config))
    record.update(_stress_state_fractions(stress_subset, hr_subset, phase))
    record.update(_hr_zone_fractions(hr_valid["heart_rate"], phase, config.max_hr_bpm))
    record.update(_variability(hr_valid, "heart_rate", f"{phase}_hr", config))
    record.update(_variability(stress_valid, "stress_level", f"{phase}_stress", config))
    record.update(_trend(hr_valid, "heart_rate", start, f"{phase}_hr", config))
    record.update(_trend(stress_valid, "stress_level", start, f"{phase}_stress", config))

    if phase == "wake":
        record.update(
            _event_episode_features(
                stress_valid.loc[pd.to_numeric(stress_valid["stress_level"], errors="coerce") >= 76, "timestamp_utc"],
                start,
                "wake_stress_high",
                config,
            )
        )
        active_mask = _stress_minus_2_with_valid_hr_mask(stress_subset, hr_subset)
        record.update(
            _event_episode_features(
                stress_subset.loc[active_mask, "timestamp_utc"],
                start,
                "wake_stress_active",
                config,
            )
        )
        record.update(
            _event_episode_features(
                hr_valid.loc[pd.to_numeric(hr_valid["heart_rate"], errors="coerce") >= 0.60 * config.max_hr_bpm, "timestamp_utc"],
                start,
                "wake_hr_zone2_plus",
                config,
            )
        )
    else:
        record.update(
            _event_episode_features(
                stress_valid.loc[pd.to_numeric(stress_valid["stress_level"], errors="coerce") >= 76, "timestamp_utc"],
                start,
                "sleep_stress_high",
                config,
            )
        )
        record.update(
            _event_episode_features(
                hr_valid.loc[pd.to_numeric(hr_valid["heart_rate"], errors="coerce") >= 0.50 * config.max_hr_bpm, "timestamp_utc"],
                start,
                "sleep_hr_zone1_plus",
                config,
            )
        )
    return record


def _sleep_recovery_features(
    sleep_start: pd.Timestamp,
    sleep_end: pd.Timestamp,
    heart_rate: pd.DataFrame,
    stress: pd.DataFrame,
    record: dict[str, Any],
    config: MonitoringCoreConfig,
) -> dict[str, float]:
    out: dict[str, float] = {
        "sleep_hr_q1_minus_q4": np.nan,
        "sleep_stress_q1_minus_q4": np.nan,
        "sleep_hr_time_to_min_minutes": np.nan,
        "sleep_stress_time_to_min_minutes": np.nan,
        "sleep_stress_time_to_low_stress_minutes": np.nan,
    }
    if "sleep_q1_hr_mean" in record and "sleep_q4_hr_mean" in record:
        out["sleep_hr_q1_minus_q4"] = (
            record["sleep_q1_hr_mean"] - record["sleep_q4_hr_mean"]
            if pd.notna(record["sleep_q1_hr_mean"]) and pd.notna(record["sleep_q4_hr_mean"])
            else np.nan
        )
    if "sleep_q1_stress_mean" in record and "sleep_q4_stress_mean" in record:
        out["sleep_stress_q1_minus_q4"] = (
            record["sleep_q1_stress_mean"] - record["sleep_q4_stress_mean"]
            if pd.notna(record["sleep_q1_stress_mean"]) and pd.notna(record["sleep_q4_stress_mean"])
            else np.nan
        )

    hr_valid = _time_slice(heart_rate, sleep_start, sleep_end).loc[lambda df: df["heart_rate_status"] == "valid"]
    if len(hr_valid) >= config.min_valid_minutes:
        ordered = _sort_by_timestamp(hr_valid)
        values = pd.to_numeric(ordered["heart_rate"], errors="coerce")
        if values.notna().any():
            min_idx = values.idxmin()
            out["sleep_hr_time_to_min_minutes"] = _duration_minutes(sleep_start, ordered.loc[min_idx, "timestamp_utc"])

    stress_valid = _time_slice(stress, sleep_start, sleep_end).loc[lambda df: df["stress_status"] == "valid"]
    if len(stress_valid) >= config.min_valid_minutes:
        ordered = _sort_by_timestamp(stress_valid)
        values = pd.to_numeric(ordered["stress_level"], errors="coerce")
        if values.notna().any():
            min_idx = values.idxmin()
            out["sleep_stress_time_to_min_minutes"] = _duration_minutes(sleep_start, ordered.loc[min_idx, "timestamp_utc"])
        low = ordered.loc[values <= 25]
        if not low.empty:
            out["sleep_stress_time_to_low_stress_minutes"] = _duration_minutes(sleep_start, low.iloc[0]["timestamp_utc"])
    return out


def _pre_sleep_features(
    wake_start: pd.Timestamp,
    wake_end: pd.Timestamp,
    heart_rate: pd.DataFrame,
    stress: pd.DataFrame,
    config: MonitoringCoreConfig,
) -> dict[str, float]:
    record: dict[str, float] = {}
    pre_start = max(wake_start, wake_end - pd.Timedelta(hours=4))
    hr_valid = heart_rate.loc[heart_rate["heart_rate_status"] == "valid"]
    stress_valid = stress.loc[stress["stress_status"] == "valid"]
    for signal, source, value_col in [
        ("hr", hr_valid, "heart_rate"),
        ("stress", stress_valid, "stress_level"),
    ]:
        summary = _summary_in_window(source, value_col, pre_start, wake_end, config.min_valid_minutes)
        for metric, value in summary.items():
            record[f"pre_sleep_4h_{signal}_{metric}"] = value
        record.update(_trend(_time_slice(source, pre_start, wake_end), value_col, pre_start, f"pre_sleep_4h_{signal}", config))
        early_end = min(pre_start + pd.Timedelta(hours=2), wake_end)
        late_start = max(pre_start, wake_end - pd.Timedelta(hours=1))
        early = _mean_in_window(source, value_col, pre_start, early_end, config.min_valid_minutes)
        late = _mean_in_window(source, value_col, late_start, wake_end, config.min_valid_minutes)
        record[f"pre_sleep_4h_{signal}_early_minus_late"] = (
            early - late if pd.notna(early) and pd.notna(late) else np.nan
        )
    stress_values = _numeric(_time_slice(stress_valid, pre_start, wake_end)["stress_level"])
    record["pre_sleep_4h_stress_high_fraction"] = (
        float((stress_values >= 76).sum() / len(stress_values)) if len(stress_values) >= config.min_valid_minutes else np.nan
    )
    return record


def _paired_hr_stress(
    phase: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    heart_rate: pd.DataFrame,
    stress: pd.DataFrame,
    config: MonitoringCoreConfig,
) -> dict[str, float]:
    record = {
        f"{phase}_hr_stress_corr": np.nan,
        f"{phase}_hr_diff_stress_diff_corr": np.nan,
        f"{phase}_stress_hr_slope": np.nan,
        f"{phase}_stress_hr_r2": np.nan,
        f"{phase}_frac_hr_zone2_plus_stress_high": np.nan,
        f"{phase}_frac_hr_below_zone1_stress_high": np.nan,
    }
    hr_valid = _time_slice(heart_rate, start, end).loc[lambda df: df["heart_rate_status"] == "valid"]
    stress_valid = _time_slice(stress, start, end).loc[lambda df: df["stress_status"] == "valid"]
    if hr_valid.empty or stress_valid.empty:
        return record
    paired = pd.merge(
        hr_valid.reset_index(drop=True)[["timestamp_utc", "heart_rate"]],
        stress_valid.reset_index(drop=True)[["timestamp_utc", "stress_level"]],
        on="timestamp_utc",
        how="inner",
    ).sort_values("timestamp_utc")
    if len(paired) < config.min_paired_minutes:
        return record
    hr = pd.to_numeric(paired["heart_rate"], errors="coerce")
    stress_values = pd.to_numeric(paired["stress_level"], errors="coerce")
    valid = hr.notna() & stress_values.notna()
    paired = paired.loc[valid].copy()
    hr = hr.loc[valid].astype(float)
    stress_values = stress_values.loc[valid].astype(float)
    if len(paired) < config.min_paired_minutes:
        return record
    record[f"{phase}_hr_stress_corr"] = float(hr.corr(stress_values)) if hr.nunique() > 1 and stress_values.nunique() > 1 else np.nan
    if hr.nunique() > 1:
        slope, intercept = np.polyfit(hr.to_numpy(dtype=float), stress_values.to_numpy(dtype=float), 1)
        predicted = slope * hr.to_numpy(dtype=float) + intercept
        total_ss = float(((stress_values - stress_values.mean()) ** 2).sum())
        residual_ss = float(((stress_values - predicted) ** 2).sum())
        record[f"{phase}_stress_hr_slope"] = float(slope)
        record[f"{phase}_stress_hr_r2"] = float(1.0 - residual_ss / total_ss) if total_ss > 0 else np.nan

    ordered = paired.reset_index(drop=True)
    timestamps = pd.to_datetime(ordered["timestamp_utc"], errors="coerce", utc=True)
    gaps = timestamps.diff().dt.total_seconds() / 60.0
    eligible = gaps <= config.gap_break_minutes
    eligible.iloc[0] = False
    hr_diff = pd.to_numeric(ordered["heart_rate"], errors="coerce").diff().loc[eligible]
    stress_diff = pd.to_numeric(ordered["stress_level"], errors="coerce").diff().loc[eligible]
    if len(hr_diff.dropna()) >= 2 and hr_diff.nunique() > 1 and stress_diff.nunique() > 1:
        record[f"{phase}_hr_diff_stress_diff_corr"] = float(hr_diff.corr(stress_diff))

    denominator = len(paired)
    record[f"{phase}_frac_hr_zone2_plus_stress_high"] = float(
        ((hr >= 0.60 * config.max_hr_bpm) & (stress_values >= 76)).sum() / denominator
    )
    record[f"{phase}_frac_hr_below_zone1_stress_high"] = float(
        ((hr < 0.50 * config.max_hr_bpm) & (stress_values >= 76)).sum() / denominator
    )
    return record


def _sleep_wake_contrasts(record: dict[str, Any]) -> dict[str, float]:
    contrast_specs = [
        ("hr_wake_mean_minus_sleep_mean", "wake_hr_mean", "sleep_hr_mean"),
        ("hr_wake_median_minus_sleep_median", "wake_hr_median", "sleep_hr_median"),
        ("hr_wake_p90_minus_sleep_p90", "wake_hr_p90", "sleep_hr_p90"),
        ("stress_wake_mean_minus_sleep_mean", "wake_stress_mean", "sleep_stress_mean"),
        ("stress_wake_median_minus_sleep_median", "wake_stress_median", "sleep_stress_median"),
        ("stress_wake_p90_minus_sleep_p90", "wake_stress_p90", "sleep_stress_p90"),
        (
            "stress_wake_high_fraction_minus_sleep_high_fraction",
            "wake_stress_frac_high",
            "sleep_stress_frac_high",
        ),
        (
            "stress_wake_active_fraction_minus_sleep_active_fraction",
            "wake_stress_frac_active",
            "sleep_stress_frac_active",
        ),
    ]
    out: dict[str, float] = {}
    for output, wake_col, sleep_col in contrast_specs:
        wake = record.get(wake_col, np.nan)
        sleep = record.get(sleep_col, np.nan)
        out[output] = wake - sleep if pd.notna(wake) and pd.notna(sleep) else np.nan
    return out


def _assert_no_forbidden_feature_columns(feature_df: pd.DataFrame, *, max_columns: int | None = None) -> None:
    bad = [column for column in feature_df.columns if any(token in column for token in FORBIDDEN_FEATURE_TOKENS)]
    if bad:
        raise ValueError(f"Forbidden legacy/quality feature columns present: {bad[:20]}")
    if max_columns is not None and feature_df.shape[1] > max_columns:
        raise ValueError(f"Feature table has {feature_df.shape[1]} columns; expected at most {max_columns}")


def build_monitoring_features_full(
    heart_rate_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    quality_index_df: pd.DataFrame,
    foundation_features_df: pd.DataFrame | None = None,
    *,
    max_hr_bpm: float = 192.0,
    gap_break_minutes: float = 2.0,
    min_valid_minutes: int = 5,
    min_paired_minutes: int = 10,
) -> pd.DataFrame:
    """Build the curated cleaned full v0 monitoring feature table."""
    del foundation_features_df
    config = MonitoringCoreConfig(
        max_hr_bpm=float(max_hr_bpm),
        gap_break_minutes=float(gap_break_minutes),
        min_valid_minutes=int(min_valid_minutes),
        min_paired_minutes=int(min_paired_minutes),
    )
    if config.max_hr_bpm <= 0:
        raise ValueError("max_hr_bpm must be positive")
    if config.gap_break_minutes <= 0:
        raise ValueError("gap_break_minutes must be positive")
    if config.min_valid_minutes < 1:
        raise ValueError("min_valid_minutes must be at least 1")
    if config.min_paired_minutes < 2:
        raise ValueError("min_paired_minutes must be at least 2")

    if quality_index_df.empty:
        return pd.DataFrame(columns=["analysis_window_id", "calendarDate"])

    heart_rate = _indexed_by_timestamp(_normalize_hr(heart_rate_df))
    stress = _indexed_by_timestamp(_normalize_stress(stress_df))
    records: list[dict[str, Any]] = []
    for _, row in quality_index_df.iterrows():
        record: dict[str, Any] = {
            "analysis_window_id": str(row["analysis_window_id"]),
            "calendarDate": pd.Timestamp(row["calendarDate"]).normalize(),
        }
        sleep_start = _coerce_utc(row.get("sleep_start_utc"))
        sleep_end = _coerce_utc(row.get("sleep_end_utc"))
        wake_start = _coerce_utc(row.get("wake_start_utc"))
        wake_end = _coerce_utc(row.get("wake_end_utc"))

        if pd.notna(sleep_start) and pd.notna(sleep_end) and sleep_start < sleep_end:
            record.update(_phase_features("sleep", sleep_start, sleep_end, heart_rate, stress, config))
            record.update(_phase_relative_windows("sleep", sleep_start, sleep_end, heart_rate, stress, config))
            record.update(_paired_hr_stress("sleep", sleep_start, sleep_end, heart_rate, stress, config))
            record.update(_sleep_recovery_features(sleep_start, sleep_end, heart_rate, stress, record, config))

        wake_available = (
            pd.notna(wake_start)
            and pd.notna(wake_end)
            and wake_start < wake_end
            and row.get("unsupported_multi_day_gap", 0) == 0
        )
        if wake_available:
            record.update(_phase_features("wake", wake_start, wake_end, heart_rate, stress, config))
            if row.get("wake_duration_plausible", 0) == 1:
                record.update(_phase_relative_windows("wake", wake_start, wake_end, heart_rate, stress, config))
            record.update(_paired_hr_stress("wake", wake_start, wake_end, heart_rate, stress, config))
            if row.get("next_sleep_start_known", 0) == 1:
                record.update(_pre_sleep_features(wake_start, wake_end, heart_rate, stress, config))

        record.update(_sleep_wake_contrasts(record))
        records.append(record)

    out = pd.DataFrame.from_records(records)
    out["calendarDate"] = pd.to_datetime(out["calendarDate"], errors="coerce").dt.normalize()
    out = out.sort_values(["calendarDate", "analysis_window_id"]).reset_index(drop=True)
    _assert_no_forbidden_feature_columns(out, max_columns=400)
    return out


CORE_FEATURE_COLUMNS = [
    "analysis_window_id",
    "calendarDate",
    *[
        f"{phase}_{signal}_{metric}"
        for phase in ["sleep", "wake"]
        for signal in ["hr", "stress"]
        for metric in ["mean", "median", "std", "p90", "histogram_entropy"]
    ],
    *[
        f"{phase}_stress_frac_{state}"
        for phase in ["sleep", "wake"]
        for state in ["resting", "low", "medium", "high", "active"]
    ],
    *[f"wake_hr_frac_{zone}" for zone in ["below_zone1", "zone1", "zone2", "zone3", "zone4", "zone5", "above_mhr"]],
    *[
        f"{phase}_{signal}_{metric}"
        for phase in ["sleep", "wake"]
        for signal in ["hr", "stress"]
        for metric in ["mean_abs_diff", "roughness"]
    ],
    *[
        f"{window}_{signal}_{metric}"
        for window in ["sleep", "wake", "pre_sleep_4h"]
        for signal in ["hr", "stress"]
        for metric in ["slope_per_hour", "trend_r2"]
    ],
    *[
        f"wake_q{idx}_{metric}"
        for idx in range(1, 5)
        for metric in ["hr_mean", "stress_mean", "stress_high_fraction"]
    ],
    *[
        f"pre_sleep_4h_{signal}_{metric}"
        for signal in ["hr", "stress"]
        for metric in ["mean", "std", "p90", "early_minus_late"]
    ],
    "pre_sleep_4h_stress_high_fraction",
    "sleep_hr_q1_minus_q4",
    "sleep_stress_q1_minus_q4",
    "sleep_hr_time_to_min_minutes",
    "sleep_stress_time_to_min_minutes",
    "sleep_stress_time_to_low_stress_minutes",
    "hr_wake_mean_minus_sleep_mean",
    "hr_wake_median_minus_sleep_median",
    "hr_wake_p90_minus_sleep_p90",
    "stress_wake_mean_minus_sleep_mean",
    "stress_wake_median_minus_sleep_median",
    "stress_wake_p90_minus_sleep_p90",
    "stress_wake_high_fraction_minus_sleep_high_fraction",
    "stress_wake_active_fraction_minus_sleep_active_fraction",
]


def select_monitoring_core_features(full_df: pd.DataFrame) -> pd.DataFrame:
    """Select the compact core v0 feature subset from the cleaned full table."""
    columns = [column for column in CORE_FEATURE_COLUMNS if column in full_df.columns]
    out = full_df.loc[:, columns].copy()
    _assert_no_forbidden_feature_columns(out, max_columns=100)
    return out


def build_monitoring_core_features(
    heart_rate_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    quality_index_df: pd.DataFrame,
    *,
    config: MonitoringCoreConfig | None = None,
) -> pd.DataFrame:
    """Build compact core v0 monitoring features for first-pass EDA/modeling."""
    config = config or MonitoringCoreConfig()
    full_df = build_monitoring_features_full(
        heart_rate_df,
        stress_df,
        quality_index_df,
        max_hr_bpm=config.max_hr_bpm,
        gap_break_minutes=config.gap_break_minutes,
        min_valid_minutes=config.min_valid_minutes,
        min_paired_minutes=config.min_paired_minutes,
    )
    return select_monitoring_core_features(full_df)


def _date_range(feature_df: pd.DataFrame) -> str:
    if feature_df.empty or "calendarDate" not in feature_df.columns:
        return "n/a"
    dates = pd.to_datetime(feature_df["calendarDate"], errors="coerce").dropna()
    if dates.empty:
        return "n/a"
    return f"{dates.min().date()} to {dates.max().date()}"


def _feature_family(column: str) -> str:
    if column in {"analysis_window_id", "calendarDate"}:
        return "identifier"
    if "_q" in column and any(column.startswith(f"{phase}_q") for phase in ["sleep", "wake"]):
        return "relative quarters"
    if column.startswith("pre_sleep_4h_"):
        return "pre-sleep/recovery"
    if column.endswith(("_slope_per_hour", "_trend_r2")):
        return "trends"
    if "minus_sleep" in column or "minus_late" in column or "q1_minus_q4" in column or "time_to_" in column:
        return "recovery/contrast"
    if "_stress_frac_" in column:
        return "stress states"
    if "_hr_frac_" in column:
        return "HR MHR zones"
    if column.endswith(("_mean_abs_diff", "_median_abs_diff", "_std_diff", "_roughness", "_max_abs_jump")):
        return "variability"
    if "episode" in column or column.endswith(("_has_event", "_total_minutes", "_duration_minutes", "_fragmentation_index")):
        return "episodes"
    if "hr_stress" in column or "stress_hr" in column or "_frac_hr_" in column:
        return "HR/stress coupling"
    return "distribution/shape"


def _family_counts(feature_df: pd.DataFrame) -> pd.Series:
    if feature_df.empty:
        return pd.Series(dtype=int)
    families = pd.Series([_feature_family(column) for column in feature_df.columns], dtype="string")
    return families.value_counts().sort_index()


def build_monitoring_quality_summary_markdown(
    quality_index_df: pd.DataFrame,
    quality_windows_df: pd.DataFrame,
) -> str:
    rows = len(quality_index_df)
    status_counts = quality_index_df.get("next_sleep_status", pd.Series(dtype=str)).value_counts(dropna=False)
    confidence_counts = quality_index_df.get("boundary_confidence", pd.Series(dtype=str)).value_counts(dropna=False)
    wake_source_counts = quality_index_df.get("wake_end_source", pd.Series(dtype=str)).value_counts(dropna=False)
    synthetic = int((quality_index_df.get("synthetic_wake_split_utc", pd.Series(dtype=float)).notna()).sum())
    unsupported = int((quality_index_df.get("unsupported_multi_day_gap", pd.Series(dtype=float)) == 1).sum())
    observed_next = int((quality_index_df.get("next_sleep_start_known", pd.Series(dtype=float)) == 1).sum())
    plausible = int((quality_index_df.get("semantic_window_plausible", pd.Series(dtype=float)) == 1).sum())
    eligible = int((quality_index_df.get("modeling_recovery_v0_eligible", pd.Series(dtype=float)) == 1).sum())
    max_accepted_wake = pd.to_numeric(quality_index_df.get("wake_duration_hours", pd.Series(dtype=float)), errors="coerce").max()
    max_observed_wake = pd.to_numeric(
        quality_index_df.get("observed_wake_duration_hours", pd.Series(dtype=float)), errors="coerce"
    ).max()

    lines = [
        "# Monitoring Quality Summary",
        "",
        "This report summarizes the compact quality layer used before feature selection. Processed parquet files remain local.",
        "",
        "## Outputs",
        "",
        "- `data/processed/monitoring_quality_index.parquet`",
        "",
        "## Analysis Rows",
        "",
        f"- Analysis rows: `{rows:,}`",
        f"- Rows with observed next sleep boundary: `{observed_next:,}`",
        f"- Rows with synthetic split timestamp populated: `{synthetic:,}`",
        f"- Unsupported multi-day gap rows: `{unsupported:,}`",
        f"- Rows plausible under `2..16h` sleep and `6..30h` wake bounds: `{plausible:,}`",
        f"- Rows eligible for recovery modeling v0: `{eligible:,}`",
        f"- Max accepted/split wake duration: `{max_accepted_wake:.2f}` hours" if pd.notna(max_accepted_wake) else "- Max accepted/split wake duration: `n/a`",
        f"- Max raw observed wake duration: `{max_observed_wake:.2f}` hours" if pd.notna(max_observed_wake) else "- Max raw observed wake duration: `n/a`",
        "",
        "## Next Sleep Status",
        "",
    ]
    for label, count in status_counts.items():
        lines.append(f"- {label}: `{int(count):,}`")
    lines.extend(["", "## Boundary Confidence", ""])
    for label, count in confidence_counts.items():
        lines.append(f"- {label}: `{int(count):,}`")
    lines.extend(["", "## Wake End Source", ""])
    for label, count in wake_source_counts.items():
        lines.append(f"- {label}: `{int(count):,}`")

    usable_columns = [
        "sleep_hr_usable",
        "sleep_stress_usable",
        "wake_hr_usable",
        "wake_stress_usable",
        "pre_sleep_4h_usable",
        "wake_quarters_usable",
    ]
    lines.extend(["", "## Usable Flags", ""])
    for column in usable_columns:
        if column in quality_index_df.columns:
            count = int((pd.to_numeric(quality_index_df[column], errors="coerce") == 1).sum())
            lines.append(f"- `{column}`: `{count:,}`")

    window_names = ", ".join(sorted(quality_windows_df["window_name"].dropna().unique())) if not quality_windows_df.empty else "n/a"
    lines.extend(
        [
            "",
            "## Internal Quality Windows",
            "",
            "Long-format quality-window diagnostics are computed internally and are not persisted by default.",
            f"- Internal rows evaluated: `{len(quality_windows_df):,}`",
            f"- Logical windows evaluated: `{window_names}`",
            "",
            "## Quality Policy",
            "",
            "- Packet 02 accepts next sleep only before local noon on the day after wake starts.",
            "- After-cutoff next sleeps with observed wake duration up to `30h` are retained as late-but-plausible observed wake boundaries.",
            "- After-cutoff intervals from `30h` to `60h` may be split with an explicit synthetic midpoint when no real calendar-date collision would be created.",
            "- Longer gaps are marked unsupported instead of being expanded into fake analysis days.",
            "- Sleep duration plausibility uses `2..16` hours; wake duration plausibility uses `6..30` hours.",
            "- Quality prioritizes coverage fraction, largest gap duration, boundary coverage, and known/missing boundaries.",
            "- Baseline usable flags allow max gaps up to `360` minutes; analysts can still create stricter subsets such as `*_max_gap_minutes <= 180`.",
            "- `modeling_recovery_v0_eligible` is a baseline row-level recovery modeling flag requiring plausible sleep/wake windows and usable whole sleep/wake HR/stress.",
            "- `pre_sleep_4h_usable` remains an optional pre-sleep anchored-feature diagnostic and is not a hard baseline eligibility requirement.",
            "- Stress quality coverage counts semantic stress observations: raw `0..100` plus raw `-2` only when same-minute valid HR confirms activity.",
            "- Numeric stress feature statistics still use only raw `0..100` values.",
            "- Raw stress `-1` and raw `-2` without same-minute valid HR remain unmeasurable for stress coverage.",
            "- Raw stress `-2` is split into HR-confirmed active proxy and no-HR unmeasurable diagnostics; only same-minute valid HR confirms activity.",
            "",
        ]
    )
    return "\n".join(lines)


def build_monitoring_features_full_summary_markdown(
    feature_df: pd.DataFrame,
    *,
    max_hr_bpm: float,
    gap_break_minutes: float,
    min_valid_minutes: int,
    min_paired_minutes: int,
    catalog_df: pd.DataFrame | None = None,
    catalog_csv_path: str = "reports/monitoring_features_full_catalog.csv",
    catalog_md_path: str = "reports/monitoring_features_full_catalog.md",
) -> str:
    family_counts = (
        catalog_df["family"].value_counts()
        if catalog_df is not None and "family" in catalog_df.columns
        else _family_counts(feature_df)
    )
    lines = [
        "# Monitoring Full Features Summary",
        "",
        "`monitoring_features_full_v0.parquet` is the cleaned Packet 03 feature table for the next feature-selection experiments.",
        "",
        "## Outputs",
        "",
        "- `data/processed/monitoring_features_full_v0.parquet`",
        f"- `{catalog_csv_path}`",
        f"- `{catalog_md_path}`",
        "",
        "## Shape",
        "",
        f"- Rows: `{len(feature_df):,}`",
        f"- Columns: `{feature_df.shape[1]:,}`",
        f"- Calendar date range: `{_date_range(feature_df)}`",
        "",
        "## Build Parameters",
        "",
        f"- Maximum heart rate parameter: `{max_hr_bpm:g}` bpm",
        f"- Gap break threshold: `{gap_break_minutes:g}` minutes",
        f"- Minimum valid minutes: `{min_valid_minutes}`",
        f"- Minimum paired HR/stress minutes: `{min_paired_minutes}`",
        "",
        "## Feature Family Counts",
        "",
    ]
    for family, count in family_counts.items():
        lines.append(f"- {family}: `{int(count):,}`")

    lines.extend(
        [
            "",
            "## Included Families",
            "",
            "- Distribution/shape summaries for sleep and wake HR and valid numeric stress.",
            "- Simplified stress state fractions, including `stress_frac_active` from raw stress `-2` only when same-minute valid HR confirms activity.",
            "- HR maximum-heart-rate zone fractions for sleep and wake.",
            "- Gap-aware variability without exposing gap counters as model features.",
            "- A small curated episode set with explicit no-event zero semantics.",
            "- Sleep/wake quarter summaries, linear trends, pre-sleep recovery, sleep-wake contrasts, and HR/stress coupling.",
            "",
            "## Explicitly Excluded From Feature Tables",
            "",
            "- `p05`, `p95`, and `trimmed_mean` distribution variants.",
            "- `stress_frac_medium_or_high` and other rolled-up stress states.",
            "- Anchored window families such as `first_30m_after_wake`, `first_2h_after_wake`, `last_2h_before_sleep`, and `last_4h_before_sleep`.",
            "- Endpoint diagnostics and `end_minus_start` contrasts.",
            "- Coverage fractions, valid counts, total counts, max-gap metrics, and boundary timing diagnostics.",
            "- Raw `-1`/`-2` diagnostic fractions, except the curated HR-confirmed `stress_frac_active` feature.",
            "- Activation scores/bands and spectral period/frequency features.",
            "",
            "## Stress And Entropy Policy",
            "",
            "- Numeric stress features use only valid raw stress `0..100`.",
            "- `stress_frac_active` is raw stress `-2` with same-minute valid HR, retained as an active/large-motion proxy rather than high stress.",
            "- Stress entropy uses fixed bins: `0..25`, `26..50`, `51..75`, and `76..100`.",
            "- HR entropy uses fixed maximum-heart-rate zones derived from `max_hr_bpm`.",
            "",
            "## Quality Join Policy",
            "",
            "- Row-level filtering lives in `data/processed/monitoring_quality_index.parquet`.",
            "- Join on `analysis_window_id` before modeling or interpreting window-heavy features.",
            "- `modeling_recovery_v0_eligible` is a baseline row-level flag for plausible sleep-wake-next-sleep windows with usable sleep and whole-wake HR/stress.",
            "- `pre_sleep_4h_usable` is optional for baseline eligibility; filter on it for stricter pre-sleep sensitivity analyses.",
            "- Baseline usable flags allow max gaps up to `360` minutes; use `*_max_gap_minutes <= 180` for stricter gap sensitivity subsets.",
            "- In the quality index, stress coverage and stress usable flags count raw `0..100` plus raw `-2` only when same-minute valid HR confirms activity.",
            "- Numeric stress feature statistics in this table still use only raw `0..100` values.",
            "- The cleaned feature tables intentionally avoid duplicating quality diagnostics as candidate predictors.",
            "",
        ]
    )
    return "\n".join(lines)


def build_monitoring_core_features_summary_markdown(core_df: pd.DataFrame, quality_index_df: pd.DataFrame) -> str:
    family_counts = _family_counts(core_df)
    eligible = int((quality_index_df.get("modeling_recovery_v0_eligible", pd.Series(dtype=float)) == 1).sum())
    lines = [
        "# Monitoring Core Features Summary",
        "",
        "`monitoring_features_core_v0.parquet` is a compact starter subset derived from the cleaned full feature table.",
        "",
        "## Outputs",
        "",
        "- `data/processed/monitoring_features_core_v0.parquet`",
        "",
        "## Shape",
        "",
        f"- Rows: `{len(core_df):,}`",
        f"- Columns: `{core_df.shape[1]:,}`",
        f"- Quality index rows: `{len(quality_index_df):,}`",
        f"- Recovery modeling v0 eligible rows: `{eligible:,}`",
        "",
        "## Core Feature Family Counts",
        "",
    ]
    for family, count in family_counts.items():
        lines.append(f"- {family}: `{int(count):,}`")
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "- Core keeps a small set of whole sleep/wake summaries, simplified stress states, wake HR zones, trends, wake quarters, pre-sleep recovery, and sleep-wake contrasts.",
            "- Core excludes quality/debug columns. Join `monitoring_quality_index.parquet` on `analysis_window_id` for filtering.",
            "- Baseline recovery eligibility does not require `pre_sleep_4h_usable`; use that flag only for stricter pre-sleep sensitivity analyses.",
            "- Baseline usable flags allow max gaps up to `360` minutes, while `*_max_gap_minutes <= 180` remains available as a stricter subset rule.",
            "- Quality stress coverage counts raw `0..100` plus raw `-2` only when same-minute valid HR confirms activity; numeric stress features remain restricted to raw `0..100`.",
            "- Anchored window zoo, endpoint diagnostics, raw status fractions, coverage metrics, and activation/spectral features are absent from core v0.",
            "",
            "## Stress State Semantics",
            "",
            "- `stress_frac_resting`: raw stress `0..25`.",
            "- `stress_frac_low`: raw stress `26..50`.",
            "- `stress_frac_medium`: raw stress `51..75`.",
            "- `stress_frac_high`: raw stress `76..100`.",
            "- `stress_frac_active`: raw stress `-2` with same-minute valid HR, retained as an active/large-motion proxy.",
            "- The denominator excludes raw `-1`, raw `-2` without same-minute valid HR, and minutes with no stress row.",
            "",
        ]
    )
    return "\n".join(lines)
