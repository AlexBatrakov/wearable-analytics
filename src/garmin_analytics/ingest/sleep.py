from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ..util.io import read_json

COLUMNS = [
    "calendarDate",
    "sleepStartTimestampGMT",
    "sleepEndTimestampGMT",
    "deepSleepSeconds",
    "lightSleepSeconds",
    "awakeSleepSeconds",
    "unmeasurableSeconds",
    "averageRespiration",
    "lowestRespiration",
    "highestRespiration",
    "avgSleepStress",
    "sleepOverallScore",
]

INT_COLS = [
    "sleepStartTimestampGMT",
    "sleepEndTimestampGMT",
    "deepSleepSeconds",
    "lightSleepSeconds",
    "awakeSleepSeconds",
    "unmeasurableSeconds",
    "avgSleepStress",
    "sleepOverallScore",
]

FLOAT_COLS = [
    "averageRespiration",
    "lowestRespiration",
    "highestRespiration",
]


def _pick(mapping: dict[str, Any], keys: list[str]) -> Any:
    """Return the first non-null mapping value for the given keys."""
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _sanitize_scalar(value: Any) -> Any:
    """Coerce non-scalar values to None for numeric casting."""
    if isinstance(value, (list, tuple, dict)):
        return None
    return value


def _to_int_nullable(series: pd.Series) -> pd.Series:
    """Convert numeric-like values to nullable Int64, dropping non-integers."""
    series = series.map(_sanitize_scalar)
    series = pd.to_numeric(series, errors="coerce")
    series = series.where(series.isna() | (series % 1 == 0))
    return series.astype("Int64")


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    """Locate sleep records inside a parsed sleep payload."""
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ["sleepData", "dailySleep", "sleep"]:
            if key in payload and isinstance(payload[key], list):
                return [row for row in payload[key] if isinstance(row, dict)]
    return []


def _row_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Normalize a sleep entry into a flat row."""
    sleep_scores = entry.get("sleepScores")
    overall_score = None
    if isinstance(sleep_scores, dict):
        overall_score = _pick(sleep_scores, ["overallScore", "score", "overall"])

    return {
        "calendarDate": entry.get("calendarDate") or entry.get("calendarDateStr"),
        "sleepStartTimestampGMT": entry.get("sleepStartTimestampGMT"),
        "sleepEndTimestampGMT": entry.get("sleepEndTimestampGMT"),
        "deepSleepSeconds": entry.get("deepSleepSeconds"),
        "lightSleepSeconds": entry.get("lightSleepSeconds"),
        "awakeSleepSeconds": entry.get("awakeSleepSeconds"),
        "unmeasurableSeconds": entry.get("unmeasurableSeconds"),
        "averageRespiration": entry.get("averageRespiration"),
        "lowestRespiration": entry.get("lowestRespiration"),
        "highestRespiration": entry.get("highestRespiration"),
        "avgSleepStress": entry.get("avgSleepStress"),
        "sleepOverallScore": overall_score,
    }


def parse_sleep_files(paths: list[Path]) -> pd.DataFrame:
    """Parse *_sleepData.json files into a normalized sleep DataFrame."""
    rows: list[dict[str, Any]] = []
    for path in paths:
        payload = read_json(path)
        records = _extract_records(payload)
        for entry in records:
            rows.append(_row_from_entry(entry))

    if not rows:
        return pd.DataFrame(columns=COLUMNS)

    df = pd.DataFrame(rows)
    df = df.reindex(columns=COLUMNS)

    df["calendarDate"] = pd.to_datetime(df["calendarDate"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["calendarDate"])

    for col in INT_COLS:
        df[col] = _to_int_nullable(df[col])
    for col in FLOAT_COLS:
        df[col] = df[col].map(_sanitize_scalar)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values("calendarDate").drop_duplicates("calendarDate", keep="last")
    return df.reset_index(drop=True)
