from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ..util.io import read_json

CORE_COLUMNS = [
    "calendarDate",
    "totalSteps",
    "totalDistanceMeters",
    "activeKilocalories",
    "bmrKilocalories",
    "totalKilocalories",
    "restingHeartRate",
    "minHeartRate",
    "maxHeartRate",
]

CORE_DERIVED_COLUMNS = [
    "bodyBatteryStartOfDay",
    "bodyBatteryEndOfDay",
    "bodyBatteryLowest",
    "bodyBatteryHighest",
    "stressAwakeDurationSeconds",
    "stressAsleepDurationSeconds",
    "stressTotalDurationSeconds",
]

# Backwards-compat: tests/other modules may import this.
COLUMNS = [*CORE_COLUMNS, *CORE_DERIVED_COLUMNS]


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


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _flatten_dict(value: dict[str, Any], prefix: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, v in value.items():
        if _is_scalar(v):
            out[f"{prefix}_{key}"] = v
    return out


def _extract_body_battery_derived(entry: dict[str, Any]) -> dict[str, Any]:
    """Extract body battery metrics into stable derived columns.

    Supports both simplified schemas (start/end/lowest/highest) and
    DI-Connect schemas with a bodyBatteryStatList.
    """
    bb = (
        entry.get("bodyBattery")
        or entry.get("bodyBatteryValues")
        or entry.get("bodyBatterySummary")
        or entry.get("bodyBatteryStats")
    )
    if not isinstance(bb, dict):
        return {
            "bodyBatteryStartOfDay": None,
            "bodyBatteryEndOfDay": None,
            "bodyBatteryLowest": None,
            "bodyBatteryHighest": None,
        }

    # Simple schema
    start = _pick(bb, ["startOfDay", "bodyBatteryStartOfDay", "start"])
    end = _pick(bb, ["endOfDay", "bodyBatteryEndOfDay", "end"])
    lowest = _pick(bb, ["lowest", "bodyBatteryLowest", "low"])
    highest = _pick(bb, ["highest", "bodyBatteryHighest", "high"])

    # DI-Connect schema with stat list
    stat_list = bb.get("bodyBatteryStatList")
    if isinstance(stat_list, list):
        for item in stat_list:
            if not isinstance(item, dict):
                continue
            stat_type = item.get("bodyBatteryStatType")
            if not isinstance(stat_type, str):
                continue
            value = item.get("statsValue")
            if stat_type == "STARTOFDAY" and start is None:
                start = value
            elif stat_type == "ENDOFDAY" and end is None:
                end = value
            elif stat_type == "LOWEST" and lowest is None:
                lowest = value
            elif stat_type == "HIGHEST" and highest is None:
                highest = value

    return {
        "bodyBatteryStartOfDay": start,
        "bodyBatteryEndOfDay": end,
        "bodyBatteryLowest": lowest,
        "bodyBatteryHighest": highest,
    }


def _extract_stress_derived(entry: dict[str, Any]) -> dict[str, Any]:
    """Extract stress duration metrics into stable derived columns.

    Supports both stressSummary schemas and allDayStress aggregatorList.
    """
    stress = (
        entry.get("stressSummary")
        or entry.get("stress")
        or entry.get("stressSummaryDto")
        or entry.get("stressSummaryData")
    )
    awake = asleep = total = None

    if isinstance(stress, dict):
        awake = _pick(
            stress,
            [
                "awakeDuration",
                "awakeStressDuration",
                "awakeStressDurationSeconds",
                "awakeStressDurationInSeconds",
            ],
        )
        asleep = _pick(
            stress,
            [
                "sleepDuration",
                "asleepDuration",
                "asleepStressDuration",
                "sleepStressDuration",
                "sleepStressDurationSeconds",
                "sleepStressDurationInSeconds",
            ],
        )
        total = _pick(
            stress,
            [
                "totalDuration",
                "totalStressDuration",
                "totalStressDurationSeconds",
                "totalStressDurationInSeconds",
            ],
        )

    # DI-Connect allDayStress.aggregatorList also contains duration-like fields.
    all_day = entry.get("allDayStress")
    if isinstance(all_day, dict):
        agg_list = all_day.get("aggregatorList")
        if isinstance(agg_list, list):
            for item in agg_list:
                if not isinstance(item, dict):
                    continue
                agg_type = item.get("type")
                if not isinstance(agg_type, str):
                    continue
                dur = item.get("totalDuration")
                if dur is None:
                    continue
                if agg_type == "AWAKE" and awake is None:
                    awake = dur
                elif agg_type == "ASLEEP" and asleep is None:
                    asleep = dur
                elif agg_type == "TOTAL" and total is None:
                    total = dur

    return {
        "stressAwakeDurationSeconds": awake,
        "stressAsleepDurationSeconds": asleep,
        "stressTotalDurationSeconds": total,
    }


def _flatten_all_day_stress(entry: dict[str, Any]) -> dict[str, Any]:
    all_day = entry.get("allDayStress")
    if not isinstance(all_day, dict):
        return {}

    out: dict[str, Any] = _flatten_dict(all_day, "allDayStress")
    agg_list = all_day.get("aggregatorList")
    if not isinstance(agg_list, list):
        return out

    for item in agg_list:
        if not isinstance(item, dict):
            continue
        agg_type = item.get("type")
        if not isinstance(agg_type, str) or not agg_type:
            continue
        for k, v in item.items():
            if k == "type":
                continue
            if _is_scalar(v):
                out[f"allDayStress_{agg_type}_{k}"] = v

    return out


def _flatten_body_battery(entry: dict[str, Any]) -> dict[str, Any]:
    bb = (
        entry.get("bodyBattery")
        or entry.get("bodyBatteryValues")
        or entry.get("bodyBatterySummary")
        or entry.get("bodyBatteryStats")
    )
    if not isinstance(bb, dict):
        return {}

    out: dict[str, Any] = _flatten_dict(bb, "bodyBattery")
    stat_list = bb.get("bodyBatteryStatList")
    if not isinstance(stat_list, list):
        return out

    for item in stat_list:
        if not isinstance(item, dict):
            continue
        stat_type = item.get("bodyBatteryStatType")
        if not isinstance(stat_type, str) or not stat_type:
            continue
        # Common case: map the value directly
        if _is_scalar(item.get("statsValue")):
            out[f"bodyBatteryStat_{stat_type}"] = item.get("statsValue")
        # Also keep other scalar attributes
        for k, v in item.items():
            if k in {"bodyBatteryStatType", "statsValue"}:
                continue
            if _is_scalar(v):
                out[f"bodyBatteryStat_{stat_type}_{k}"] = v

    return out


def _flatten_entry(entry: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {}

    # Keep all scalar top-level fields.
    for key, value in entry.items():
        if _is_scalar(value):
            row[key] = value

    # Ensure calendarDate is always present (some exports use calendarDateStr).
    row["calendarDate"] = entry.get("calendarDate") or entry.get("calendarDateStr") or row.get("calendarDate")

    # Flatten selected nested dicts.
    for field in ["hydration", "respiration", "stressSummary"]:
        value = entry.get(field)
        if isinstance(value, dict):
            row.update(_flatten_dict(value, field))

    row.update(_flatten_all_day_stress(entry))
    row.update(_flatten_body_battery(entry))

    # Add stable derived columns (useful even when schemas differ).
    row.update(_extract_body_battery_derived(entry))
    row.update(_extract_stress_derived(entry))

    # Preserve a few legacy names for convenience.
    if "totalDistanceMeters" not in row and "totalDistance" in row:
        row["totalDistanceMeters"] = row.get("totalDistance")

    return row


def _coerce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if col == "calendarDate":
            continue
        s = df[col]

        non_null = s.dropna()
        if non_null.empty:
            continue

        # Boolean
        if non_null.map(lambda v: isinstance(v, bool)).all():
            df[col] = s.astype("boolean")
            continue

        # Numeric (allow numeric-like strings)
        numeric = pd.to_numeric(s.map(_sanitize_scalar), errors="coerce")
        if numeric.notna().sum() == 0:
            continue

        # If most values are numeric-like, coerce.
        if numeric.notna().sum() / max(len(non_null), 1) >= 0.95:
            numeric_non_null = numeric.dropna()
            is_int_like = (numeric_non_null % 1 == 0).all() if not numeric_non_null.empty else False
            if is_int_like:
                df[col] = numeric.astype("Int64")
            else:
                df[col] = numeric.astype("Float64")

    return df


def _deterministic_column_order(columns: list[str]) -> list[str]:
    seen: set[str] = set()

    def _add(out: list[str], col: str) -> None:
        if col in columns and col not in seen:
            out.append(col)
            seen.add(col)

    out: list[str] = []
    _add(out, "calendarDate")
    for col in CORE_COLUMNS:
        _add(out, col)
    for col in CORE_DERIVED_COLUMNS:
        _add(out, col)

    for col in sorted(columns):
        if col not in seen:
            out.append(col)
            seen.add(col)
    return out


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    """Locate summary records inside a parsed UDS payload."""
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        # Some payloads (and our pretty previews) may be a single record dict.
        if "calendarDate" in payload or "calendarDateStr" in payload:
            return [payload]
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
            rows.append(_flatten_entry(entry))

    if not rows:
        return pd.DataFrame(columns=COLUMNS)

    df = pd.DataFrame(rows)

    # Deterministic column order for stable analysis notebooks and diffs.
    ordered_cols = _deterministic_column_order(list(df.columns))
    df = df.reindex(columns=ordered_cols)

    df["calendarDate"] = pd.to_datetime(df["calendarDate"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["calendarDate"])

    df = _coerce_dtypes(df)

    df = df.sort_values("calendarDate").drop_duplicates("calendarDate", keep="last")
    return df.reset_index(drop=True)
