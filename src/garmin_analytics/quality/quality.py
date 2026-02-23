from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class QualityConfig:
    steps_min: int = 50
    stress_any_min_seconds: int = 21600
    stress_full_min_seconds: int = 72000
    strict_min_score: int = 4
    loose_min_score: int = 3
    top_n: int = 50


QUALITY_FLAGS = [
    "has_steps",
    "has_hr",
    "has_stress_duration",
    "has_bodybattery_end",
    "has_sleep",
]


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _bool_series(df: pd.DataFrame, name: str, default: bool = False) -> pd.Series:
    if name not in df.columns:
        return pd.Series([default] * len(df), index=df.index, dtype="boolean")
    return df[name].astype("boolean")


def _label_from_score(score: pd.Series, min_score: int) -> pd.Series:
    label = pd.Series("partial", index=score.index, dtype="string")
    label = label.mask(score >= min_score, "good")
    label = label.mask(score <= 1, "bad")
    return label


def _match_with_tolerance(
    left: pd.Series,
    right: pd.Series,
    tolerance_seconds: int = 60,
) -> pd.Series:
    left_num = _numeric(left)
    right_num = _numeric(right)
    out = pd.Series(pd.NA, index=left.index, dtype="boolean")
    present = left_num.notna() & right_num.notna()
    out.loc[present] = ((left_num.loc[present] - right_num.loc[present]).abs() <= tolerance_seconds)
    return out


def apply_quality_labels(df: pd.DataFrame, config: QualityConfig) -> pd.DataFrame:
    out = df.copy()

    total_steps = _numeric(out["totalSteps"]) if "totalSteps" in out.columns else pd.Series([pd.NA] * len(out), index=out.index)
    stress_total = _numeric(out["stressTotalDurationSeconds"]) if "stressTotalDurationSeconds" in out.columns else pd.Series([pd.NA] * len(out), index=out.index)

    out["has_steps"] = ((total_steps.notna()) & (total_steps >= config.steps_min)).astype("boolean")

    hr_sources = [
        out["minHeartRate"].notna() if "minHeartRate" in out.columns else pd.Series(False, index=out.index),
        out["maxHeartRate"].notna() if "maxHeartRate" in out.columns else pd.Series(False, index=out.index),
        out["restingHeartRate"].notna() if "restingHeartRate" in out.columns else pd.Series(False, index=out.index),
    ]
    out["has_hr"] = (hr_sources[0] | hr_sources[1] | hr_sources[2]).astype("boolean")

    out["has_stress_duration"] = ((stress_total.notna()) & (stress_total >= config.stress_any_min_seconds)).astype("boolean")
    out["full_day_stress"] = ((stress_total.notna()) & (stress_total >= config.stress_full_min_seconds)).astype("boolean")

    out["has_bodybattery_start"] = (
        out["bodyBatteryStartOfDay"].notna() if "bodyBatteryStartOfDay" in out.columns else pd.Series(False, index=out.index)
    ).astype("boolean")
    out["has_bodybattery_end"] = (
        out["bodyBatteryEndOfDay"].notna() if "bodyBatteryEndOfDay" in out.columns else pd.Series(False, index=out.index)
    ).astype("boolean")
    out["has_bodybattery_any"] = (
        _bool_series(out, "has_bodybattery_start", default=False) | _bool_series(out, "has_bodybattery_end", default=False)
    ).astype("boolean")
    out["bodybattery_start_without_end"] = (
        _bool_series(out, "has_bodybattery_start", default=False)
        & (~_bool_series(out, "has_bodybattery_end", default=False))
    ).astype("boolean")

    has_sleep_start = out["sleepStartTimestampGMT"].notna() if "sleepStartTimestampGMT" in out.columns else pd.Series(False, index=out.index)
    has_sleep_end = out["sleepEndTimestampGMT"].notna() if "sleepEndTimestampGMT" in out.columns else pd.Series(False, index=out.index)
    out["has_sleep"] = (has_sleep_start & has_sleep_end).astype("boolean")

    if "allDayStress_TOTAL_totalDuration" in out.columns and "stressTotalDurationSeconds" in out.columns:
        out["stress_duration_matches_allDayStress_TOTAL"] = _match_with_tolerance(
            out["stressTotalDurationSeconds"],
            out["allDayStress_TOTAL_totalDuration"],
        )
    else:
        out["stress_duration_matches_allDayStress_TOTAL"] = pd.Series(pd.NA, index=out.index, dtype="boolean")

    if "allDayStress_AWAKE_totalDuration" in out.columns and "stressAwakeDurationSeconds" in out.columns:
        out["stress_awake_matches_allDayStress_AWAKE"] = _match_with_tolerance(
            out["stressAwakeDurationSeconds"],
            out["allDayStress_AWAKE_totalDuration"],
        )
    else:
        out["stress_awake_matches_allDayStress_AWAKE"] = pd.Series(pd.NA, index=out.index, dtype="boolean")

    score = pd.Series(0, index=out.index, dtype="int64")
    for flag in QUALITY_FLAGS:
        score = score + _bool_series(out, flag, default=False).fillna(False).astype(int)
    out["quality_score"] = score

    out["day_quality_label_strict"] = _label_from_score(score, config.strict_min_score)
    out["day_quality_label_loose"] = _label_from_score(score, config.loose_min_score)
    out["valid_day_strict"] = (score >= config.strict_min_score).astype("boolean")
    out["valid_day_loose"] = (score >= config.loose_min_score).astype("boolean")

    # Corrupted artifact day: stress defaults to ~full day while all other key signals are absent.
    corrupted = (
        stress_total.notna()
        & (stress_total >= int(23.5 * 3600))
        & (~_bool_series(out, "has_hr", default=False).fillna(False))
        & (~_bool_series(out, "has_sleep", default=False).fillna(False))
        & (~_bool_series(out, "has_bodybattery_end", default=False).fillna(False))
        & (~_bool_series(out, "has_steps", default=False).fillna(False))
    )
    out["corrupted_stress_only_day"] = corrupted.astype("boolean")

    # Force these days to bad regardless of score thresholds.
    out.loc[corrupted, "day_quality_label_strict"] = "bad"
    out.loc[corrupted, "day_quality_label_loose"] = "bad"
    out.loc[corrupted, "valid_day_strict"] = False
    out.loc[corrupted, "valid_day_loose"] = False

    missing_flags = [*QUALITY_FLAGS, "full_day_stress"]

    def _reasons(row: pd.Series) -> str:
        missing = [flag for flag in missing_flags if not bool(row.get(flag, False))]
        if bool(row.get("corrupted_stress_only_day", False)):
            missing = ["corrupted_stress_only_day", *missing]
        return ",".join(missing)

    reason_cols = [*missing_flags, "corrupted_stress_only_day"]
    out["suspicion_reasons"] = out[reason_cols].fillna(False).apply(_reasons, axis=1)
    return out


