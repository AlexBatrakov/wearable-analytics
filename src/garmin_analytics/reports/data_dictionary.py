from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ISO_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")


QUALITY_COLUMNS: set[str] = {
    "totalSteps",
    "minHeartRate",
    "maxHeartRate",
    "restingHeartRate",
    "stressTotalDurationSeconds",
    "bodyBatteryEndOfDay",
    "sleepStartTimestampGMT",
    "sleepEndTimestampGMT",
}

# Curated shortlist for decision-oriented summaries in markdown.
KEY_ANALYSIS_COLUMNS: tuple[str, ...] = (
    "totalSteps",
    "totalDistanceMeters",
    "activeKilocalories",
    "restingHeartRate",
    "minHeartRate",
    "maxHeartRate",
    "stressTotalDurationSeconds",
    "stressAwakeDurationSeconds",
    "bodyBatteryStartOfDay",
    "bodyBatteryEndOfDay",
    "sleepStartTimestampGMT",
    "sleepEndTimestampGMT",
    "deepSleepSeconds",
    "lightSleepSeconds",
    "remSleepSeconds",
    "awakeSleepSeconds",
    "averageRespiration",
    "avgSleepStress",
    "sleepOverallScore",
    "sleepQualityScore",
    "sleepDurationScore",
    "sleepRecoveryScore",
)


@dataclass(frozen=True)
class DictionaryOptions:
    max_sample_values: int = 5
    example_max_len: int = 80


def _is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series)


def _is_boolean_dtype(series: pd.Series) -> bool:
    return pd.api.types.is_bool_dtype(series)


def _is_timestamp_col(name: str) -> bool:
    lowered = name.lower()
    return "timestamp" in lowered or "timegmt" in lowered or "timelocal" in lowered


def _looks_like_iso_datetime(series: pd.Series) -> bool:
    sample = series.dropna().astype(str).head(20)
    if sample.empty:
        return False
    return bool(sample.map(lambda v: bool(ISO_DT_RE.match(v))).any())


def _looks_like_epoch_ms(series: pd.Series) -> bool:
    if not _is_numeric(series):
        return False
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return False
    max_v = float(numeric.max())
    return max_v >= 1_000_000_000_000


def _looks_like_epoch_seconds(series: pd.Series) -> bool:
    if not _is_numeric(series):
        return False
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return False
    max_v = float(numeric.max())
    return 1_000_000_000 <= max_v < 1_000_000_000_000


def _infer_unit(name: str, series: pd.Series) -> str:
    lowered = name.lower()
    if _is_timestamp_col(name):
        if _looks_like_iso_datetime(series):
            return "datetime"
        if _looks_like_epoch_ms(series):
            return "ms"
        if _looks_like_epoch_seconds(series):
            return "s"

    if "version" in lowered:
        return ""

    if "meters" in lowered:
        return "Meters"
    if "durationinmilliseconds" in lowered:
        return "Milliseconds"
    if "seconds" in lowered:
        return "Seconds"
    if "hydration" in lowered and "ml" in lowered:
        return "mL"
    if "kilocalories" in lowered or "calories" in lowered:
        return "Kilocalories"
    if "milliseconds" in lowered:
        return "Milliseconds"
    if "heartrate" in lowered:
        return "bpm"
    if lowered.endswith("hr") or "averagehr" in lowered:
        return "bpm"
    if "respiration" in lowered:
        return "brpm"
    if "spo2" in lowered:
        return "percent"

    if "value" in lowered and _is_numeric(series):
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().any():
            min_v = float(numeric.min())
            max_v = float(numeric.max())
            if 0 <= min_v <= 100 and 0 <= max_v <= 100:
                return "percent"

    return ""


