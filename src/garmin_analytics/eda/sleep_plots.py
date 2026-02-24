from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from .plots_common import maybe_savefig, rolling_mean


@dataclass(frozen=True)
class SleepScoreBucket:
    name: str
    color: str


SCORE_BUCKETS: tuple[SleepScoreBucket, ...] = (
    SleepScoreBucket("poor", "#d62728"),
    SleepScoreBucket("fair", "#ff7f0e"),
    SleepScoreBucket("good", "#2ca02c"),
    SleepScoreBucket("excellent", "#1f77b4"),
    SleepScoreBucket("unknown", "#7f7f7f"),
)

RAW_LINE_ALPHA = 0.25
RAW_LINE_WIDTH = 0.8
ROLL_LINE_ALPHA = 0.95
ROLL_LINE_WIDTH = 2.0


def _normalize_dates(frame: pd.DataFrame, date_col: str = "calendarDate") -> pd.DataFrame:
    out = frame.copy()
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce").dt.normalize()
    return out.dropna(subset=[date_col]).sort_values(date_col)


def _reindexed_series(frame: pd.DataFrame, y_col: str, date_col: str = "calendarDate") -> pd.Series:
    if date_col not in frame.columns or y_col not in frame.columns:
        return pd.Series(dtype=float)

    tmp = _normalize_dates(frame[[date_col, y_col]], date_col=date_col)
    tmp[y_col] = pd.to_numeric(tmp[y_col], errors="coerce")
    if tmp.empty:
        return pd.Series(dtype=float)

    idx = pd.date_range(tmp[date_col].min(), tmp[date_col].max(), freq="D")
    return tmp.set_index(date_col)[y_col].astype(float).reindex(idx)


def _plot_with_rolling(
    ax,
    frame: pd.DataFrame,
    y_col: str,
    label: str,
    rolling_days: int = 7,
    date_col: str = "calendarDate",
) -> pd.Series:
    series = _reindexed_series(frame, y_col=y_col, date_col=date_col)
    if series.empty:
        return series

    ax.plot(series.index, series.values, label=f"{label} (raw)", lw=RAW_LINE_WIDTH, alpha=RAW_LINE_ALPHA)
    ax.plot(series.index, rolling_mean(series, window=rolling_days).values, label=f"{label} ({rolling_days}d)", lw=ROLL_LINE_WIDTH, alpha=ROLL_LINE_ALPHA)
    return series


def _bucket_name(score: float | None) -> str:
    if pd.isna(score):
        return "unknown"
    # Garmin sleep quality labels (official ranges):
    # Excellent 90-100, Good 80-89, Fair 60-79, Poor < 60.
    if score < 60:
        return "poor"
    if score < 80:
        return "fair"
    if score < 90:
        return "good"
    return "excellent"


def _infer_epoch_unit(numeric: pd.Series) -> str:
    med = float(numeric.dropna().abs().median())
    if med >= 1e14:
        return "ns"
    if med >= 1e11:
        return "ms"
    return "s"


def _parse_sleep_timestamp(series: pd.Series, local_tz) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    numeric_ratio = float(numeric.notna().mean()) if len(series) else 0.0

    if numeric_ratio >= 0.8 and numeric.notna().any():
        unit = _infer_epoch_unit(numeric)
        # Unix epoch timestamps are UTC by definition; shift to local once.
        return pd.to_datetime(numeric, unit=unit, errors="coerce", utc=True).dt.tz_convert(local_tz).dt.tz_localize(None)

    # For textual timestamps, treat values as already-local wall time (naive).
    return pd.to_datetime(series, errors="coerce")


def _parse_sleep_timestamp_utc_naive(series: pd.Series) -> pd.Series:
    """Parse Garmin sleep timestamp fields (usually GMT) into UTC naive datetimes."""
    numeric = pd.to_numeric(series, errors="coerce")
    numeric_ratio = float(numeric.notna().mean()) if len(series) else 0.0
    if numeric_ratio >= 0.8 and numeric.notna().any():
        unit = _infer_epoch_unit(numeric)
        return pd.to_datetime(numeric, unit=unit, errors="coerce", utc=True).dt.tz_localize(None)

    # If textual timestamps are supplied, treat them as UTC for GMT-named columns.
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    if isinstance(parsed, pd.Series):
        return parsed.dt.tz_localize(None)
    return pd.Series(dtype="datetime64[ns]")


