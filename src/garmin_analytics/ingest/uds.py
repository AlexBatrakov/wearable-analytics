from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ..util.io import read_json

COLUMNS = [
    "calendarDate",
    "totalSteps",
    "totalDistanceMeters",
    "activeKilocalories",
    "bmrKilocalories",
    "totalKilocalories",
    "restingHeartRate",
    "minHeartRate",
    "maxHeartRate",
    "bodyBatteryStartOfDay",
    "bodyBatteryEndOfDay",
    "bodyBatteryLowest",
    "bodyBatteryHighest",
    "stressAwakeDurationSeconds",
    "stressAsleepDurationSeconds",
    "stressTotalDurationSeconds",
]

INT_COLS = [
    "totalSteps",
    "totalDistanceMeters",
    "activeKilocalories",
    "bmrKilocalories",
    "totalKilocalories",
    "restingHeartRate",
    "minHeartRate",
    "maxHeartRate",
    "bodyBatteryStartOfDay",
    "bodyBatteryEndOfDay",
    "bodyBatteryLowest",
    "bodyBatteryHighest",
    "stressAwakeDurationSeconds",
    "stressAsleepDurationSeconds",
    "stressTotalDurationSeconds",
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


def _extract_body_battery(entry: dict[str, Any]) -> dict[str, Any]:
    """Extract body battery metrics from a daily summary entry."""
    bb = (
        entry.get("bodyBattery")
        or entry.get("bodyBatteryValues")
        or entry.get("bodyBatterySummary")
        or entry.get("bodyBatteryStats")
    )
    if isinstance(bb, dict):
        return {
            "bodyBatteryStartOfDay": _pick(
                bb, ["startOfDay", "bodyBatteryStartOfDay", "start"]
            ),
            "bodyBatteryEndOfDay": _pick(
                bb, ["endOfDay", "bodyBatteryEndOfDay", "end"]
            ),
            "bodyBatteryLowest": _pick(bb, ["lowest", "bodyBatteryLowest", "low"]),
            "bodyBatteryHighest": _pick(
                bb, ["highest", "bodyBatteryHighest", "high"]
            ),
        }
    return {
        "bodyBatteryStartOfDay": None,
        "bodyBatteryEndOfDay": None,
        "bodyBatteryLowest": None,
        "bodyBatteryHighest": None,
    }


def _extract_stress(entry: dict[str, Any]) -> dict[str, Any]:
    """Extract stress duration metrics from a daily summary entry."""
    stress = (
        entry.get("stressSummary")
        or entry.get("stress")
        or entry.get("stressSummaryDto")
        or entry.get("stressSummaryData")
    )
    if isinstance(stress, dict):
        return {
            "stressAwakeDurationSeconds": _pick(
                stress,
                [
                    "awakeDuration",
                    "awakeStressDuration",
                    "awakeStressDurationSeconds",
                    "awakeStressDurationInSeconds",
                ],
            ),
            "stressAsleepDurationSeconds": _pick(
                stress,
                [
                    "sleepDuration",
                    "asleepDuration",
                    "asleepStressDuration",
                    "sleepStressDuration",
                    "sleepStressDurationSeconds",
                    "sleepStressDurationInSeconds",
                ],
            ),
            "stressTotalDurationSeconds": _pick(
                stress,
                [
                    "totalDuration",
                    "totalStressDuration",
                    "totalStressDurationSeconds",
                    "totalStressDurationInSeconds",
                ],
            ),
        }
    return {
        "stressAwakeDurationSeconds": None,
        "stressAsleepDurationSeconds": None,
        "stressTotalDurationSeconds": None,
    }


def _row_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Normalize a daily summary record into a flat row."""
    row = {
        "calendarDate": entry.get("calendarDate") or entry.get("calendarDateStr"),
        "totalSteps": entry.get("totalSteps"),
        "totalDistanceMeters": entry.get("totalDistanceMeters")
        or entry.get("totalDistance"),
        "activeKilocalories": entry.get("activeKilocalories"),
        "bmrKilocalories": entry.get("bmrKilocalories"),
        "totalKilocalories": entry.get("totalKilocalories"),
        "restingHeartRate": entry.get("restingHeartRate"),
        "minHeartRate": entry.get("minHeartRate"),
        "maxHeartRate": entry.get("maxHeartRate"),
    }
    row.update(_extract_body_battery(entry))
    row.update(_extract_stress(entry))
    return row


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    """Locate summary records inside a parsed UDS payload."""
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ["dailySummaries", "entries", "summaries", "records"]:
            if key in payload and isinstance(payload[key], list):
                return [row for row in payload[key] if isinstance(row, dict)]
    return []


def parse_uds_files(paths: list[Path]) -> pd.DataFrame:
    """Parse UDSFile_*.json files into a normalized daily DataFrame."""
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
        df[col] = df[col].map(_sanitize_scalar)
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    df = df.sort_values("calendarDate").drop_duplicates("calendarDate", keep="last")
    return df.reset_index(drop=True)