def _infer_group(name: str) -> str:
    lowered = name.lower()
    if lowered.startswith("alldaystress") or "stress" in lowered:
        return "stress"
    if lowered.startswith("bodybattery") or "bodybattery" in lowered:
        return "body_battery"
    if lowered.startswith("respiration") or "respiration" in lowered:
        return "respiration"
    if lowered.startswith("hydration"):
        return "hydration"
    if lowered.startswith("includes"):
        return "flags_includes"
    if lowered.startswith("sleep") or "sleep" in lowered:
        return "sleep"
    if "spo2" in lowered:
        return "spo2"
    if "heartrate" in lowered:
        return "heart_rate"
    if "kilocalories" in lowered or "calories" in lowered:
        return "calories"
    if "steps" in lowered or "distance" in lowered or "meters" in lowered:
        return "steps_distance"
    if "timestamp" in lowered or lowered.endswith("date") or "date" in lowered:
        return "timestamps"
    return "other"


def _column_annotations(name: str, inferred_group: str) -> dict[str, Any]:
    """Decision-support annotations for downstream usage and prioritization."""
    used_in_quality = name in QUALITY_COLUMNS

    # Broad EDA usage heuristic with a few exclusions for clearly technical/meta columns.
    technical_prefixes = ("version", "source")
    used_in_eda = not (
        name == "calendarDate"
        or name.endswith("_calendarDate")
        or any(name.lower().startswith(p) for p in technical_prefixes)
        or "userprofilepk" in name.lower()
        or "uuid" in name.lower()
    )

    model_feature_groups = {
        "stress",
        "body_battery",
        "heart_rate",
        "steps_distance",
        "calories",
        "sleep",
        "spo2",
        "respiration",
        "hydration",
    }
    candidate_model_feature = (
        used_in_eda and inferred_group in model_feature_groups and name != "calendarDate"
    )

    high_priority = set(KEY_ANALYSIS_COLUMNS) | QUALITY_COLUMNS
    if name in high_priority:
        analysis_priority = "high"
    elif inferred_group in {"stress", "sleep", "body_battery", "heart_rate", "steps_distance", "spo2"}:
        analysis_priority = "medium"
    else:
        analysis_priority = "low"

    return {
        "used_in_quality": used_in_quality,
        "used_in_eda": used_in_eda,
        "candidate_model_feature": candidate_model_feature,
        "analysis_priority": analysis_priority,
    }


def _note_for_column(name: str, series: pd.Series) -> str:
    lowered = name.lower()
    if "uuid" in lowered or "userprofilepk" in lowered:
        return "likely identifier"

    if _is_timestamp_col(name):
        if _looks_like_iso_datetime(series):
            return "ISO datetime string"
        if _looks_like_epoch_ms(series):
            return "epoch millis"
        if _looks_like_epoch_seconds(series):
            return "epoch seconds timestamp"

    if _is_numeric(series) and ("timestamp" in lowered or "date" in lowered):
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().any():
            max_v = float(numeric.max())
            if max_v >= 1_000_000_000_000:
                return "epoch millis timestamp"
            if 1_000_000_000 <= max_v < 1_000_000_000_000:
                return "epoch seconds timestamp"

    if _looks_like_iso_datetime(series):
        return "ISO datetime string"

    return ""


def _example_values(series: pd.Series, max_values: int) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return json.dumps([])
    unique = pd.unique(non_null)
    sample = unique[:max_values]
    safe: list[Any] = []
    for value in sample:
        v = value.item() if hasattr(value, "item") else value
        if isinstance(v, (pd.Timestamp, datetime, date)):
            safe.append(v.isoformat())
        else:
            safe.append(v)
    return json.dumps(safe)


def _numeric_stats(series: pd.Series) -> dict[str, Any]:
    if (not _is_numeric(series)) or _is_boolean_dtype(series):
        return {
            "min": None,
            "p05": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p95": None,
            "max": None,
            "mean": None,
            "std": None,
        }
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return {
            "min": None,
            "p05": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p95": None,
            "max": None,
            "mean": None,
            "std": None,
        }
    q = numeric.quantile([0.05, 0.25, 0.75, 0.95])
    return {
        "min": float(numeric.min()),
        "p05": float(q.loc[0.05]),
        "p25": float(q.loc[0.25]),
        "median": float(numeric.median()),
        "p75": float(q.loc[0.75]),
        "p95": float(q.loc[0.95]),
        "max": float(numeric.max()),
        "mean": float(numeric.mean()),
        "std": float(numeric.std()),
    }