def _garmin_local_offset_from_wellness(frame: pd.DataFrame) -> pd.Series:
    """Derive per-row local offset from Garmin wellnessStart/End local-vs-gmt fields."""
    pairs = [
        ("wellnessStartTimeGmt", "wellnessStartTimeLocal"),
        ("wellnessEndTimeGmt", "wellnessEndTimeLocal"),
    ]
    offsets: list[pd.Series] = []

    for gmt_col, local_col in pairs:
        if gmt_col not in frame.columns or local_col not in frame.columns:
            continue
        gmt_ts = pd.to_datetime(frame[gmt_col], errors="coerce")
        local_ts = pd.to_datetime(frame[local_col], errors="coerce")
        offsets.append(local_ts - gmt_ts)

    if not offsets:
        return pd.Series(pd.NaT, index=frame.index, dtype="timedelta64[ns]")

    out = offsets[0]
    for extra in offsets[1:]:
        out = out.fillna(extra)

    # Sanity guard: ignore implausible offsets.
    bad = out.abs() > pd.Timedelta(hours=18)
    out = out.mask(bad)
    return out


def _shifted_hour(series: pd.Series, anchor_hour: int = 16) -> pd.Series:
    hour = series.dt.hour + series.dt.minute / 60.0 + series.dt.second / 3600.0
    shifted = hour.copy()
    shifted[shifted < anchor_hour] = shifted[shifted < anchor_hour] + 24.0
    return shifted


def _finalize_figure(fig, *, save_figs: bool, fig_dir: Path | str | None, fig_name: str) -> None:
    fig.tight_layout()
    maybe_savefig(fig, fig_name, save_figs=save_figs, fig_dir=fig_dir)
    plt.show()
    plt.close(fig)


def plot_sleep_intervals(
    df_sleep: pd.DataFrame,
    *,
    anchor_hour: int = 16,
    score_col: str = "sleepOverallScore",
    stick_lw: float = 1.2,
    marker_size: float = 10.0,
    save_figs: bool = False,
    fig_dir: Path | str | None = None,
    fig_name: str = "sleep_intervals_sticks",
):
    required = ["calendarDate", "sleepStartTimestampGMT", "sleepEndTimestampGMT"]
    if not all(col in df_sleep.columns for col in required):
        print("Skip: missing sleep interval columns")
        return None

    optional_cols = [c for c in ["wellnessStartTimeGmt", "wellnessStartTimeLocal", "wellnessEndTimeGmt", "wellnessEndTimeLocal"] if c in df_sleep.columns]
    frame = df_sleep[[*required, *optional_cols, *([score_col] if score_col in df_sleep.columns else [])]].copy()
    local_tz = datetime.now().astimezone().tzinfo
    frame["calendarDate"] = pd.to_datetime(frame["calendarDate"], errors="coerce").dt.normalize()
    # Parse GMT timestamps and convert to local wall time using Garmin-provided per-day local offset if available.
    start_utc = _parse_sleep_timestamp_utc_naive(frame["sleepStartTimestampGMT"])
    end_utc = _parse_sleep_timestamp_utc_naive(frame["sleepEndTimestampGMT"])
    local_offset = _garmin_local_offset_from_wellness(frame)

    if local_offset.notna().any():
        frame["sleepStartTimestampGMT"] = start_utc + local_offset
        frame["sleepEndTimestampGMT"] = end_utc + local_offset
        missing_offset = local_offset.isna()
        if bool(missing_offset.any()):
            # Fallback row-wise to machine local conversion where Garmin local offset is unavailable.
            frame.loc[missing_offset, "sleepStartTimestampGMT"] = _parse_sleep_timestamp(
                frame.loc[missing_offset, "sleepStartTimestampGMT"],
                local_tz=local_tz,
            ).values
            frame.loc[missing_offset, "sleepEndTimestampGMT"] = _parse_sleep_timestamp(
                frame.loc[missing_offset, "sleepEndTimestampGMT"],
                local_tz=local_tz,
            ).values
    else:
        frame["sleepStartTimestampGMT"] = _parse_sleep_timestamp(frame["sleepStartTimestampGMT"], local_tz=local_tz)
        frame["sleepEndTimestampGMT"] = _parse_sleep_timestamp(frame["sleepEndTimestampGMT"], local_tz=local_tz)
    frame = frame.dropna(subset=["calendarDate", "sleepStartTimestampGMT", "sleepEndTimestampGMT"]).sort_values("calendarDate")

    if frame.empty:
        print("Skip: no plottable data for sleep intervals")
        return None

    frame["start_h"] = _shifted_hour(frame["sleepStartTimestampGMT"], anchor_hour=anchor_hour)
    frame["end_h"] = _shifted_hour(frame["sleepEndTimestampGMT"], anchor_hour=anchor_hour)
    crossing = frame["end_h"] < frame["start_h"]
    frame.loc[crossing, "end_h"] = frame.loc[crossing, "end_h"] + 24.0
    frame["score_bucket"] = frame[score_col].apply(_bucket_name) if score_col in frame.columns else "unknown"

    fig, ax = plt.subplots(figsize=(12, 5))

    for bucket in SCORE_BUCKETS:
        part = frame[frame["score_bucket"] == bucket.name]
        if part.empty:
            continue
        ax.vlines(part["calendarDate"], part["start_h"], part["end_h"], color=bucket.color, lw=stick_lw, alpha=0.9)
        ax.scatter(part["calendarDate"], part["start_h"], color=bucket.color, s=marker_size, alpha=0.95)
        ax.scatter(part["calendarDate"], part["end_h"], color=bucket.color, s=marker_size, alpha=0.95)

    y_min = min(float(frame["start_h"].min()) - 0.25, float(anchor_hour) - 0.5)
    y_max = max(float(frame["end_h"].max()) + 0.25, float(anchor_hour) + 24.0)
    ax.set_ylim(y_min, y_max)
    yticks = np.arange(anchor_hour, anchor_hour + 24 + 0.1, 2)
    ylabels = [f"{int(t % 24):02d}:00" for t in yticks]
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    ax.set_title(f"Sleep intervals over time ({anchor_hour}→{anchor_hour} local day)")
    ax.set_xlabel("calendarDate")
    ax.set_ylabel("local time-of-day")
    ax.grid(axis="y", alpha=0.2)

    handles = [Line2D([0], [0], color=bucket.color, lw=3, label=bucket.name) for bucket in SCORE_BUCKETS]
    ax.legend(handles=handles, title="sleepOverallScore", loc="best")
    _finalize_figure(fig, save_figs=save_figs, fig_dir=fig_dir, fig_name=fig_name)
    return None


