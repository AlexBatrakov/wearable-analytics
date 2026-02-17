from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ISO_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")


@dataclass(frozen=True)
class DictionaryOptions:
    max_sample_values: int = 5
    example_max_len: int = 80


def _is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series)


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


def _infer_unit(name: str, series: pd.Series) -> str:
    lowered = name.lower()
    if _is_timestamp_col(name):
        if series.dtype == object and _looks_like_iso_datetime(series):
            return "datetime"
        if _looks_like_epoch_ms(series):
            return "ms"

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
    if "respiration" in lowered:
        return "brpm"
    if "spo2" in lowered:
        return "percent"
    if "heartrate" in lowered:
        return "bpm"

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
    if lowered.startswith("bodybattery"):
        return "body_battery"
    if lowered.startswith("respiration"):
        return "respiration"
    if lowered.startswith("hydration"):
        return "hydration"
    if lowered.startswith("includes"):
        return "flags_includes"
    if lowered.startswith("sleep"):
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


def _note_for_column(name: str, series: pd.Series) -> str:
    lowered = name.lower()
    if "uuid" in lowered or "userprofilepk" in lowered:
        return "likely identifier"

    if _is_timestamp_col(name):
        if series.dtype == object and _looks_like_iso_datetime(series):
            return "ISO datetime string"
        if _looks_like_epoch_ms(series):
            return "epoch millis"

    if _is_numeric(series) and ("timestamp" in lowered or "date" in lowered):
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().any():
            max_v = float(numeric.max())
            if max_v >= 1_000_000_000_000:
                return "epoch millis timestamp"
            if 1_000_000_000 <= max_v < 1_000_000_000_000:
                return "epoch seconds timestamp"

    if series.dtype == object and _looks_like_iso_datetime(series):
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
    if not _is_numeric(series):
        return {"min": None, "median": None, "max": None, "mean": None, "std": None}
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() == 0:
        return {"min": None, "median": None, "max": None, "mean": None, "std": None}
    return {
        "min": float(numeric.min()),
        "median": float(numeric.median()),
        "max": float(numeric.max()),
        "mean": float(numeric.mean()),
        "std": float(numeric.std()),
    }


def build_data_dictionary(df: pd.DataFrame, max_sample_values: int = 5) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total = len(df)

    for col in df.columns:
        series = df[col]
        non_null = int(series.notna().sum())
        missing = int(series.isna().sum())
        missing_pct = float(missing / total * 100) if total else 0.0
        n_unique = int(series.nunique(dropna=True))

        stats = _numeric_stats(series)
        row = {
            "column": col,
            "dtype": str(series.dtype),
            "non_null_count": non_null,
            "missing_count": missing,
            "missing_pct": missing_pct,
            "n_unique": n_unique,
            "example_values": _example_values(series, max_sample_values),
            "min": stats["min"],
            "median": stats["median"],
            "max": stats["max"],
            "mean": stats["mean"],
            "std": stats["std"],
            "inferred_unit": _infer_unit(col, series),
            "inferred_group": _infer_group(col),
            "notes": _note_for_column(col, series),
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
        values = [str(row.get(col, "")) for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_markdown_report(
    dictionary_df: pd.DataFrame,
    source_df: pd.DataFrame,
    *,
    options: DictionaryOptions | None = None,
) -> str:
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

    summary = dictionary_df.sort_values("missing_pct", ascending=False).head(30)
    summary_table = summary[["column", "dtype", "missing_pct", "inferred_group", "notes"]]
    lines.extend(["", "## Missingness summary (top 30)", "", _markdown_table(summary_table, list(summary_table.columns))])

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
            "missing_pct",
            "n_unique",
            "example_values",
            "min",
            "median",
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
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "data_dictionary.csv"
    md_path = out_dir / "data_dictionary.md"

    dictionary_df.to_csv(csv_path, index=False)
    md = build_markdown_report(dictionary_df, source_df, options=options)
    md_path.write_text(md, encoding="utf-8")
    return csv_path, md_path