def _zero_pct(series: pd.Series) -> float | None:
    if (not _is_numeric(series)) or _is_boolean_dtype(series):
        return None
    numeric = pd.to_numeric(series, errors="coerce")
    numeric = numeric.dropna()
    if numeric.empty:
        return None
    return float((numeric == 0).mean() * 100.0)


def _is_constant_non_null(series: pd.Series) -> bool | None:
    non_null = series.dropna()
    if non_null.empty:
        return None
    return bool(non_null.nunique(dropna=True) <= 1)


def _coverage_window_metrics(
    *,
    series: pd.Series,
    calendar_dates: pd.Series | None,
) -> dict[str, Any]:
    if calendar_dates is None:
        return {
            "first_non_null_date": None,
            "last_non_null_date": None,
            "coverage_span_days": None,
            "coverage_within_span_pct": None,
        }

    mask = series.notna() & calendar_dates.notna()
    if not bool(mask.any()):
        return {
            "first_non_null_date": None,
            "last_non_null_date": None,
            "coverage_span_days": None,
            "coverage_within_span_pct": None,
        }

    dates = calendar_dates.loc[mask]
    first = pd.Timestamp(dates.min()).normalize()
    last = pd.Timestamp(dates.max()).normalize()
    span_days = int((last - first).days) + 1

    in_span = calendar_dates.notna() & (calendar_dates >= first) & (calendar_dates <= last)
    in_span_rows = int(in_span.sum())
    coverage_pct = float(mask.sum() / in_span_rows * 100.0) if in_span_rows else None

    return {
        "first_non_null_date": first.date().isoformat(),
        "last_non_null_date": last.date().isoformat(),
        "coverage_span_days": span_days,
        "coverage_within_span_pct": coverage_pct,
    }


def build_data_dictionary(df: pd.DataFrame, max_sample_values: int = 5) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total = len(df)
    calendar_dates: pd.Series | None = None
    if "calendarDate" in df.columns:
        parsed = pd.to_datetime(df["calendarDate"], errors="coerce")
        if isinstance(parsed.dtype, pd.DatetimeTZDtype):
            parsed = parsed.dt.tz_localize(None)
        calendar_dates = parsed.dt.normalize()

    for col in df.columns:
        series = df[col]
        non_null = int(series.notna().sum())
        non_null_pct = float(non_null / total * 100) if total else 0.0
        missing = int(series.isna().sum())
        missing_pct = float(missing / total * 100) if total else 0.0
        n_unique = int(series.nunique(dropna=True))

        stats = _numeric_stats(series)
        coverage = _coverage_window_metrics(series=series, calendar_dates=calendar_dates)
        inferred_group = _infer_group(col)
        annotations = _column_annotations(col, inferred_group)
        row = {
            "column": col,
            "dtype": str(series.dtype),
            "non_null_count": non_null,
            "non_null_pct": non_null_pct,
            "missing_count": missing,
            "missing_pct": missing_pct,
            "n_unique": n_unique,
            "is_constant": _is_constant_non_null(series),
            "zero_pct": _zero_pct(series),
            "first_non_null_date": coverage["first_non_null_date"],
            "last_non_null_date": coverage["last_non_null_date"],
            "coverage_span_days": coverage["coverage_span_days"],
            "coverage_within_span_pct": coverage["coverage_within_span_pct"],
            "example_values": _example_values(series, max_sample_values),
            "min": stats["min"],
            "p05": stats["p05"],
            "p25": stats["p25"],
            "median": stats["median"],
            "p75": stats["p75"],
            "p95": stats["p95"],
            "max": stats["max"],
            "mean": stats["mean"],
            "std": stats["std"],
            "inferred_unit": _infer_unit(col, series),
            "inferred_group": inferred_group,
            "notes": _note_for_column(col, series),
            "used_in_quality": annotations["used_in_quality"],
            "used_in_eda": annotations["used_in_eda"],
            "candidate_model_feature": annotations["candidate_model_feature"],
            "analysis_priority": annotations["analysis_priority"],
        }
        rows.append(row)

    return pd.DataFrame(rows)


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def _markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "|" + "|".join([" --- "] * len(columns)) + "|"
    lines = [header, sep]
    for _, row in df.iterrows():
        values = [_format_markdown_value(row.get(col, "")) for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _format_markdown_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (float,)) and pd.isna(value):
        return ""
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if abs(value) >= 1000:
            return f"{value:.2f}".rstrip("0").rstrip(".")
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


