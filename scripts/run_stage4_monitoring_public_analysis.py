from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/wearable-analytics-matplotlib")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


DEFAULT_SELECTED_DATE = "2026-02-10"
DISPLAY_TIMEZONE = "Europe/Berlin"


@dataclass(frozen=True)
class MonitoringEdaData:
    root: Path
    heart_rate: pd.DataFrame
    stress: pd.DataFrame
    semantic_windows: pd.DataFrame
    quality: pd.DataFrame
    core_features: pd.DataFrame
    full_features: pd.DataFrame
    catalog: pd.DataFrame


def find_repo_root(start: Path | None = None) -> Path:
    start = Path.cwd() if start is None else Path(start)
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "data").exists():
            return candidate
    raise FileNotFoundError("Could not locate repository root")


def load_stage4_monitoring_data(root: Path | None = None) -> MonitoringEdaData:
    root = find_repo_root() if root is None else Path(root)
    data_dir = root / "data" / "processed"
    report_dir = root / "reports"
    paths = {
        "heart_rate": data_dir / "monitoring_heart_rate.parquet",
        "stress": data_dir / "monitoring_stress.parquet",
        "semantic_windows": data_dir / "semantic_sleep_windows.parquet",
        "quality": data_dir / "monitoring_quality_index.parquet",
        "core_features": data_dir / "monitoring_features_core_v0.parquet",
        "full_features": data_dir / "monitoring_features_full_v0.parquet",
        "catalog": report_dir / "monitoring_features_full_catalog.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required Stage 4 input(s): {missing}")

    frames: dict[str, pd.DataFrame] = {
        "heart_rate": pd.read_parquet(paths["heart_rate"]),
        "stress": pd.read_parquet(paths["stress"]),
        "semantic_windows": pd.read_parquet(paths["semantic_windows"]),
        "quality": pd.read_parquet(paths["quality"]),
        "core_features": pd.read_parquet(paths["core_features"]),
        "full_features": pd.read_parquet(paths["full_features"]),
        "catalog": pd.read_csv(paths["catalog"]),
    }
    for frame in frames.values():
        _normalize_monitoring_dates(frame)

    return MonitoringEdaData(root=root, **frames)


def _normalize_monitoring_dates(frame: pd.DataFrame) -> None:
    for column in frame.columns:
        if column.endswith("_utc") or column == "timestamp_utc":
            frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True)
    if "calendarDate" in frame.columns:
        frame["calendarDate"] = pd.to_datetime(frame["calendarDate"], errors="coerce").dt.normalize()


def date_range_text(frame: pd.DataFrame, column: str) -> str:
    if column not in frame.columns or frame[column].dropna().empty:
        return ""
    values = frame[column].dropna()
    return f"{values.min().date()} to {values.max().date()}"


def monitoring_inventory(data: MonitoringEdaData) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "table": "monitoring_heart_rate",
                "rows": len(data.heart_rate),
                "columns": data.heart_rate.shape[1],
                "date_range": date_range_text(data.heart_rate, "timestamp_utc"),
            },
            {
                "table": "monitoring_stress",
                "rows": len(data.stress),
                "columns": data.stress.shape[1],
                "date_range": date_range_text(data.stress, "timestamp_utc"),
            },
            {
                "table": "semantic_sleep_windows",
                "rows": len(data.semantic_windows),
                "columns": data.semantic_windows.shape[1],
                "date_range": date_range_text(data.semantic_windows, "calendarDate"),
            },
            {
                "table": "monitoring_quality_index",
                "rows": len(data.quality),
                "columns": data.quality.shape[1],
                "date_range": date_range_text(data.quality, "calendarDate"),
            },
            {
                "table": "monitoring_features_core_v0",
                "rows": len(data.core_features),
                "columns": data.core_features.shape[1],
                "date_range": date_range_text(data.core_features, "calendarDate"),
            },
            {
                "table": "monitoring_features_full_v0",
                "rows": len(data.full_features),
                "columns": data.full_features.shape[1],
                "date_range": date_range_text(data.full_features, "calendarDate"),
            },
        ]
    )


def stress_status_counts(data: MonitoringEdaData) -> pd.DataFrame:
    return (
        data.stress["stress_status"]
        .value_counts(dropna=False)
        .rename_axis("stress_status")
        .reset_index(name="rows")
    )


def quality_funnel(data: MonitoringEdaData) -> pd.DataFrame:
    quality = data.quality
    usable_cols = ["sleep_hr_usable", "sleep_stress_usable", "wake_hr_usable", "wake_stress_usable"]
    usable_all = quality[usable_cols].eq(1).all(axis=1)
    out = pd.DataFrame(
        [
            {"step": "Observed semantic sleep windows", "rows": len(data.semantic_windows)},
            {"step": "Analysis windows after boundary policy", "rows": len(quality)},
            {"step": "Rows with observed next sleep boundary", "rows": int(quality["next_sleep_start_utc"].notna().sum())},
            {
                "step": "Rows plausible under sleep/wake duration bounds",
                "rows": int(quality["semantic_window_plausible"].eq(1).sum()),
            },
            {"step": "Rows usable for sleep and wake HR/stress", "rows": int(usable_all.sum())},
            {
                "step": "Rows eligible for recovery modeling v0",
                "rows": int(quality["modeling_recovery_v0_eligible"].eq(1).sum()),
            },
        ]
    )
    out["share_of_analysis_rows"] = np.where(
        out["step"].eq("Observed semantic sleep windows"), np.nan, out["rows"] / len(quality)
    )
    return out


def boundary_counts(data: MonitoringEdaData) -> pd.DataFrame:
    return (
        data.quality["boundary_confidence"]
        .value_counts(dropna=False)
        .rename_axis("boundary_confidence")
        .reset_index(name="rows")
    )


def usable_flag_counts(data: MonitoringEdaData) -> pd.DataFrame:
    cols = [
        "sleep_hr_usable",
        "sleep_stress_usable",
        "wake_hr_usable",
        "wake_stress_usable",
        "pre_sleep_4h_usable",
        "wake_quarters_usable",
        "modeling_recovery_v0_eligible",
    ]
    return pd.DataFrame({"flag": cols, "rows": [int(data.quality[col].eq(1).sum()) for col in cols]})