def plot_sleep_duration(
    df_sleep: pd.DataFrame,
    *,
    save_figs: bool = False,
    fig_dir: Path | str | None = None,
    fig_name: str = "sleep_total_hours",
):
    col = "sleep_total_hours" if "sleep_total_hours" in df_sleep.columns else None
    if col is None and "sleep_total_seconds" in df_sleep.columns:
        frame = df_sleep[["calendarDate", "sleep_total_seconds"]].copy()
        frame["sleep_total_hours"] = pd.to_numeric(frame["sleep_total_seconds"], errors="coerce") / 3600.0
        col = "sleep_total_hours"
    elif col is not None:
        frame = df_sleep[["calendarDate", col]].copy()
    else:
        print("Skip: missing sleep_total_seconds/sleep_total_hours")
        return None

    fig, ax = plt.subplots(figsize=(12, 4))
    series = _plot_with_rolling(ax, frame, y_col=col, label="sleep_total_hours", rolling_days=7)
    if series.empty:
        print("Skip: no plottable data for sleep duration")
        plt.close(fig)
        return None
    ax.set_title("Sleep duration over time (df_sleep)")
    ax.set_xlabel("calendarDate")
    ax.set_ylabel("hours")
    ax.legend()
    _finalize_figure(fig, save_figs=save_figs, fig_dir=fig_dir, fig_name=fig_name)
    return None


