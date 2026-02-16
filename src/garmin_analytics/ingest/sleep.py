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
    "remSleepSeconds",
    "awakeSleepSeconds",
    "unmeasurableSeconds",
    "averageRespiration",
    "lowestRespiration",
    "highestRespiration",
    "avgSleepStress",
    "awakeCount",
    "restlessMomentCount",
    "retro",
    "sleepWindowConfirmationType",
    "spo2SleepMeasurementStartTimestampGMT",
    "spo2SleepMeasurementEndTimestampGMT",
    "spo2SleepAverageSPO2",
    "spo2SleepAverageHR",
    "spo2SleepLowestSPO2",
    "sleepOverallScore",
    "sleepQualityScore",
    "sleepDurationScore",
    "sleepRecoveryScore",
    "sleepDeepScore",
    "sleepRemScore",
    "sleepLightScore",
    "sleepAwakeningsCountScore",
    "sleepAwakeTimeScore",
    "sleepCombinedAwakeScore",
    "sleepRestfulnessScore",
    "sleepInterruptionsScore",
    "sleepFeedback",
    "sleepInsight",
]

INT_COLS = [
    "sleepStartTimestampGMT",
    "sleepEndTimestampGMT",
    "deepSleepSeconds",
    "lightSleepSeconds",
    "remSleepSeconds",
    "awakeSleepSeconds",
    "unmeasurableSeconds",
    "awakeCount",
    "restlessMomentCount",
    "spo2SleepMeasurementStartTimestampGMT",
    "spo2SleepMeasurementEndTimestampGMT",
    "spo2SleepLowestSPO2",
    "sleepOverallScore",
    "sleepQualityScore",
    "sleepDurationScore",
    "sleepRecoveryScore",
    "sleepDeepScore",
    "sleepRemScore",
    "sleepLightScore",
    "sleepAwakeningsCountScore",
    "sleepAwakeTimeScore",
    "sleepCombinedAwakeScore",
    "sleepRestfulnessScore",
    "sleepInterruptionsScore",
]

FLOAT_COLS = [
    "averageRespiration",
    "lowestRespiration",
    "highestRespiration",
    "avgSleepStress",
    "spo2SleepAverageSPO2",
    "spo2SleepAverageHR",
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


def _to_unix_seconds_nullable(series: pd.Series) -> pd.Series:
    """Convert timestamps to nullable unix seconds.

    Supports already-numeric seconds (int/float/str) and ISO-like datetime strings.
    """
    # First: numeric-like seconds.
    numeric = pd.to_numeric(series.map(_sanitize_scalar), errors="coerce")
    out = numeric.where(numeric.isna() | (numeric % 1 == 0)).astype("Int64")

    # Second: parse ISO timestamps for the remaining values.
    missing = out.isna()
    if missing.any():
        dt = pd.to_datetime(series.where(missing), errors="coerce", utc=True)
        epoch = pd.Timestamp("1970-01-01", tz="UTC")
        secs = (dt - epoch) / pd.Timedelta(seconds=1)
        secs = pd.to_numeric(secs, errors="coerce")
        secs = secs.where(dt.notna())
        out = out.where(~missing, secs.astype("Int64"))

    return out


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

    scores: dict[str, Any] = {}
    if isinstance(sleep_scores, dict):
        scores = {
            "sleepOverallScore": _pick(sleep_scores, ["overallScore", "score", "overall"]),
            "sleepQualityScore": sleep_scores.get("qualityScore"),
            "sleepDurationScore": sleep_scores.get("durationScore"),
            "sleepRecoveryScore": sleep_scores.get("recoveryScore"),
            "sleepDeepScore": sleep_scores.get("deepScore"),
            "sleepRemScore": sleep_scores.get("remScore"),
            "sleepLightScore": sleep_scores.get("lightScore"),
            "sleepAwakeningsCountScore": sleep_scores.get("awakeningsCountScore"),
            "sleepAwakeTimeScore": sleep_scores.get("awakeTimeScore"),
            "sleepCombinedAwakeScore": sleep_scores.get("combinedAwakeScore"),
            "sleepRestfulnessScore": sleep_scores.get("restfulnessScore"),
            "sleepInterruptionsScore": sleep_scores.get("interruptionsScore"),
            "sleepFeedback": sleep_scores.get("feedback"),
            "sleepInsight": sleep_scores.get("insight"),
        }

    spo2 = entry.get("spo2SleepSummary")
    spo2_out: dict[str, Any] = {}
    if isinstance(spo2, dict):
        # Do not include identifiers like userProfilePk or deviceId.
        spo2_out = {
            "spo2SleepMeasurementStartTimestampGMT": spo2.get("sleepMeasurementStartGMT"),
            "spo2SleepMeasurementEndTimestampGMT": spo2.get("sleepMeasurementEndGMT"),
            "spo2SleepAverageSPO2": spo2.get("averageSPO2"),
            "spo2SleepAverageHR": spo2.get("averageHR"),
            "spo2SleepLowestSPO2": spo2.get("lowestSPO2"),
        }

    row = {
        "calendarDate": entry.get("calendarDate") or entry.get("calendarDateStr"),
        "sleepStartTimestampGMT": entry.get("sleepStartTimestampGMT"),
        "sleepEndTimestampGMT": entry.get("sleepEndTimestampGMT"),
        "deepSleepSeconds": entry.get("deepSleepSeconds"),
        "lightSleepSeconds": entry.get("lightSleepSeconds"),
        "remSleepSeconds": entry.get("remSleepSeconds"),
        "awakeSleepSeconds": entry.get("awakeSleepSeconds"),
        "unmeasurableSeconds": entry.get("unmeasurableSeconds"),
        "averageRespiration": entry.get("averageRespiration"),
        "lowestRespiration": entry.get("lowestRespiration"),
        "highestRespiration": entry.get("highestRespiration"),
        "avgSleepStress": entry.get("avgSleepStress"),
        "awakeCount": entry.get("awakeCount"),
        "restlessMomentCount": entry.get("restlessMomentCount"),
        "retro": entry.get("retro"),
        "sleepWindowConfirmationType": entry.get("sleepWindowConfirmationType"),
    }

    row.update(spo2_out)
    row.update(scores)

    # Ensure sleepOverallScore exists even when scores are missing.
    row.setdefault("sleepOverallScore", None)
    return row


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

    # Parse timestamps (support numeric seconds and ISO strings).
    for col in ["sleepStartTimestampGMT", "sleepEndTimestampGMT", "spo2SleepMeasurementStartTimestampGMT", "spo2SleepMeasurementEndTimestampGMT"]:
        if col in df.columns:
            df[col] = _to_unix_seconds_nullable(df[col])

    for col in INT_COLS:
        if col in [
            "sleepStartTimestampGMT",
            "sleepEndTimestampGMT",
            "spo2SleepMeasurementStartTimestampGMT",
            "spo2SleepMeasurementEndTimestampGMT",
        ]:
            continue
        df[col] = _to_int_nullable(df[col])
    for col in FLOAT_COLS:
        df[col] = df[col].map(_sanitize_scalar)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "retro" in df.columns:
        df["retro"] = df["retro"].astype("boolean")

    df = df.sort_values("calendarDate").drop_duplicates("calendarDate", keep="last")
    return df.reset_index(drop=True)