def build_suspicious_days(quality_df: pd.DataFrame, top_n: int) -> pd.DataFrame:
    out = quality_df.copy()
    stress_total = _numeric(out["stressTotalDurationSeconds"]) if "stressTotalDurationSeconds" in out.columns else pd.Series([pd.NA] * len(out), index=out.index)
    out["_sort_stress"] = stress_total.fillna(-1)
    out["_sort_missing_sleep"] = (~_bool_series(out, "has_sleep", default=False).fillna(False)).astype(int)

    cols = [
        "calendarDate",
        "quality_score",
        "day_quality_label_strict",
        "day_quality_label_loose",
        "corrupted_stress_only_day",
        "has_steps",
        "has_hr",
        "has_stress_duration",
        "has_bodybattery_start",
        "has_bodybattery_end",
        "has_bodybattery_any",
        "bodybattery_start_without_end",
        "has_sleep",
        "full_day_stress",
        "stressTotalDurationSeconds",
        "totalSteps",
        "minHeartRate",
        "maxHeartRate",
        "restingHeartRate",
        "bodyBatteryStartOfDay",
        "bodyBatteryEndOfDay",
        "suspicion_reasons",
    ]
    existing = [c for c in cols if c in out.columns]

    out = out.sort_values(
        ["quality_score", "_sort_stress", "_sort_missing_sleep"],
        ascending=[True, True, False],
    ).head(top_n)

    return out[existing].reset_index(drop=True)