def plot_sleep_duration_scored(
    df_sleep: pd.DataFrame,
    *,
    score_col: str = "sleepOverallScore",
    rolling_days: int = 7,
    cmap: str = "viridis",
    save_figs: bool = False,
    fig_dir: Path | str | None = None,
    fig_name: str = "sleep_total_hours_scored",
):
    col = "sleep_total_hours" if "sleep_total_hours" in df_sleep.columns else None
    if col is None and "sleep_total_seconds" in df_sleep.columns:
        frame = df_sleep[["calendarDate", "sleep_total_seconds"]].copy()
        frame["sleep_total_hours"] = pd.to_numeric(frame["sleep_total_seconds"], errors="coerce") / 3600.0
        col = "sleep_total_hours"
    elif col is not None:
        keep = ["calendarDate", col]
        if score_col in df_sleep.columns:
            keep.append(score_col)
        frame = df_sleep[keep].copy()
    else:
        print("Skip: missing sleep_total_seconds/sleep_total_hours")
        return None

    frame["calendarDate"] = pd.to_datetime(frame["calendarDate"], errors="coerce").dt.normalize()
    frame[col] = pd.to_numeric(frame[col], errors="coerce")
    if score_col in frame.columns:
        frame[score_col] = pd.to_numeric(frame[score_col], errors="coerce")
    frame = frame.dropna(subset=["calendarDate", col]).sort_values("calendarDate")
    if frame.empty:
        print("Skip: no plottable data for sleep duration scored")
        return None

    fig, ax = plt.subplots(figsize=(12, 4))
    series = _reindexed_series(frame, y_col=col)
    if series.empty:
        print("Skip: no plottable data for sleep duration scored")
        plt.close(fig)
        return None

    # Light stems from rolling baseline to point improve temporal readability.
    ax.vlines(
        frame["calendarDate"],
        ymin=np.nanmin(series.values),
        ymax=frame[col].values,
        color="#cccccc",
        lw=0.6,
        alpha=0.5,
        zorder=1,
    )
    if score_col in frame.columns and frame[score_col].notna().any():
        sc = ax.scatter(
            frame["calendarDate"],
            frame[col],
            c=frame[score_col],
            cmap=cmap,
            s=18,
            alpha=0.9,
            edgecolors="none",
            zorder=3,
        )
        cbar = fig.colorbar(sc, ax=ax, pad=0.01)
        cbar.set_label(score_col)
    else:
        ax.scatter(frame["calendarDate"], frame[col], color="#1f77b4", s=18, alpha=0.8, zorder=3)

    ax.plot(
        series.index,
        rolling_mean(series, window=rolling_days).values,
        color="#111111",
        lw=ROLL_LINE_WIDTH,
        alpha=ROLL_LINE_ALPHA,
        label=f"sleep_total_hours ({rolling_days}d)",
    )
    ax.set_title(f"Sleep duration over time, colored by {score_col}" if score_col in frame.columns else "Sleep duration over time")
    ax.set_xlabel("calendarDate")
    ax.set_ylabel("hours")
    ax.legend(loc="best")
    _finalize_figure(fig, save_figs=save_figs, fig_dir=fig_dir, fig_name=fig_name)
    return None


def plot_sleep_stage_fractions(
    df_sleep: pd.DataFrame,
    *,
    save_figs: bool = False,
    fig_dir: Path | str | None = None,
    fig_name: str = "sleep_stage_fractions",
):
    stage_sec_map = {
        "deepSleepSeconds": "deep_pct",
        "lightSleepSeconds": "light_pct",
        "remSleepSeconds": "rem_pct",
        "awakeSleepSeconds": "awake_pct",
    }
    sec_cols = [c for c in stage_sec_map if c in df_sleep.columns]
    if len(sec_cols) < 2:
        print("Skip: missing sleep stage second columns")
        return None

    frame = _normalize_dates(df_sleep[["calendarDate", *sec_cols]].copy())
    for col in sec_cols:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")

    if "unmeasurableSeconds" in df_sleep.columns:
        frame["unmeasurableSeconds"] = pd.to_numeric(df_sleep["unmeasurableSeconds"], errors="coerce").reindex(frame.index)
        sec_cols = [*sec_cols, "unmeasurableSeconds"]

    total_sleep = frame[sec_cols].sum(axis=1, min_count=1)
    valid = total_sleep > 0
    frame = frame.loc[valid].copy()
    total_sleep = total_sleep.loc[valid]

    pct_cols: list[str] = []
    for sec_col in sec_cols:
        out_col = stage_sec_map.get(sec_col, "unmeasurable_pct")
        frame[out_col] = frame[sec_col] / total_sleep
        pct_cols.append(out_col)

    frame = frame.dropna(subset=pct_cols, how="all")
    if frame.empty:
        print("Skip: no plottable sleep stage fraction data")
        return None

    y = [pd.to_numeric(frame[c], errors="coerce").to_numpy() for c in pct_cols]
    fig, ax = plt.subplots(figsize=(12, 4))
    bottom = np.zeros(len(frame), dtype=float)
    for col, vals in zip(pct_cols, y):
        vals_safe = np.nan_to_num(vals, nan=0.0)
        ax.bar(frame["calendarDate"], vals_safe, bottom=bottom, width=1.0, label=col, alpha=0.9)
        bottom = bottom + vals_safe
    ax.set_ylim(0, 1)
    ax.set_title("Sleep stage fractions over time (df_sleep)")
    ax.set_xlabel("calendarDate")
    ax.set_ylabel("share of sleep")
    ax.legend(loc="best")
    _finalize_figure(fig, save_figs=save_figs, fig_dir=fig_dir, fig_name=fig_name)
    return None