def build_markdown_report(
    dictionary_df: pd.DataFrame,
    source_df: pd.DataFrame,
    *,
    options: DictionaryOptions | None = None,
    mode: str = "full",
) -> str:
    if mode not in {"full", "summary"}:
        raise ValueError("mode must be 'full' or 'summary'")

    opts = options or DictionaryOptions()

    now = datetime.now(timezone.utc).isoformat()
    shape = f"rows={len(source_df)}, columns={len(source_df.columns)}"

    date_range = ""
    if "calendarDate" in source_df.columns:
        dates = pd.to_datetime(source_df["calendarDate"], errors="coerce")
        if dates.notna().any():
            date_range = f"{dates.min().date()} to {dates.max().date()}"

    warnings = dictionary_df[dictionary_df["notes"] == "likely identifier"]["column"].tolist()
    warning_text = ""
    if warnings:
        warning_text = (
            "\n\n**WARNING:** Identifier-like columns detected: "
            + ", ".join(warnings)
            + "\n"
        )

    lines = [
        "# Data Dictionary",
        "",
        f"Generated at (UTC): {now}",
        f"Dataset shape: {shape}",
    ]
    if date_range:
        lines.append(f"Date range: {date_range}")
    if warning_text:
        lines.append(warning_text.strip())

    if "analysis_priority" in dictionary_df.columns:
        priority_counts = (
            dictionary_df["analysis_priority"]
            .fillna("unknown")
            .astype(str)
            .value_counts()
            .to_dict()
        )
        lines.extend(
            [
                "",
                "## Executive summary",
                "",
                f"- Analysis priority counts: {priority_counts}",
            ]
        )

    # Decision-oriented shortlist for quicker navigation and downstream planning.
    if "column" in dictionary_df.columns:
        key_signals = dictionary_df[dictionary_df["column"].isin(KEY_ANALYSIS_COLUMNS)].copy()
        if not key_signals.empty:
            order_map = {c: i for i, c in enumerate(KEY_ANALYSIS_COLUMNS)}
            key_signals["_order"] = key_signals["column"].map(order_map)
            key_signals = key_signals.sort_values("_order")
            cols = [
                "column",
                "inferred_group",
                "inferred_unit",
                "non_null_pct",
                "missing_pct",
                "is_constant",
                "zero_pct",
                "first_non_null_date",
                "last_non_null_date",
                "used_in_quality",
                "used_in_eda",
                "candidate_model_feature",
                "analysis_priority",
                "notes",
            ]
            existing_cols = [c for c in cols if c in key_signals.columns]
            lines.extend(
                [
                    "",
                    "## Key analysis signals",
                    "",
                    _markdown_table(key_signals[existing_cols], existing_cols),
                ]
            )

    if "used_in_quality" in dictionary_df.columns:
        quality_cols = dictionary_df[dictionary_df["used_in_quality"] == True].copy()
        if not quality_cols.empty:
            quality_cols = quality_cols.sort_values(
                ["missing_pct", "column"], ascending=[False, True]
            )
            cols = [
                "column",
                "dtype",
                "non_null_pct",
                "missing_pct",
                "first_non_null_date",
                "last_non_null_date",
                "coverage_within_span_pct",
                "inferred_group",
                "notes",
            ]
            existing_cols = [c for c in cols if c in quality_cols.columns]
            lines.extend(
                [
                    "",
                    "## Quality-relevant columns",
                    "",
                    _markdown_table(quality_cols[existing_cols], existing_cols),
                ]
            )

            # Explain why the current quality stage is feasible using observed coverage.
            coverage_min = quality_cols["non_null_pct"].min() if "non_null_pct" in quality_cols.columns else None
            coverage_med = quality_cols["non_null_pct"].median() if "non_null_pct" in quality_cols.columns else None
            low_cov = quality_cols[quality_cols.get("non_null_pct", pd.Series(dtype=float)) < 85].copy()
            low_cov_list = []
            if not low_cov.empty and "column" in low_cov.columns and "non_null_pct" in low_cov.columns:
                low_cov = low_cov.sort_values("non_null_pct", ascending=True)
                low_cov_list = [
                    f"{row['column']} ({_format_markdown_value(row['non_null_pct'])}% non-null)"
                    for _, row in low_cov.iterrows()
                ]

            lines.extend(
                [
                    "",
                    "## Quality-readiness rationale",
                    "",
                    f"- Quality uses `{int(len(quality_cols))}` core columns/flags.",
                    f"- Non-null coverage across these columns ranges from `{_format_markdown_value(coverage_min)}%` to `100%`.",
                    f"- Median non-null coverage across quality-relevant columns: `{_format_markdown_value(coverage_med)}%`.",
                ]
            )
            if low_cov_list:
                lines.append(
                    "- Lowest-coverage quality inputs (expected to drive many partial/bad labels): "
                    + ", ".join(low_cov_list)
                )
            lines.extend(
                [
                    "- Use this table to justify threshold choices and explain why some labels are dominated by missing sleep/body-battery coverage rather than parser failures.",
                ]
            )

    missingness_limit = 20 if mode == "summary" else 30
    summary = dictionary_df.sort_values("missing_pct", ascending=False).head(missingness_limit)
    summary_table = summary[
        [
            "column",
            "dtype",
            "non_null_pct",
            "missing_pct",
            "is_constant",
            "first_non_null_date",
            "last_non_null_date",
            "inferred_group",
            "notes",
        ]
    ]
    lines.extend(
        [
            "",
            f"## Missingness summary (top {missingness_limit})",
            "",
            _markdown_table(summary_table, list(summary_table.columns)),
        ]
    )

    if mode == "summary":
        lines.extend(
            [
                "",
                "## Notes",
                "",
                "- This is the short decision-support report (`summary` mode).",
                "- Use `data_dictionary.md` (full mode) for complete column-by-group appendix.",
            ]
        )
        return "\n".join(lines) + "\n"

    lines.append("")
    lines.append("## Columns by group")

    grouped = dictionary_df.sort_values(["inferred_group", "column"]).groupby("inferred_group")
    for group, group_df in grouped:
        lines.append("")
        lines.append(f"### {group}")
        group_view = group_df.copy()
        group_view["example_values"] = group_view["example_values"].map(
            lambda v: _truncate(str(v), opts.example_max_len)
        )
        cols = [
            "column",
            "dtype",
            "non_null_pct",
            "missing_pct",
            "n_unique",
            "is_constant",
            "zero_pct",
            "first_non_null_date",
            "last_non_null_date",
            "example_values",
            "min",
            "p05",
            "p25",
            "median",
            "p75",
            "p95",
            "max",
            "inferred_unit",
            "notes",
        ]
        lines.append("")
        lines.append(_markdown_table(group_view[cols], cols))

    return "\n".join(lines) + "\n"


def write_dictionary_reports(
    dictionary_df: pd.DataFrame,
    source_df: pd.DataFrame,
    out_dir: Path,
    *,
    options: DictionaryOptions | None = None,
    markdown_mode: str = "full",
) -> tuple[Path, Path | None, Path | None]:
    if markdown_mode not in {"full", "summary", "both"}:
        raise ValueError("markdown_mode must be one of: full, summary, both")

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "data_dictionary.csv"
    full_md_path = out_dir / "data_dictionary.md"
    summary_md_path = out_dir / "data_dictionary_summary.md"

    dictionary_df.to_csv(csv_path, index=False)
    wrote_full: Path | None = None
    wrote_summary: Path | None = None

    if markdown_mode in {"full", "both"}:
        md = build_markdown_report(dictionary_df, source_df, options=options, mode="full")
        full_md_path.write_text(md, encoding="utf-8")
        wrote_full = full_md_path

    if markdown_mode in {"summary", "both"}:
        md_summary = build_markdown_report(dictionary_df, source_df, options=options, mode="summary")
        summary_md_path.write_text(md_summary, encoding="utf-8")
        wrote_summary = summary_md_path

    return csv_path, wrote_full, wrote_summary