def monthly_quality_summary(data: MonitoringEdaData) -> pd.DataFrame:
    quality = data.quality.copy()
    quality["month"] = quality["calendarDate"].dt.to_period("M").dt.to_timestamp()
    grouped = quality.groupby("month", as_index=False)
    out = grouped.agg(
        analysis_rows=("analysis_window_id", "count"),
        eligible_rows=("modeling_recovery_v0_eligible", "sum"),
        wake_hr_usable_rows=("wake_hr_usable", "sum"),
        wake_stress_usable_rows=("wake_stress_usable", "sum"),
    )
    status_counts = (
        quality.pivot_table(
            index="month",
            columns="boundary_confidence",
            values="analysis_window_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    out = out.merge(status_counts, on="month", how="left")
    for column in ["synthetic_split", "unsupported_multi_day_gap", "missing_next_sleep"]:
        if column not in out.columns:
            out[column] = 0
    out["eligible_rate"] = out["eligible_rows"] / out["analysis_rows"]
    return out.sort_values("month").reset_index(drop=True)


def coverage_long(data: MonitoringEdaData) -> pd.DataFrame:
    label_map = {
        "sleep_hr_coverage_fraction": ("sleep", "HR", "Sleep HR"),
        "sleep_stress_coverage_fraction": ("sleep", "stress", "Sleep stress"),
        "wake_hr_coverage_fraction": ("wake", "HR", "Wake HR"),
        "wake_stress_coverage_fraction": ("wake", "stress", "Wake stress"),
    }
    rows = []
    for column, (phase, signal, label) in label_map.items():
        values = pd.to_numeric(data.quality[column], errors="coerce").dropna()
        rows.append(pd.DataFrame({"metric": label, "phase": phase, "signal": signal, "coverage_fraction": values}))
    return pd.concat(rows, ignore_index=True)


def coverage_summary(data: MonitoringEdaData) -> pd.DataFrame:
    out = (
        coverage_long(data)
        .groupby(["phase", "signal", "metric"], as_index=False)["coverage_fraction"]
        .agg(count="count", median="median", p10=lambda s: s.quantile(0.10), p90=lambda s: s.quantile(0.90))
    )
    return out


def feature_table_overview(data: MonitoringEdaData) -> tuple[pd.DataFrame, pd.DataFrame]:
    shapes = pd.DataFrame(
        [
            {"feature_table": "core v0", "rows": data.core_features.shape[0], "columns": data.core_features.shape[1]},
            {"feature_table": "full v0", "rows": data.full_features.shape[0], "columns": data.full_features.shape[1]},
        ]
    )
    families = (
        data.catalog.groupby("family", dropna=False)
        .size()
        .sort_values(ascending=False)
        .rename("columns")
        .reset_index()
    )
    return shapes, families


def eligible_core_frame(data: MonitoringEdaData) -> pd.DataFrame:
    keys = ["analysis_window_id", "calendarDate"]
    eligible = data.quality.loc[data.quality["modeling_recovery_v0_eligible"].eq(1), keys].copy()
    return eligible.merge(data.core_features, on=keys, how="left", validate="1:1")


def quality_full_frame(data: MonitoringEdaData) -> pd.DataFrame:
    keys = ["analysis_window_id", "calendarDate"]
    return data.quality.merge(data.full_features, on=keys, how="left", validate="1:1")


def stress_state_summary(data: MonitoringEdaData) -> pd.DataFrame:
    frame = eligible_core_frame(data)
    columns = [
        "wake_stress_frac_resting",
        "wake_stress_frac_low",
        "wake_stress_frac_medium",
        "wake_stress_frac_high",
        "wake_stress_frac_active",
    ]
    rows = []
    for column in columns:
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        rows.append(
            {
                "state": column.replace("wake_stress_frac_", ""),
                "mean_fraction": float(values.mean()),
                "median_fraction": float(values.median()),
                "p25": float(values.quantile(0.25)),
                "p75": float(values.quantile(0.75)),
            }
        )
    return pd.DataFrame(rows)


def hr_zone_summary(data: MonitoringEdaData) -> pd.DataFrame:
    frame = eligible_core_frame(data)
    columns = [
        "wake_hr_frac_below_zone1",
        "wake_hr_frac_zone1",
        "wake_hr_frac_zone2",
        "wake_hr_frac_zone3",
        "wake_hr_frac_zone4",
        "wake_hr_frac_zone5",
        "wake_hr_frac_above_mhr",
    ]
    rows = []
    for column in columns:
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        label = column.replace("wake_hr_frac_", "").replace("_", " ")
        rows.append({"zone": label, "mean_fraction": float(values.mean()), "median_fraction": float(values.median())})
    return pd.DataFrame(rows)


def quarter_shape(data: MonitoringEdaData, phase: str) -> pd.DataFrame:
    if phase not in {"wake", "sleep"}:
        raise ValueError("phase must be 'wake' or 'sleep'")

    frame = quality_full_frame(data)
    if phase == "wake":
        frame = frame[frame["modeling_recovery_v0_eligible"].eq(1)].copy()
    else:
        frame = frame[
            frame["semantic_window_plausible"].eq(1)
            & frame["sleep_hr_usable"].eq(1)
            & frame["sleep_stress_usable"].eq(1)
        ].copy()

    rows = []
    for quarter in range(1, 5):
        for signal in ["hr", "stress"]:
            column = f"{phase}_q{quarter}_{signal}_mean"
            if column not in frame.columns:
                continue
            values = pd.to_numeric(frame[column], errors="coerce").dropna()
            if values.empty:
                continue
            rows.append(
                {
                    "phase": phase,
                    "quarter": f"Q{quarter}",
                    "signal": "Heart rate" if signal == "hr" else "Stress",
                    "rows": int(values.shape[0]),
                    "mean_value": float(values.mean()),
                    "median_value": float(values.median()),
                    "p25": float(values.quantile(0.25)),
                    "p75": float(values.quantile(0.75)),
                }
            )
    return pd.DataFrame(rows)


def wake_quarter_shape(data: MonitoringEdaData) -> pd.DataFrame:
    return quarter_shape(data, "wake")


def sleep_quarter_shape(data: MonitoringEdaData) -> pd.DataFrame:
    return quarter_shape(data, "sleep")


def pre_sleep_summary(data: MonitoringEdaData) -> pd.DataFrame:
    frame = eligible_core_frame(data)
    usable = data.quality.loc[data.quality["modeling_recovery_v0_eligible"].eq(1), ["analysis_window_id", "pre_sleep_4h_usable"]]
    frame = frame.merge(usable, on="analysis_window_id", how="left", validate="1:1")
    rows = [
        {"metric": "eligible rows", "value": int(len(frame))},
        {"metric": "pre_sleep_4h_usable rows", "value": int(frame["pre_sleep_4h_usable"].eq(1).sum())},
    ]
    for column in [
        "pre_sleep_4h_hr_mean",
        "pre_sleep_4h_stress_mean",
        "pre_sleep_4h_hr_early_minus_late",
        "pre_sleep_4h_stress_early_minus_late",
    ]:
        if column not in frame.columns:
            continue
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        rows.append({"metric": column, "value": float(values.median()) if not values.empty else np.nan})
    return pd.DataFrame(rows)


def choose_analysis_window(quality: pd.DataFrame, selected_date: str | None = DEFAULT_SELECTED_DATE) -> pd.Series:
    coverage_cols = [
        "sleep_hr_coverage_fraction",
        "sleep_stress_coverage_fraction",
        "wake_hr_coverage_fraction",
        "wake_stress_coverage_fraction",
    ]
    gap_cols = [
        "sleep_hr_max_gap_minutes",
        "sleep_stress_max_gap_minutes",
        "wake_hr_max_gap_minutes",
        "wake_stress_max_gap_minutes",
    ]
    scored = quality.copy()
    scored["coverage_score"] = scored[coverage_cols].mean(axis=1)
    scored["largest_gap"] = scored[gap_cols].max(axis=1)
    sort_cols = ["modeling_recovery_v0_eligible", "coverage_score", "largest_gap", "calendarDate"]
    sort_ascending = [False, False, True, False]
    if selected_date is not None:
        selected_day = pd.Timestamp(selected_date).normalize()
        matches = scored[scored["calendarDate"].eq(selected_day)].copy()
        if matches.empty:
            valid_min = scored["calendarDate"].min().date().isoformat()
            valid_max = scored["calendarDate"].max().date().isoformat()
            raise ValueError(f"No monitoring analysis window for {selected_date}. Valid range: {valid_min} to {valid_max}.")
        return matches.sort_values(sort_cols, ascending=sort_ascending).iloc[0]
    eligible = scored[scored["modeling_recovery_v0_eligible"].eq(1)].copy()
    return eligible.sort_values(sort_cols, ascending=sort_ascending).iloc[0]


def select_representative_day_gallery(data: MonitoringEdaData) -> pd.DataFrame:
    quality = data.quality.copy()
    coverage_cols = [
        "sleep_hr_coverage_fraction",
        "sleep_stress_coverage_fraction",
        "wake_hr_coverage_fraction",
        "wake_stress_coverage_fraction",
    ]
    gap_cols = [
        "sleep_hr_max_gap_minutes",
        "sleep_stress_max_gap_minutes",
        "wake_hr_max_gap_minutes",
        "wake_stress_max_gap_minutes",
    ]
    quality["coverage_score"] = quality[coverage_cols].mean(axis=1)
    quality["largest_gap_minutes"] = quality[gap_cols].max(axis=1)

    metrics = data.core_features[
        [
            "analysis_window_id",
            "wake_stress_frac_high",
            "wake_stress_frac_active",
            "wake_hr_frac_zone2",
            "wake_hr_frac_zone3",
            "wake_hr_frac_zone4",
            "wake_hr_frac_zone5",
        ]
    ].copy()
    load_cols = [column for column in metrics.columns if column != "analysis_window_id"]
    metrics["wake_load_score"] = metrics[load_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
    quality = quality.merge(metrics[["analysis_window_id", "wake_load_score"]], on="analysis_window_id", how="left", validate="1:1")

    rows: list[pd.Series] = []
    chosen_ids: set[str] = set()

    high_quality = quality[
        quality["modeling_recovery_v0_eligible"].eq(1)
        & quality["boundary_confidence"].eq("observed")
        & quality["wake_end_utc"].notna()
    ].copy()
    if not high_quality.empty:
        selected = high_quality.sort_values(
            ["coverage_score", "largest_gap_minutes", "calendarDate"],
            ascending=[False, True, False],
        ).iloc[0].copy()
        selected["gallery_label"] = "high_quality_reference"
        selected["selection_reason"] = "Observed eligible window with high combined HR/stress coverage and small gaps."
        rows.append(selected)
        chosen_ids.add(str(selected["analysis_window_id"]))

    load_candidates = quality[
        quality["modeling_recovery_v0_eligible"].eq(1)
        & quality["wake_end_utc"].notna()
        & ~quality["analysis_window_id"].astype(str).isin(chosen_ids)
    ].copy()
    if not load_candidates.empty:
        selected = load_candidates.sort_values(
            ["wake_load_score", "coverage_score", "largest_gap_minutes"],
            ascending=[False, False, True],
        ).iloc[0].copy()
        selected["gallery_label"] = "high_wake_load"
        selected["selection_reason"] = "Eligible window with high wake stress-state and elevated-HR-zone signal."
        rows.append(selected)
        chosen_ids.add(str(selected["analysis_window_id"]))

    issue_priority = {
        "unsupported_multi_day_gap": 0,
        "synthetic_split": 1,
        "missing_next_sleep": 2,
        "observed_late_within_duration": 3,
        "observed": 4,
    }
    issue_candidates = quality[
        (quality["modeling_recovery_v0_eligible"].ne(1) | quality["boundary_confidence"].ne("observed"))
        & quality["sleep_start_utc"].notna()
        & quality["wake_start_utc"].notna()
        & quality["wake_end_utc"].notna()
        & ~quality["analysis_window_id"].astype(str).isin(chosen_ids)
    ].copy()
    if not issue_candidates.empty:
        issue_candidates["issue_priority"] = issue_candidates["boundary_confidence"].map(issue_priority).fillna(9)
        selected = issue_candidates.sort_values(
            ["issue_priority", "coverage_score", "calendarDate"],
            ascending=[True, False, False],
        ).iloc[0].copy()
        selected["gallery_label"] = "imperfect_gap_or_boundary"
        selected["selection_reason"] = "Non-observed or non-eligible window that keeps a visible boundary/quality issue in view."
        rows.append(selected)

    gallery = pd.DataFrame(rows)
    if gallery.empty:
        return gallery

    gallery = gallery.drop_duplicates("analysis_window_id", keep="first").reset_index(drop=True)
    return gallery[
        [
            "gallery_label",
            "calendarDate",
            "analysis_window_id",
            "boundary_confidence",
            "modeling_recovery_v0_eligible",
            "coverage_score",
            "largest_gap_minutes",
            "selection_reason",
        ]
    ]


def prepare_day_browser_data(data: MonitoringEdaData, selected: pd.Series) -> dict[str, Any]:
    start_utc = selected["sleep_start_utc"]
    end_utc = selected["wake_end_utc"]
    if pd.isna(end_utc):
        end_utc = selected["next_sleep_start_utc"]
    if pd.isna(start_utc) or pd.isna(end_utc):
        raise ValueError("Selected day is missing a complete display window")

    offset = float(selected.get("local_utc_offset_minutes", 0.0))
    heart_rate = _window_subset(data.heart_rate, start_utc, end_utc)
    stress = _window_subset(data.stress, start_utc, end_utc)

    valid_hr_times = set(heart_rate.loc[heart_rate["heart_rate_status"].eq("valid"), "timestamp_utc"])
    stress["same_minute_valid_hr"] = stress["timestamp_utc"].isin(valid_hr_times)
    stress["numeric_stress"] = np.where(stress["stress_level_raw"].between(0, 100), stress["stress_level_raw"].astype(float), np.nan)
    stress["stress_semantic_status"] = "valid_stress"
    stress.loc[stress["stress_level_raw"].eq(-2) & stress["same_minute_valid_hr"], "stress_semantic_status"] = "active_proxy"
    stress.loc[stress["stress_level_raw"].eq(-2) & ~stress["same_minute_valid_hr"], "stress_semantic_status"] = "unmeasurable_minus_2_no_hr"
    stress.loc[stress["stress_level_raw"].eq(-1), "stress_semantic_status"] = "unmeasurable_minus_1"

    heart_rate["timestamp_local"] = _localize_series(heart_rate["timestamp_utc"], offset)
    stress["timestamp_local"] = _localize_series(stress["timestamp_utc"], offset)
    context = {
        "analysis_window_id": selected["analysis_window_id"],
        "calendarDate": selected["calendarDate"],
        "boundary_confidence": selected["boundary_confidence"],
        "modeling_recovery_v0_eligible": int(selected["modeling_recovery_v0_eligible"]),
        "sleep_start": _localize_timestamp(selected["sleep_start_utc"], offset),
        "wake_start": _localize_timestamp(selected["wake_start_utc"], offset),
        "wake_end": _localize_timestamp(selected["wake_end_utc"], offset),
    }
    summary = pd.DataFrame(
        [
            {"metric": "selected_date", "value": selected["calendarDate"].date().isoformat()},
            {"metric": "analysis_window_id", "value": selected["analysis_window_id"]},
            {"metric": "boundary_confidence", "value": selected["boundary_confidence"]},
            {"metric": "modeling_recovery_v0_eligible", "value": int(selected["modeling_recovery_v0_eligible"])},
            {"metric": "HR rows in window", "value": len(heart_rate)},
            {"metric": "stress rows in window", "value": len(stress)},
            {"metric": "valid numeric stress rows", "value": int(stress["numeric_stress"].notna().sum())},
            {"metric": "active proxy rows", "value": int(stress["stress_semantic_status"].eq("active_proxy").sum())},
            {
                "metric": "unmeasurable -2 rows without HR",
                "value": int(stress["stress_semantic_status"].eq("unmeasurable_minus_2_no_hr").sum()),
            },
            {"metric": "unmeasurable -1 rows", "value": int(stress["stress_semantic_status"].eq("unmeasurable_minus_1").sum())},
        ]
    )
    return {"heart_rate": heart_rate, "stress": stress, "context": context, "summary": summary}


def _window_subset(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    mask = frame["timestamp_utc"].ge(start) & frame["timestamp_utc"].lt(end)
    return frame.loc[mask].sort_values("timestamp_utc").copy()


def _localize_timestamp(value: Any, offset_minutes: float) -> pd.Timestamp:
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(ts):
        return pd.NaT
    return pd.Timestamp(ts + pd.Timedelta(minutes=float(offset_minutes))).tz_localize(None)


def _localize_series(series: pd.Series, offset_minutes: float) -> pd.Series:
    ts = pd.to_datetime(series, errors="coerce", utc=True)
    return (ts + pd.Timedelta(minutes=float(offset_minutes))).dt.tz_localize(None)


def wake_local_time_points(data: MonitoringEdaData) -> pd.DataFrame:
    good_windows = data.quality[
        data.quality["modeling_recovery_v0_eligible"].eq(1)
        & data.quality["wake_start_utc"].notna()
        & data.quality["wake_end_utc"].notna()
    ].copy()
    rows: list[pd.DataFrame] = []

    for _, window in good_windows.iterrows():
        offset = float(window.get("local_utc_offset_minutes", 0.0))
        calendar_day = pd.Timestamp(window["calendarDate"]).normalize()
        wake_start = window["wake_start_utc"]
        wake_end = window["wake_end_utc"]
        wake_duration_seconds = (wake_end - wake_start).total_seconds()
        if wake_duration_seconds <= 0:
            continue

        heart_rate = _window_subset(data.heart_rate, wake_start, wake_end)
        heart_rate = heart_rate[heart_rate["heart_rate_status"].eq("valid")].copy()
        if not heart_rate.empty:
            local_ts = _localize_series(heart_rate["timestamp_utc"], offset)
            wake_fraction = _wake_phase_fraction(heart_rate["timestamp_utc"], wake_start, wake_duration_seconds)
            rows.append(
                pd.DataFrame(
                    {
                        "analysis_window_id": window["analysis_window_id"],
                        "calendarDate": window["calendarDate"],
                        "signal": "Heart rate",
                        "timestamp_local": local_ts,
                        "wake_local_hour": _wake_day_local_hour(local_ts, calendar_day),
                        "wake_phase_fraction": wake_fraction,
                        "value": pd.to_numeric(heart_rate["heart_rate"], errors="coerce"),
                    }
                )
            )

        stress = _window_subset(data.stress, wake_start, wake_end)
        stress = stress[stress["stress_level_raw"].between(0, 100)].copy()
        if not stress.empty:
            local_ts = _localize_series(stress["timestamp_utc"], offset)
            wake_fraction = _wake_phase_fraction(stress["timestamp_utc"], wake_start, wake_duration_seconds)
            rows.append(
                pd.DataFrame(
                    {
                        "analysis_window_id": window["analysis_window_id"],
                        "calendarDate": window["calendarDate"],
                        "signal": "Stress",
                        "timestamp_local": local_ts,
                        "wake_local_hour": _wake_day_local_hour(local_ts, calendar_day),
                        "wake_phase_fraction": wake_fraction,
                        "value": pd.to_numeric(stress["stress_level_raw"], errors="coerce"),
                    }
                )
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "analysis_window_id",
                "calendarDate",
                "signal",
                "timestamp_local",
                "wake_local_hour",
                "wake_phase_fraction",
                "value",
            ]
        )

    points = pd.concat(rows, ignore_index=True)
    return points.dropna(subset=["wake_local_hour", "wake_phase_fraction", "value"]).reset_index(drop=True)


def _wake_day_local_hour(timestamps: pd.Series, calendar_day: pd.Timestamp) -> pd.Series:
    local_day = timestamps.dt.normalize()
    day_offset = (local_day - calendar_day).dt.days.clip(lower=0)
    return timestamps.dt.hour + timestamps.dt.minute / 60.0 + timestamps.dt.second / 3600.0 + 24.0 * day_offset


def _wake_phase_fraction(timestamps_utc: pd.Series, wake_start_utc: pd.Timestamp, wake_duration_seconds: float) -> pd.Series:
    elapsed_seconds = (pd.to_datetime(timestamps_utc, errors="coerce", utc=True) - wake_start_utc).dt.total_seconds()
    return (elapsed_seconds / wake_duration_seconds).clip(lower=0.0, upper=1.0)


def wake_local_time_summary(points: pd.DataFrame, *, bin_minutes: int = 30) -> pd.DataFrame:
    if points.empty:
        return pd.DataFrame(columns=["signal", "local_time_bin", "points", "median", "p25", "p75"])
    bin_width = bin_minutes / 60.0
    frame = points.copy()
    frame["local_time_bin"] = (np.floor(frame["wake_local_hour"] / bin_width) * bin_width).round(3)
    summary = (
        frame.groupby(["signal", "local_time_bin"], as_index=False)["value"]
        .agg(points="count", median="median", p25=lambda s: s.quantile(0.25), p75=lambda s: s.quantile(0.75))
        .sort_values(["signal", "local_time_bin"])
        .reset_index(drop=True)
    )
    return summary


def wake_phase_fraction_summary(points: pd.DataFrame, *, bins: int = 40) -> pd.DataFrame:
    if points.empty:
        return pd.DataFrame(columns=["signal", "phase_fraction_bin", "points", "median", "p25", "p75"])
    bin_width = 1.0 / bins
    frame = points[points["wake_phase_fraction"].between(0, 1)].copy()
    frame["phase_fraction_bin"] = (np.floor(frame["wake_phase_fraction"] / bin_width) * bin_width).clip(upper=1 - bin_width).round(4)
    summary = (
        frame.groupby(["signal", "phase_fraction_bin"], as_index=False)["value"]
        .agg(points="count", median="median", p25=lambda s: s.quantile(0.25), p75=lambda s: s.quantile(0.75))
        .sort_values(["signal", "phase_fraction_bin"])
        .reset_index(drop=True)
    )
    return summary


def contiguous_spans(timestamps: list[pd.Timestamp], gap_minutes: int = 2) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    if not timestamps:
        return []
    ordered = sorted(pd.to_datetime(list(timestamps), errors="coerce"))
    ordered = [ts for ts in ordered if pd.notna(ts)]
    if not ordered:
        return []
    spans = []
    start = ordered[0]
    end = ordered[0]
    for ts in ordered[1:]:
        if ts - end <= pd.Timedelta(minutes=gap_minutes):
            end = ts
            continue
        spans.append((start, end))
        start = ts
        end = ts
    spans.append((start, end))
    return spans


def split_frame_by_gap(frame: pd.DataFrame, timestamp_column: str, gap_minutes: int = 2) -> list[pd.DataFrame]:
    if frame.empty:
        return []
    ordered = frame.sort_values(timestamp_column).copy()
    gap_breaks = ordered[timestamp_column].diff() > pd.Timedelta(minutes=gap_minutes)
    segment_ids = gap_breaks.fillna(False).cumsum()
    return [segment.copy() for _, segment in ordered.groupby(segment_ids)]


def plot_quality_funnel(funnel: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9, 4.2))
    plot_data = funnel[funnel["step"] != "Observed semantic sleep windows"].copy()
    ax.barh(plot_data["step"], plot_data["rows"], color="#2f6f73")
    ax.invert_yaxis()
    ax.set_xlabel("Rows")
    ax.set_title("Monitoring quality funnel")
    for idx, value in enumerate(plot_data["rows"]):
        ax.text(value + 5, idx, f"{value:,}", va="center")
    fig.tight_layout()
    return fig


def plot_quality_over_time(monthly: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(monthly["month"], monthly["analysis_rows"], color="#7c4d79", marker="o", label="analysis rows")
    ax.plot(monthly["month"], monthly["eligible_rows"], color="#2f6f73", marker="o", label="modeling eligible")
    ax.bar(monthly["month"], monthly["unsupported_multi_day_gap"], width=20, color="#c43c4b", alpha=0.35, label="unsupported gaps")
    ax.bar(monthly["month"], monthly["synthetic_split"], width=20, bottom=monthly["unsupported_multi_day_gap"], color="#d8872e", alpha=0.35, label="synthetic split rows")
    ax.set_title("Monitoring quality over time")
    ax.set_ylabel("Rows per month")
    ax.set_xlabel("Month")
    ax.legend(loc="upper left", ncols=2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


def plot_coverage_distributions(coverage: pd.DataFrame) -> plt.Figure:
    metrics = coverage["metric"].drop_duplicates().tolist()
    values = [coverage.loc[coverage["metric"].eq(metric), "coverage_fraction"].dropna() for metric in metrics]
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.boxplot(values, tick_labels=metrics, vert=True, patch_artist=True, boxprops={"facecolor": "#d7e8df"})
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("Coverage fraction")
    ax.set_title("Minute-level coverage by semantic window")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def plot_day_browser(browser: dict[str, Any], *, display_timezone: str = DISPLAY_TIMEZONE, show_status_spans: bool = True) -> plt.Figure:
    heart_rate = browser["heart_rate"]
    stress = browser["stress"]
    context = browser["context"]

    plot_start = context["sleep_start"] - pd.Timedelta(minutes=15)
    plot_end = context["wake_end"] + pd.Timedelta(minutes=15)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    valid_hr = heart_rate[heart_rate["heart_rate_status"].eq("valid")].copy()
    if not valid_hr.empty:
        for segment in split_frame_by_gap(valid_hr, "timestamp_local", gap_minutes=2):
            ax1.plot(segment["timestamp_local"], segment["heart_rate"], color="#1f77b4", linewidth=1.0)
    else:
        ax1.text(0.5, 0.5, "No heart-rate points for selected date", ha="center", va="center", transform=ax1.transAxes)
    _add_window_markers(ax1, context)
    ax1.set_title(
        f"Monitoring browser: {context['calendarDate'].date().isoformat()} ({display_timezone}) - {context['analysis_window_id']}"
    )
    ax1.set_ylabel("Heart rate")
    ax1.grid(alpha=0.25)
    handles, _labels = ax1.get_legend_handles_labels()
    if handles:
        ax1.legend(loc="upper right")

    valid_stress = stress[stress["stress_semantic_status"].eq("valid_stress") & stress["numeric_stress"].notna()].copy()
    if not valid_stress.empty:
        ax2.scatter(
            valid_stress["timestamp_local"],
            valid_stress["numeric_stress"],
            s=10,
            alpha=0.6,
            color="#d62728",
            label="Valid stress",
        )
    elif stress.empty:
        ax2.text(0.5, 0.5, "No stress points for selected date", ha="center", va="center", transform=ax2.transAxes)

    if show_status_spans:
        span_layers = [
            ("active_proxy", "#c8b6ff", 0.18, "Active proxy (-2 + valid HR)"),
            ("unmeasurable_minus_2_no_hr", "#9ea4aa", 0.18, "Unmeasurable (-2 without HR)"),
            ("unmeasurable_minus_1", "#cbbfaf", 0.18, "Unmeasurable (-1)"),
        ]
        for status, color, alpha, label in span_layers:
            status_frame = stress[stress["stress_semantic_status"].eq(status)]
            for index, (start, end) in enumerate(contiguous_spans(status_frame["timestamp_local"].tolist())):
                ax2.axvspan(
                    start,
                    end + pd.Timedelta(minutes=1),
                    color=color,
                    alpha=alpha,
                    label=label if index == 0 else None,
                )

    _add_window_markers(ax2, context)
    ax2.set_ylabel("Stress level")
    ax2.set_xlabel("Time")
    ax2.set_ylim(-4, 105)
    ax2.set_xlim(plot_start, plot_end)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H"))
    ax2.grid(alpha=0.25)
    handles, _labels = ax2.get_legend_handles_labels()
    if handles:
        ax2.legend(loc="upper right")
    fig.tight_layout()
    return fig


def plot_day_gallery(
    data: MonitoringEdaData,
    gallery: pd.DataFrame,
    *,
    display_timezone: str = DISPLAY_TIMEZONE,
    max_days: int = 3,
) -> plt.Figure:
    if gallery.empty:
        fig, ax = plt.subplots(figsize=(10, 2.5))
        ax.text(0.5, 0.5, "No representative monitoring windows available", ha="center", va="center")
        ax.axis("off")
        return fig

    rows = gallery.head(max_days).reset_index(drop=True)
    fig, axes = plt.subplots(len(rows), 1, figsize=(12, 2.8 * len(rows)), sharex=False)
    axes = np.atleast_1d(axes)

    for ax, (_, row) in zip(axes, rows.iterrows()):
        selected = data.quality.loc[data.quality["analysis_window_id"].eq(row["analysis_window_id"])].iloc[0]
        browser = prepare_day_browser_data(data, selected)
        heart_rate = browser["heart_rate"]
        stress = browser["stress"]
        context = browser["context"]

        ax2 = ax.twinx()
        valid_hr = heart_rate[heart_rate["heart_rate_status"].eq("valid")].copy()
        for index, segment in enumerate(split_frame_by_gap(valid_hr, "timestamp_local", gap_minutes=2)):
            ax.plot(
                segment["timestamp_local"],
                segment["heart_rate"],
                color="#1f77b4",
                linewidth=0.9,
                label="Heart rate" if index == 0 else None,
            )

        valid_stress = stress[stress["stress_semantic_status"].eq("valid_stress") & stress["numeric_stress"].notna()].copy()
        if not valid_stress.empty:
            ax2.scatter(
                valid_stress["timestamp_local"],
                valid_stress["numeric_stress"],
                s=8,
                alpha=0.45,
                color="#d62728",
                label="Valid stress",
            )

        for status, color, label in [
            ("active_proxy", "#c8b6ff", "Active proxy"),
            ("unmeasurable_minus_2_no_hr", "#9ea4aa", "Unmeasurable -2"),
            ("unmeasurable_minus_1", "#cbbfaf", "Unmeasurable -1"),
        ]:
            status_frame = stress[stress["stress_semantic_status"].eq(status)]
            for index, (start, end) in enumerate(contiguous_spans(status_frame["timestamp_local"].tolist())):
                ax.axvspan(
                    start,
                    end + pd.Timedelta(minutes=1),
                    color=color,
                    alpha=0.14,
                    label=label if index == 0 else None,
                )

        _add_window_markers(ax, context)
        plot_start = context["sleep_start"] - pd.Timedelta(minutes=15)
        plot_end = context["wake_end"] + pd.Timedelta(minutes=15)
        ax.set_xlim(plot_start, plot_end)
        ax2.set_ylim(-4, 105)
        ax.set_ylabel("HR")
        ax2.set_ylabel("Stress")
        title_label = str(row["gallery_label"]).replace("_", " ")
        ax.set_title(
            f"{title_label}: {context['calendarDate'].date().isoformat()} | "
            f"{context['boundary_confidence']} | eligible={context['modeling_recovery_v0_eligible']}"
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H"))
        ax.grid(alpha=0.22)

    handles: list[Any] = []
    labels: list[str] = []
    for axis in fig.axes:
        axis_handles, axis_labels = axis.get_legend_handles_labels()
        for handle, label in zip(axis_handles, axis_labels):
            if label not in labels:
                handles.append(handle)
                labels.append(label)
    if handles:
        fig.legend(handles, labels, loc="upper center", ncols=min(5, len(handles)), bbox_to_anchor=(0.5, 1.02))
    fig.suptitle(f"Representative monitoring day gallery ({display_timezone})", y=1.04)
    fig.tight_layout()
    return fig


def _add_window_markers(axis: plt.Axes, context: dict[str, Any]) -> None:
    specs = [
        ("sleep_start", "Sleep start", "#2ca02c", "--", 1.4),
        ("wake_start", "Wake start", "#111111", ":", 1.6),
        ("wake_end", "Wake end", "#ff7f0e", "-.", 1.6),
    ]
    plotted: list[pd.Timestamp] = []
    for key, label, color, linestyle, linewidth in specs:
        timestamp = context.get(key)
        if pd.isna(timestamp):
            continue
        if any(abs((timestamp - existing).total_seconds()) < 1 for existing in plotted):
            continue
        plotted.append(timestamp)
        axis.axvline(timestamp, color=color, linestyle=linestyle, linewidth=linewidth, alpha=0.9, label=label)


def plot_stress_state_composition(summary: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    colors = ["#7dbb89", "#c6cf6a", "#d8872e", "#c43c4b", "#8f7bd4"]
    ax.bar(summary["state"], summary["mean_fraction"], color=colors)
    ax.set_ylim(0, max(0.05, summary["mean_fraction"].max() * 1.25))
    ax.set_ylabel("Mean fraction of wake stress-state minutes")
    ax.set_title("Wake stress-state composition among eligible days")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def plot_hr_zone_composition(summary: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.bar(summary["zone"], summary["mean_fraction"], color="#5d8aa8")
    ax.set_ylabel("Mean fraction of wake HR minutes")
    ax.set_title("Wake heart-rate zone composition among eligible days")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def plot_quarter_shape(shape: pd.DataFrame, phase_label: str) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharex=True)
    for ax, signal, color in [
        (axes[0], "Heart rate", "#1f77b4"),
        (axes[1], "Stress", "#d62728"),
    ]:
        subset = shape[shape["signal"].eq(signal)]
        if subset.empty:
            ax.text(0.5, 0.5, f"No {signal.lower()} quarter data", ha="center", va="center", transform=ax.transAxes)
        else:
            ax.plot(subset["quarter"], subset["mean_value"], color=color, marker="o")
            ax.fill_between(subset["quarter"], subset["p25"], subset["p75"], color=color, alpha=0.15)
        ax.set_title(signal)
        ax.set_xlabel(f"{phase_label} quarter")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Mean value")
    fig.suptitle(f"Average within-{phase_label.lower()} shape", y=1.02)
    fig.tight_layout()
    return fig


def plot_wake_quarter_shape(shape: pd.DataFrame) -> plt.Figure:
    return plot_quarter_shape(shape, "Wake")


def plot_sleep_quarter_shape(shape: pd.DataFrame) -> plt.Figure:
    return plot_quarter_shape(shape, "Sleep")


def plot_wake_sleep_quarter_shape(wake_shape: pd.DataFrame, sleep_shape: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5), sharex=True)
    for row_index, (shape, phase_label) in enumerate([(wake_shape, "Wake"), (sleep_shape, "Sleep")]):
        for col_index, (signal, color) in enumerate([("Heart rate", "#1f77b4"), ("Stress", "#d62728")]):
            ax = axes[row_index, col_index]
            subset = shape[shape["signal"].eq(signal)]
            if subset.empty:
                ax.text(0.5, 0.5, f"No {phase_label.lower()} {signal.lower()} data", ha="center", va="center", transform=ax.transAxes)
            else:
                ax.plot(subset["quarter"], subset["mean_value"], color=color, marker="o")
                ax.fill_between(subset["quarter"], subset["p25"], subset["p75"], color=color, alpha=0.15)
            ax.set_title(f"{phase_label} {signal.lower()}")
            ax.set_xlabel(f"{phase_label} quarter")
            ax.grid(alpha=0.25)
        axes[row_index, 0].set_ylabel("Mean value")
    fig.suptitle("Average within-window shape: wake and sleep quarters", y=1.02)
    fig.tight_layout()
    return fig


def plot_wake_local_time_distributions(
    points: pd.DataFrame,
    *,
    bin_minutes: int = 30,
    min_points_per_bin: int = 100,
) -> plt.Figure:
    fig, axes = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
    specs = [
        ("Heart rate", "Blues", "Heart rate"),
        ("Stress", "Reds", "Stress"),
    ]
    x_bins = np.arange(0, 30 + bin_minutes / 60.0, bin_minutes / 60.0)
    plot_points = points[points["wake_local_hour"].between(0, 30)].copy()
    summary = wake_local_time_summary(plot_points, bin_minutes=bin_minutes)

    for ax, (signal, cmap, label) in zip(axes, specs):
        subset = plot_points[plot_points["signal"].eq(signal)].copy()
        if subset.empty:
            ax.text(0.5, 0.5, f"No {label.lower()} wake points", ha="center", va="center", transform=ax.transAxes)
            ax.set_ylabel(label)
            continue

        if signal == "Stress":
            y_bins = np.linspace(0, 100, 61)
        else:
            lower = max(35.0, np.floor(subset["value"].quantile(0.005) / 5.0) * 5.0)
            upper = min(180.0, np.ceil(subset["value"].quantile(0.995) / 5.0) * 5.0)
            if lower >= upper:
                lower, upper = 35.0, 180.0
            y_bins = np.linspace(lower, upper, 60)

        hist = ax.hist2d(
            subset["wake_local_hour"],
            subset["value"],
            bins=[x_bins, y_bins],
            cmap=cmap,
            norm=LogNorm(vmin=1),
        )
        cbar = fig.colorbar(hist[3], ax=ax, pad=0.01)
        cbar.set_label("Minute points")

        signal_summary = summary[summary["signal"].eq(signal)].copy()
        if not signal_summary.empty:
            signal_summary = signal_summary[signal_summary["points"].ge(min_points_per_bin)]
            if not signal_summary.empty:
                mids = signal_summary["local_time_bin"] + bin_minutes / 120.0
                ax.plot(mids, signal_summary["median"], color="#111111", linewidth=2.0, label="median")
                ax.plot(mids, signal_summary["p25"], color="#111111", linestyle="--", linewidth=1.3, label="IQR")
                ax.plot(mids, signal_summary["p75"], color="#111111", linestyle="--", linewidth=1.3)

        ax.set_ylabel(label)
        ax.legend(loc="upper right")
        ax.grid(alpha=0.2)

    axes[-1].set_xlabel("Wake-day local clock hour (after midnight shown as 24+)")
    axes[-1].set_xlim(0, 30)
    axes[-1].set_xticks([0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30])
    axes[-1].set_xticklabels(["00", "03", "06", "09", "12", "15", "18", "21", "24", "03+1", "06+1"])
    fig.suptitle("Wake minute points by local clock time among recovery-eligible days", y=1.02)
    fig.tight_layout()
    return fig


def plot_wake_phase_fraction_distributions(
    points: pd.DataFrame,
    *,
    bins: int = 40,
    min_points_per_bin: int = 100,
) -> plt.Figure:
    fig, axes = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
    specs = [
        ("Heart rate", "Blues", "Heart rate"),
        ("Stress", "Reds", "Stress"),
    ]
    x_bins = np.linspace(0, 1, bins + 1)
    plot_points = points[points["wake_phase_fraction"].between(0, 1)].copy()
    summary = wake_phase_fraction_summary(plot_points, bins=bins)

    for ax, (signal, cmap, label) in zip(axes, specs):
        subset = plot_points[plot_points["signal"].eq(signal)].copy()
        if subset.empty:
            ax.text(0.5, 0.5, f"No {label.lower()} wake points", ha="center", va="center", transform=ax.transAxes)
            ax.set_ylabel(label)
            continue

        if signal == "Stress":
            y_bins = np.linspace(0, 100, 61)
        else:
            lower = max(35.0, np.floor(subset["value"].quantile(0.005) / 5.0) * 5.0)
            upper = min(180.0, np.ceil(subset["value"].quantile(0.995) / 5.0) * 5.0)
            if lower >= upper:
                lower, upper = 35.0, 180.0
            y_bins = np.linspace(lower, upper, 60)

        hist = ax.hist2d(
            subset["wake_phase_fraction"],
            subset["value"],
            bins=[x_bins, y_bins],
            cmap=cmap,
            norm=LogNorm(vmin=1),
        )
        cbar = fig.colorbar(hist[3], ax=ax, pad=0.01)
        cbar.set_label("Minute points")

        signal_summary = summary[summary["signal"].eq(signal)].copy()
        if not signal_summary.empty:
            signal_summary = signal_summary[signal_summary["points"].ge(min_points_per_bin)]
            if not signal_summary.empty:
                mids = signal_summary["phase_fraction_bin"] + 0.5 / bins
                ax.plot(mids, signal_summary["median"], color="#111111", linewidth=2.0, label="median")
                ax.plot(mids, signal_summary["p25"], color="#111111", linestyle="--", linewidth=1.3, label="IQR")
                ax.plot(mids, signal_summary["p75"], color="#111111", linestyle="--", linewidth=1.3)

        ax.set_ylabel(label)
        ax.legend(loc="upper right")
        ax.grid(alpha=0.2)

    axes[-1].set_xlabel("Fraction of wake phase elapsed")
    axes[-1].set_xlim(0, 1)
    axes[-1].set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    axes[-1].set_xticklabels(["0", "0.25", "0.50", "0.75", "1.00"])
    fig.suptitle("Wake minute points by normalized wake-phase fraction", y=1.02)
    fig.tight_layout()
    return fig


def plot_wake_stress_quarter_distributions(points: pd.DataFrame, *, bins: int = 25) -> plt.Figure:
    stress = points[
        points["signal"].eq("Stress")
        & points["wake_phase_fraction"].between(0, 1)
        & points["value"].between(0, 100)
    ].copy()
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)
    axes = axes.ravel()
    labels = ["Q1", "Q2", "Q3", "Q4"]
    stress["wake_quarter"] = pd.cut(
        stress["wake_phase_fraction"],
        bins=[0, 0.25, 0.50, 0.75, 1.000001],
        labels=labels,
        include_lowest=True,
        right=False,
    )
    bin_edges = np.linspace(0, 100, bins + 1)

    for ax, label in zip(axes, labels):
        subset = stress[stress["wake_quarter"].eq(label)]
        if subset.empty:
            ax.text(0.5, 0.5, f"No {label} stress points", ha="center", va="center", transform=ax.transAxes)
            continue
        ax.hist(
            subset["value"],
            bins=bin_edges,
            density=True,
            color="#d62728",
            alpha=0.45,
            edgecolor="#7f1d1d",
            linewidth=0.7,
        )
        ax.axvline(subset["value"].median(), color="#111111", linewidth=1.8, label="median")
        ax.set_title(f"{label} stress distribution")
        ax.grid(alpha=0.22)
        ax.text(
            0.97,
            0.92,
            f"n={len(subset):,}",
            ha="right",
            va="top",
            transform=ax.transAxes,
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75},
        )
        ax.legend(loc="upper left")

    for ax in axes[::2]:
        ax.set_ylabel("Density")
    for ax in axes[2:]:
        ax.set_xlabel("Numeric stress")
    fig.suptitle("Numeric wake-stress distribution by normalized wake quarter", y=1.02)
    fig.tight_layout()
    return fig


def plot_pre_sleep_window(data: MonitoringEdaData) -> plt.Figure:
    frame = eligible_core_frame(data)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    plot_specs = [
        ("pre_sleep_4h_hr_mean", "Pre-sleep HR mean", "#1f77b4"),
        ("pre_sleep_4h_stress_mean", "Pre-sleep stress mean", "#d62728"),
    ]
    for ax, (column, title, color) in zip(axes, plot_specs):
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        ax.hist(values, bins=24, color=color, alpha=0.75)
        ax.axvline(values.median(), color="#111111", linestyle=":", linewidth=1.4, label="median")
        ax.set_title(title)
        ax.set_ylabel("Eligible days")
        ax.legend(loc="best")
        ax.grid(alpha=0.25)
    fig.suptitle("Pre-sleep four-hour window features", y=1.02)
    fig.tight_layout()
    return fig


def markdown_table(frame: pd.DataFrame, columns: list[str] | None = None, rows: int | None = None) -> str:
    table = frame.copy()
    if columns is not None:
        table = table.loc[:, columns]
    if rows is not None:
        table = table.head(rows)
    if table.empty:
        return "_No rows._"
    formatted = table.copy()
    for col in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[col]):
            formatted[col] = formatted[col].map(lambda value: "" if pd.isna(value) else f"{value:.3f}")
        else:
            formatted[col] = formatted[col].map(lambda value: "" if pd.isna(value) else str(value))
    header = "| " + " | ".join(formatted.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(formatted.columns)) + " |"
    body = ["| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |" for row in formatted.to_numpy()]
    return "\n".join([header, sep, *body])


def write_monitoring_eda_summary(
    data: MonitoringEdaData,
    *,
    selected_date: str | None = DEFAULT_SELECTED_DATE,
    output_path: Path | None = None,
) -> Path:
    output_path = data.root / "reports" / "monitoring_eda_summary.md" if output_path is None else Path(output_path)
    selected = choose_analysis_window(data.quality, selected_date)
    inventory = monitoring_inventory(data)
    funnel = quality_funnel(data)
    monthly = monthly_quality_summary(data)
    coverage = coverage_summary(data)
    stress_summary = stress_state_summary(data)
    hr_summary = hr_zone_summary(data)
    wake_shape = wake_quarter_shape(data)
    sleep_shape = sleep_quarter_shape(data)
    wake_time_points = wake_local_time_points(data)
    wake_time_overview = (
        wake_time_points.groupby("signal", as_index=False)
        .agg(
            points=("value", "count"),
            windows=("analysis_window_id", "nunique"),
            median_value=("value", "median"),
        )
        .sort_values("signal")
    )
    gallery = select_representative_day_gallery(data)
    pre_sleep = pre_sleep_summary(data)
    feature_shapes, family_counts = feature_table_overview(data)

    report = "\n\n".join(
        [
            "# Monitoring EDA Summary",
            (
                "Stage 4 adds minute-level heart-rate and stress monitoring to the aggregate JSON case study. "
                "This report summarizes the current public EDA layer: inventory, quality, semantic-day inspection, "
                "status-aware stress states, HR zones, within-window shape, representative day traces, and pre-sleep features."
            ),
            "## What Minute-Level FIT Adds",
            "\n".join(
                [
                    "- Intra-day HR/stress dynamics instead of daily summaries only.",
                    "- Sleep-aware windows rather than midnight-to-midnight grouping.",
                    "- Direct coverage, boundary, and gap diagnostics before modeling.",
                    "- Stress status semantics that separate numeric stress, unmeasurable values, and HR-confirmed active proxy minutes.",
                    "- Wake-quarter, sleep-quarter, and pre-sleep windows that define candidate predictors for the next modeling pass.",
                ]
            ),
            "## Current Monitoring Inventory",
            markdown_table(inventory, ["table", "rows", "columns", "date_range"]),
            "## Quality Funnel",
            markdown_table(funnel, ["step", "rows", "share_of_analysis_rows"]),
            "## Quality Over Time",
            (
                "Quality is uneven over calendar time, which is why downstream modeling keeps a future holdout while using "
                "past-random train/validation splits for the earlier history. "
                "Recent months include usable observed windows as well as a small number of synthetic or unsupported boundary cases."
            ),
            markdown_table(monthly.tail(8), ["month", "analysis_rows", "eligible_rows", "synthetic_split", "unsupported_multi_day_gap", "eligible_rate"]),
            "## Coverage Diagnostics",
            markdown_table(coverage, ["phase", "signal", "metric", "count", "median", "p10", "p90"]),
            "## Monitoring Day Browser",
            (
                f"The selected browser window is `{selected['analysis_window_id']}` on "
                f"`{selected['calendarDate'].date().isoformat()}`. It exposes the sleep start, wake start, and wake end boundaries, "
                "the HR trace, valid numeric stress points, and status-value intervals that daily aggregate JSON cannot show."
            ),
            "A compact representative-day gallery also keeps several regimes visible without editing notebook constants:",
            markdown_table(
                gallery,
                [
                    "gallery_label",
                    "calendarDate",
                    "analysis_window_id",
                    "boundary_confidence",
                    "modeling_recovery_v0_eligible",
                    "coverage_score",
                    "largest_gap_minutes",
                ],
            ),
            "## Stress States And HR Zones",
            "Wake stress-state composition among recovery-eligible windows:",
            markdown_table(stress_summary, ["state", "mean_fraction", "median_fraction", "p25", "p75"]),
            "Wake HR-zone composition among recovery-eligible windows:",
            markdown_table(hr_summary, ["zone", "mean_fraction", "median_fraction"]),
            "## Within-Window Shape",
            (
                "Wake quarters summarize daytime shape among recovery-eligible rows. Sleep quarters use plausible rows with usable "
                "sleep HR and stress, and remain descriptive EDA features rather than sleep-stage detection."
            ),
            "Wake quarters:",
            markdown_table(wake_shape, ["quarter", "signal", "rows", "mean_value", "median_value", "p25", "p75"]),
            "Sleep quarters:",
            markdown_table(sleep_shape, ["quarter", "signal", "rows", "mean_value", "median_value", "p25", "p75"]),
            "Wake local-time point distribution:",
            (
                "The local-time profile uses all recovery-eligible wake minute points and anchors after-midnight values as 24+ "
                "so the late-wake period remains visually continuous."
            ),
            markdown_table(wake_time_overview, ["signal", "points", "windows", "median_value"]),
            "Wake phase-fraction point distribution:",
            (
                "The normalized wake-phase profile uses the same recovery-eligible minute points, but maps each wake window to "
                "`0..1`. This separates a relative late-wake effect from a strict local-clock-time effect."
            ),
            "Wake stress distribution by normalized quarter:",
            (
                "Density-normalized stress histograms split the same wake points into four normalized wake quarters, "
                "which makes changes in distribution shape visible beyond the median line."
            ),
            "## Pre-Sleep Window",
            markdown_table(pre_sleep, ["metric", "value"]),
            "## Feature Readiness For Modeling",
            markdown_table(feature_shapes, ["feature_table", "rows", "columns"]),
            "Full feature catalog family counts:",
            markdown_table(family_counts, ["family", "columns"]),
            "## Interpretation",
            "\n".join(
                [
                    "- The monitoring layer is useful because it makes within-day physiology and missingness visible, not because it proves a prediction claim.",
                    "- Quality filtering removes a meaningful number of windows before modeling, especially when wake boundaries or whole-wake coverage are weak.",
                    "- Active/status proxy stress minutes are analytically different from numeric high-stress minutes and are kept separate.",
                    "- Wake-quarter, sleep-quarter, gallery day-browser, and pre-sleep features provide the most direct EDA bridge into future sleep-outcome modeling.",
                    "- The layer remains single-subject observational wearable data and should be interpreted as a quality-aware baseline.",
                ]
            ),
            "## Figure References",
            "\n".join(
                [
                    "- `docs/img/monitoring_example_day.png`",
                    "- `docs/img/monitoring_day_gallery.png`",
                    "- `docs/img/monitoring_within_day_shape.png`",
                    "- `docs/img/monitoring_wake_local_time_distribution.png`",
                    "- `docs/img/monitoring_wake_phase_fraction_distribution.png`",
                    "- `docs/img/monitoring_wake_stress_quarter_distribution.png`",
                ]
            ),
            "## Links",
            "\n".join(
                [
                    "- [Notebook 07: monitoring FIT EDA](../notebooks/07_monitoring_fit_eda.ipynb)",
                    "- [Stage 4 monitoring docs](../docs/stage4_monitoring.md)",
                ]
            ),
        ]
    )
    output_path.write_text(report + "\n", encoding="utf-8")
    return output_path


def write_public_figures(
    data: MonitoringEdaData,
    *,
    selected_date: str | None = DEFAULT_SELECTED_DATE,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    output_dir = data.root / "docs" / "img" if output_dir is None else Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    selected = choose_analysis_window(data.quality, selected_date)
    browser = prepare_day_browser_data(data, selected)
    gallery = select_representative_day_gallery(data)
    wake_shape = wake_quarter_shape(data)
    sleep_shape = sleep_quarter_shape(data)
    wake_time_points = wake_local_time_points(data)
    figures = {
        "monitoring_quality_funnel": plot_quality_funnel(quality_funnel(data)),
        "monitoring_quality_over_time": plot_quality_over_time(monthly_quality_summary(data)),
        "monitoring_coverage_distributions": plot_coverage_distributions(coverage_long(data)),
        "monitoring_example_day": plot_day_browser(browser),
        "monitoring_day_gallery": plot_day_gallery(data, gallery),
        "monitoring_stress_state_composition": plot_stress_state_composition(stress_state_summary(data)),
        "monitoring_within_day_shape": plot_wake_sleep_quarter_shape(wake_shape, sleep_shape),
        "monitoring_wake_local_time_distribution": plot_wake_local_time_distributions(wake_time_points),
        "monitoring_wake_phase_fraction_distribution": plot_wake_phase_fraction_distributions(wake_time_points),
        "monitoring_wake_stress_quarter_distribution": plot_wake_stress_quarter_distributions(wake_time_points),
    }
    paths: dict[str, Path] = {}
    for name, figure in figures.items():
        path = output_dir / f"{name}.png"
        figure.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(figure)
        paths[name] = path
    return paths


def write_public_outputs(
    data: MonitoringEdaData,
    *,
    selected_date: str | None = DEFAULT_SELECTED_DATE,
    write_figures: bool = True,
) -> dict[str, Path]:
    paths = {"report": write_monitoring_eda_summary(data, selected_date=selected_date)}
    if write_figures:
        paths.update(write_public_figures(data, selected_date=selected_date))
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate the public Stage 4 monitoring EDA report and figures.")
    parser.add_argument("--root", type=Path, default=None, help="Repository root. Defaults to auto-detection.")
    parser.add_argument("--selected-date", default=DEFAULT_SELECTED_DATE, help="Semantic-day date for the example day browser.")
    parser.add_argument("--no-figures", action="store_true", help="Regenerate the report only.")
    args = parser.parse_args(argv)

    data = load_stage4_monitoring_data(args.root)
    paths = write_public_outputs(data, selected_date=args.selected_date, write_figures=not args.no_figures)
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