def plot_sleep_stage_hours(
    df_sleep: pd.DataFrame,
    *,
    save_figs: bool = False,
    fig_dir: Path | str | None = None,
    fig_name: str = "sleep_stage_hours",
):
    sec_cols = [
        c
        for c in ["deepSleepSeconds", "lightSleepSeconds", "remSleepSeconds", "awakeSleepSeconds", "unmeasurableSeconds"]
        if c in df_sleep.columns
    ]
    if len(sec_cols) < 2:
        print("Skip: missing sleep stage second columns")
        return None

    frame = _normalize_dates(df_sleep[["calendarDate", *sec_cols]].copy())
    hour_cols: list[str] = []
    for col in sec_cols:
        hour_col = col.replace("Seconds", "Hours")
        frame[hour_col] = pd.to_numeric(frame[col], errors="coerce") / 3600.0
        hour_cols.append(hour_col)

    frame = frame.dropna(subset=hour_cols, how="all")
    if frame.empty:
        print("Skip: no plottable sleep stage hour data")
        return None

    y = [pd.to_numeric(frame[c], errors="coerce").to_numpy() for c in hour_cols]
    fig, ax = plt.subplots(figsize=(12, 4))
    bottom = np.zeros(len(frame), dtype=float)
    for col, vals in zip(hour_cols, y):
        vals_safe = np.nan_to_num(vals, nan=0.0)
        ax.bar(frame["calendarDate"], vals_safe, bottom=bottom, width=1.0, label=col, alpha=0.9)
        bottom = bottom + vals_safe
    ax.set_title("Sleep stage absolute hours over time (df_sleep)")
    ax.set_xlabel("calendarDate")
    ax.set_ylabel("hours")
    ax.legend(loc="best")
    _finalize_figure(fig, save_figs=save_figs, fig_dir=fig_dir, fig_name=fig_name)
    return None


def plot_sleep_scores(
    df_sleep: pd.DataFrame,
    *,
    rolling_days: int = 7,
    save_figs: bool = False,
    fig_dir: Path | str | None = None,
    fig_name: str = "sleep_scores",
):
    groups = [
        ["sleepOverallScore", "sleepQualityScore"],
        ["sleepDurationScore", "sleepRecoveryScore"],
    ]
    group_names = ["overall_quality", "duration_recovery"]

    available_groups = [[c for c in grp if c in df_sleep.columns] for grp in groups]
    if all(len(grp) == 0 for grp in available_groups):
        print("Skip: missing sleep score columns")
        return None

    made_plot = False
    for suffix, cols in zip(group_names, available_groups):
        if not cols:
            continue

        fig, ax = plt.subplots(figsize=(12, 4))
        plotted = False
        for col in cols:
            series = _plot_with_rolling(ax, df_sleep, y_col=col, label=col, rolling_days=rolling_days)
            plotted = plotted or (not series.empty)

        if not plotted:
            plt.close(fig)
            continue

        made_plot = True
        ax.set_title(f"Sleep scores over time ({suffix})")
        ax.set_xlabel("calendarDate")
        ax.set_ylabel("score")
        ax.legend(loc="best", ncol=2)
        _finalize_figure(
            fig,
            save_figs=save_figs,
            fig_dir=fig_dir,
            fig_name=f"{fig_name}_{suffix}",
        )

    if not made_plot:
        print("Skip: no plottable sleep scores")
    return None