def build_suspicious_days_artifacts(quality_df: pd.DataFrame, top_n: int) -> pd.DataFrame:
    """Artifact-focused suspicious export.

    Prioritizes rows that look like telemetry artifacts (e.g., high/full-day stress with
    missing corroborating signals), rather than simply the sparsest rows.
    """
    out = quality_df.copy()
    stress_total = _numeric(out["stressTotalDurationSeconds"]) if "stressTotalDurationSeconds" in out.columns else pd.Series([pd.NA] * len(out), index=out.index)
    out["_sort_stress_desc"] = stress_total.fillna(-1)

    corroborating_missing = pd.Series(0, index=out.index, dtype="int64")
    for col in ["has_hr", "has_sleep", "has_bodybattery_end", "has_steps"]:
        corroborating_missing = corroborating_missing + (~_bool_series(out, col, default=False).fillna(False)).astype(int)
    out["_sort_missing_corroborating"] = corroborating_missing

    out["_sort_corrupted"] = _bool_series(out, "corrupted_stress_only_day", default=False).fillna(False).astype(int)
    out["_sort_full_stress"] = _bool_series(out, "full_day_stress", default=False).fillna(False).astype(int)

    cols = [
        "calendarDate",
        "quality_score",
        "day_quality_label_strict",
        "day_quality_label_loose",
        "corrupted_stress_only_day",
        "has_steps",
        "has_hr",
        "has_stress_duration",
        "has_bodybattery_start",
        "has_bodybattery_end",
        "has_bodybattery_any",
        "bodybattery_start_without_end",
        "has_sleep",
        "full_day_stress",
        "stressTotalDurationSeconds",
        "totalSteps",
        "minHeartRate",
        "maxHeartRate",
        "restingHeartRate",
        "bodyBatteryStartOfDay",
        "bodyBatteryEndOfDay",
        "suspicion_reasons",
    ]
    existing = [c for c in cols if c in out.columns]

    out = out.sort_values(
        [
            "_sort_corrupted",
            "_sort_full_stress",
            "_sort_missing_corroborating",
            "_sort_stress_desc",
            "quality_score",
        ],
        ascending=[False, False, False, False, True],
    ).head(top_n)

    return out[existing].reset_index(drop=True)


def _label_table(series: pd.Series) -> pd.DataFrame:
    counts = series.value_counts(dropna=False)
    total = counts.sum()
    order = ["good", "partial", "bad"]
    rows: list[dict[str, Any]] = []
    for label in order:
        count = int(counts.get(label, 0))
        pct = (count / total * 100.0) if total else 0.0
        rows.append({"label": label, "count": count, "pct": round(pct, 2)})
    return pd.DataFrame(rows)