def plot_sleep_respiration(
    df_sleep: pd.DataFrame,
    *,
    rolling_days: int = 7,
    save_figs: bool = False,
    fig_dir: Path | str | None = None,
    fig_name: str = "sleep_respiration",
):
    label_map = {
        "lowestRespiration": "lowest",
        "averageRespiration": "average",
        "highestRespiration": "highest",
    }
    cols = [c for c in ["lowestRespiration", "averageRespiration", "highestRespiration"] if c in df_sleep.columns]
    if len(cols) < 2:
        print("Skip: missing sleep respiration columns")
        return None

    fig, ax = plt.subplots(figsize=(12, 4))
    plotted = False
    for col in cols:
        series = _reindexed_series(df_sleep, y_col=col)
        if series.empty:
            continue
        plotted = True
        ax.plot(series.index, series.values, label=f"{label_map[col]} (raw)", lw=RAW_LINE_WIDTH, alpha=RAW_LINE_ALPHA)
        ax.plot(
            series.index,
            rolling_mean(series, window=rolling_days).values,
            label=f"{label_map[col]} ({rolling_days}d)",
            lw=ROLL_LINE_WIDTH,
            alpha=ROLL_LINE_ALPHA,
        )

    if not plotted:
        print("Skip: no plottable sleep respiration")
        plt.close(fig)
        return None

    ax.set_title("Sleep respiration over time (df_sleep)")
    ax.set_xlabel("calendarDate")
    ax.set_ylabel("brpm")
    ax.legend(loc="best", ncol=2)
    _finalize_figure(fig, save_figs=save_figs, fig_dir=fig_dir, fig_name=fig_name)
    return None


def plot_sleep_spo2(
    df_sleep: pd.DataFrame,
    *,
    rolling_days: int = 7,
    save_figs: bool = False,
    fig_dir: Path | str | None = None,
    fig_name: str = "sleep_spo2",
):
    # Garmin exports may expose both legacy and sleep-summary naming variants.
    # Prefer one coherent pair to avoid plotting duplicated signals twice.
    preferred_pairs = [
        [("averageSpo2Value", "avgSpO2"), ("lowestSpo2Value", "lowestSpO2")],
        [("spo2SleepAverageSPO2", "sleepAvgSpO2"), ("spo2SleepLowestSPO2", "sleepLowestSpO2")],
    ]
    cols: list[tuple[str, str]] = []
    for pair in preferred_pairs:
        if all(col in df_sleep.columns for col, _ in pair):
            cols = pair
            break
    if not cols:
        # Fallback: use any available pair-like columns (still keep order stable)
        fallback = [
            ("averageSpo2Value", "avgSpO2"),
            ("lowestSpo2Value", "lowestSpO2"),
            ("spo2SleepAverageSPO2", "sleepAvgSpO2"),
            ("spo2SleepLowestSPO2", "sleepLowestSpO2"),
        ]
        cols = [(c, label) for c, label in fallback if c in df_sleep.columns]
    if len(cols) < 2:
        print("Skip: missing sleep SpO2 columns")
        return None

    fig, ax = plt.subplots(figsize=(12, 4))
    plotted = False
    palette = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd"]
    for (col, label), color in zip(cols, palette):
        series = _reindexed_series(df_sleep, y_col=col)
        if series.empty:
            continue
        plotted = True
        ax.plot(series.index, series.values, label=f"{label} (raw)", lw=RAW_LINE_WIDTH, alpha=RAW_LINE_ALPHA, color=color)
        ax.plot(
            series.index,
            rolling_mean(series, window=rolling_days).values,
            label=f"{label} ({rolling_days}d)",
            lw=ROLL_LINE_WIDTH,
            alpha=ROLL_LINE_ALPHA,
            color=color,
        )

    if not plotted:
        print("Skip: no plottable sleep SpO2")
        plt.close(fig)
        return None

    ax.set_title("Sleep oxygen saturation over time (df_sleep)")
    ax.set_xlabel("calendarDate")
    ax.set_ylabel("SpO2 (%)")
    ax.legend(loc="best", ncol=2)
    _finalize_figure(fig, save_figs=save_figs, fig_dir=fig_dir, fig_name=fig_name)
    return None


def plot_sleep_stress(
    df_sleep: pd.DataFrame,
    *,
    rolling_days: int = 7,
    save_figs: bool = False,
    fig_dir: Path | str | None = None,
    fig_name: str = "avg_sleep_stress",
):
    if "avgSleepStress" not in df_sleep.columns:
        print("Skip: missing avgSleepStress")
        return None

    fig, ax = plt.subplots(figsize=(12, 4))
    series = _plot_with_rolling(ax, df_sleep, y_col="avgSleepStress", label="avgSleepStress", rolling_days=rolling_days)
    if series.empty:
        print("Skip: no plottable avgSleepStress")
        plt.close(fig)
        return None

    ax.set_title("Average sleep stress over time (df_sleep)")
    ax.set_xlabel("calendarDate")
    ax.set_ylabel("stress")
    ax.legend(loc="best")
    _finalize_figure(fig, save_figs=save_figs, fig_dir=fig_dir, fig_name=fig_name)
    return None