def _markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    def _fmt(value: Any) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    header = "| " + " | ".join(columns) + " |"
    sep = "|" + "|".join([" --- "] * len(columns)) + "|"
    lines = [header, sep]
    for _, row in df.iterrows():
        vals = [_fmt(row.get(c, "")) for c in columns]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _reason_frequency_table(quality_df: pd.DataFrame, mask: pd.Series | None = None) -> pd.DataFrame:
    if "suspicion_reasons" not in quality_df.columns:
        return pd.DataFrame(columns=["reason", "count", "pct_of_rows"])

    data = quality_df
    if mask is not None:
        data = quality_df.loc[mask.fillna(False)]

    total_rows = len(data)
    if total_rows == 0:
        return pd.DataFrame(columns=["reason", "count", "pct_of_rows"])

    counts: dict[str, int] = {}
    for raw in data["suspicion_reasons"].fillna("").astype(str):
        for reason in [token.strip() for token in raw.split(",") if token.strip()]:
            counts[reason] = counts.get(reason, 0) + 1

    rows = [
        {"reason": reason, "count": count, "pct_of_rows": round(count / total_rows * 100.0, 2)}
        for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    return pd.DataFrame(rows)


def build_quality_summary_markdown(
    quality_df: pd.DataFrame,
    *,
    input_path: Path,
    config: QualityConfig,
) -> str:
    generated = datetime.now(timezone.utc).isoformat()
    shape = f"rows={len(quality_df)}, columns={len(quality_df.columns)}"

    date_range = ""
    if "calendarDate" in quality_df.columns:
        dates = pd.to_datetime(quality_df["calendarDate"], errors="coerce")
        if dates.notna().any():
            date_range = f"{dates.min().date()} to {dates.max().date()}"

    strict_tbl = _label_table(quality_df["day_quality_label_strict"])
    loose_tbl = _label_table(quality_df["day_quality_label_loose"])

    coverage_rows = []
    for col in QUALITY_FLAGS:
        if col in quality_df.columns:
            frac = float(_bool_series(quality_df, col, default=False).fillna(False).mean())
            coverage_rows.append({"flag": col, "fraction_true": round(frac, 4), "pct_true": round(frac * 100.0, 2)})
    coverage_tbl = pd.DataFrame(coverage_rows)

    bb_patterns_tbl = pd.DataFrame(columns=["has_bodybattery_start", "has_bodybattery_end", "count", "pct"])
    if "has_bodybattery_start" in quality_df.columns and "has_bodybattery_end" in quality_df.columns:
        bb_start = _bool_series(quality_df, "has_bodybattery_start", default=False).fillna(False)
        bb_end = _bool_series(quality_df, "has_bodybattery_end", default=False).fillna(False)
        bb_patterns_tbl = (
            pd.DataFrame({"has_bodybattery_start": bb_start.astype(int), "has_bodybattery_end": bb_end.astype(int)})
            .value_counts(sort=True)
            .reset_index(name="count")
        )
        total_rows = len(quality_df)
        bb_patterns_tbl["pct"] = bb_patterns_tbl["count"].apply(
            lambda count: round((count / total_rows * 100.0) if total_rows else 0.0, 2)
        )

    start_without_end_count = 0
    start_without_end_pct = 0.0
    if "bodybattery_start_without_end" in quality_df.columns:
        bb_start_only = _bool_series(quality_df, "bodybattery_start_without_end", default=False).fillna(False)
        start_without_end_count = int(bb_start_only.sum())
        start_without_end_pct = float(bb_start_only.mean() * 100.0) if len(bb_start_only) else 0.0

    stress = _numeric(quality_df["stressTotalDurationSeconds"]) if "stressTotalDurationSeconds" in quality_df.columns else pd.Series(dtype=float)
    stress_hours = stress / 3600.0
    stress_stats = {
        "min_hours": float(stress_hours.min()) if stress_hours.notna().any() else None,
        "median_hours": float(stress_hours.median()) if stress_hours.notna().any() else None,
        "max_hours": float(stress_hours.max()) if stress_hours.notna().any() else None,
        "days_lt_1h": int((stress_hours < 1).sum()) if len(stress_hours) else 0,
        "days_lt_6h": int((stress_hours < 6).sum()) if len(stress_hours) else 0,
        "days_lt_12h": int((stress_hours < 12).sum()) if len(stress_hours) else 0,
        "days_lt_20h": int((stress_hours < 20).sum()) if len(stress_hours) else 0,
    }

    def _match_summary(col: str) -> str:
        if col not in quality_df.columns:
            return "column unavailable"
        s = quality_df[col].astype("boolean")
        valid = s.notna().sum()
        if valid == 0:
            return "no comparable rows"
        true_pct = float((s == True).sum() / valid * 100.0)
        false_pct = float((s == False).sum() / valid * 100.0)
        return f"true={true_pct:.2f}%, false={false_pct:.2f}%, compared_rows={int(valid)}"

    corrupted_count = 0
    corrupted_pct = 0.0
    corrupted_range = "n/a"
    if "corrupted_stress_only_day" in quality_df.columns:
        corrupted = _bool_series(quality_df, "corrupted_stress_only_day", default=False).fillna(False)
        corrupted_count = int(corrupted.sum())
        corrupted_pct = float(corrupted.mean() * 100.0) if len(corrupted) else 0.0
        if corrupted_count > 0 and "calendarDate" in quality_df.columns:
            corrupted_dates = pd.to_datetime(quality_df.loc[corrupted, "calendarDate"], errors="coerce")
            corrupted_dates = corrupted_dates.dropna()
            if not corrupted_dates.empty:
                corrupted_range = f"{corrupted_dates.min().date()} to {corrupted_dates.max().date()}"

    strict_bad_mask = (
        (quality_df["day_quality_label_strict"] == "bad")
        if "day_quality_label_strict" in quality_df.columns
        else pd.Series(False, index=quality_df.index, dtype="boolean")
    )
    reason_freq_all_tbl = _reason_frequency_table(quality_df)
    reason_freq_strict_bad_tbl = _reason_frequency_table(quality_df, strict_bad_mask)

    lines = [
        "# Quality Summary",
        "",
        f"Generated at (UTC): {generated}",
        f"Input file: {input_path}",
        f"Dataset shape: {shape}",
    ]
    if date_range:
        lines.append(f"Date range: {date_range}")

    lines.extend([
        "",
        "## Strict labels",
        "",
        _markdown_table(strict_tbl, ["label", "count", "pct"]),
        "",
        "## Loose labels",
        "",
        _markdown_table(loose_tbl, ["label", "count", "pct"]),
        "",
        "## Thresholds (current config)",
        "",
        f"- steps_min: {config.steps_min}",
        f"- stress_any_min_seconds: {config.stress_any_min_seconds} ({config.stress_any_min_seconds / 3600:.1f}h)",
        f"- stress_full_min_seconds: {config.stress_full_min_seconds} ({config.stress_full_min_seconds / 3600:.1f}h)",
        f"- strict_min_score: {config.strict_min_score}",
        f"- loose_min_score: {config.loose_min_score}",
        "",
        "## Coverage metrics",
        "",
        _markdown_table(coverage_tbl, ["flag", "fraction_true", "pct_true"]) if not coverage_tbl.empty else "No coverage flags available.",
        "",
        "## Body Battery coverage diagnostics",
        "",
        _markdown_table(bb_patterns_tbl, ["has_bodybattery_start", "has_bodybattery_end", "count", "pct"]) if not bb_patterns_tbl.empty else "No Body Battery diagnostics available.",
        "",
        f"- start present, end missing (`bodybattery_start_without_end`): {start_without_end_count} days ({start_without_end_pct:.2f}%)",
        "- Interpretation: start-only Body Battery usually means the watch was worn earlier in the day but powered off before end-of-day, so coverage is partial rather than a parser failure.",
        "",
        "## Stress duration summary",
        "",
        f"- min/median/max hours: {stress_stats['min_hours']:.2f}, {stress_stats['median_hours']:.2f}, {stress_stats['max_hours']:.2f}" if stress_stats["min_hours"] is not None else "- min/median/max hours: n/a",
        f"- days with stressTotalDurationSeconds < 1h: {stress_stats['days_lt_1h']}",
        f"- days with stressTotalDurationSeconds < 6h: {stress_stats['days_lt_6h']}",
        f"- days with stressTotalDurationSeconds < 12h: {stress_stats['days_lt_12h']}",
        f"- days with stressTotalDurationSeconds < 20h: {stress_stats['days_lt_20h']}",
        "",
        "## Duplicate sanity checks",
        "",
        f"- stress_duration_matches_allDayStress_TOTAL: {_match_summary('stress_duration_matches_allDayStress_TOTAL')}",
        f"- stress_awake_matches_allDayStress_AWAKE: {_match_summary('stress_awake_matches_allDayStress_AWAKE')}",
        "",
        "## Corrupted stress-only days",
        "",
        f"- count: {corrupted_count}",
        f"- percent: {corrupted_pct:.2f}%",
        f"- date range: {corrupted_range}",
        "",
        "## Suspicion reason frequencies (all rows)",
        "",
        _markdown_table(reason_freq_all_tbl, ["reason", "count", "pct_of_rows"]) if not reason_freq_all_tbl.empty else "No suspicion reasons available.",
        "",
        "## Suspicion reason frequencies (strict bad rows)",
        "",
        _markdown_table(reason_freq_strict_bad_tbl, ["reason", "count", "pct_of_rows"]) if not reason_freq_strict_bad_tbl.empty else "No strict-bad rows.",
        "",
        "## Notes",
        "",
        f"- Strict validity uses quality_score >= {config.strict_min_score}.",
        f"- Loose validity uses quality_score >= {config.loose_min_score}.",
        "- Quality labels describe day-level analysis readiness / signal coverage, not medical-grade measurement quality.",
        "- `has_bodybattery_end` is intentionally used (instead of any Body Battery presence) because end-of-day value is more useful for day-outcome analyses.",
        "- Missing sleep often indicates no night coverage for that date.",
    ])
    return "\n".join(lines) + "\n"


def write_quality_outputs(
    quality_df: pd.DataFrame,
    suspicious_df: pd.DataFrame,
    *,
    suspicious_artifacts_df: pd.DataFrame | None = None,
    out_dir: Path,
    summary_markdown: str,
    output_parquet: Path,
    write_parquet: bool,
) -> tuple[Path, Path, Path | None, Path | None]:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "quality_summary.md"
    suspicious_path = out_dir / "suspicious_days.csv"
    suspicious_artifacts_path = out_dir / "suspicious_days_artifacts.csv"

    summary_path.write_text(summary_markdown, encoding="utf-8")
    suspicious_df.to_csv(suspicious_path, index=False)
    wrote_artifacts_path: Path | None = None
    if suspicious_artifacts_df is not None:
        suspicious_artifacts_df.to_csv(suspicious_artifacts_path, index=False)
        wrote_artifacts_path = suspicious_artifacts_path

    parquet_path: Path | None = None
    if write_parquet:
        output_parquet.parent.mkdir(parents=True, exist_ok=True)
        quality_df.to_parquet(output_parquet, index=False, engine="pyarrow")
        parquet_path = output_parquet

    return summary_path, suspicious_path, parquet_path, wrote_artifacts_path
