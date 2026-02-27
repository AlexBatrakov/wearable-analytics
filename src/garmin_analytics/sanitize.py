from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


_GUID_RE = re.compile(r"^[0-9a-fA-F-]{32,}$")
_STRESS_LEVEL_RE = re.compile(r"(?:^|_)averageStressLevel(?:Intensity)?$")


def default_sensitive_column_patterns() -> list[re.Pattern[str]]:
    """Return default regex patterns for sensitive identifier-like column names."""
    return [
        re.compile(r"uuid", re.IGNORECASE),
        re.compile(r"userProfilePK", re.IGNORECASE),
    ]


def _looks_like_identifier_name(name: str) -> bool:
    lowered = name.lower()

    if lowered == "uuid" or "uuid" in lowered:
        return True
    if "userprofilepk" in lowered:
        return True

    # Conservative handling of "pk": only drop when it's clearly an identifier.
    # We avoid dropping legitimate metric columns that may contain "pk" as part of a word.
    if "pk" in lowered:
        pk_is_token = lowered.endswith("pk") or "_pk" in lowered or lowered.startswith("pk_")
        if pk_is_token and ("user" in lowered or "profile" in lowered):
            return True

    return False


def _looks_like_guid_column(series: pd.Series, sample_size: int = 200) -> bool:
    if series.dtype.kind not in {"O", "U", "S"}:
        return False

    non_null = series.dropna()
    if non_null.empty:
        return False

    sample = non_null.astype(str).head(sample_size)
    matches = sample.map(lambda v: bool(_GUID_RE.match(v)))
    if len(sample) < 5:
        # Conservative for small samples: drop only if everything matches.
        return bool(matches.all())

    return matches.mean() >= 0.8


def _is_calendar_duplicate(col: str) -> bool:
    lowered = col.lower()
    if lowered == "calendardate":
        return False
    return lowered.endswith("_calendardate") or lowered.endswith("_calendardatestr")


def _is_stress_level_column(col: str) -> bool:
    if col == "avgSleepStress":
        return True
    return bool(_STRESS_LEVEL_RE.search(col))


def _normalize_stress_levels(df: pd.DataFrame) -> dict[str, int]:
    """Normalize stress-level sentinel/out-of-range values to NaN.

    Garmin exports may encode missing stress levels with negative sentinels
    (e.g., -2 for ASLEEP, -1 for AWAKE/TOTAL). Stress level is expected to be
    in [0, 100], so anything outside this interval is treated as missing.
    """
    replaced_counts: dict[str, int] = {}
    for col in df.columns:
        if not _is_stress_level_column(col):
            continue

        numeric = pd.to_numeric(df[col], errors="coerce")
        invalid_mask = numeric.notna() & ((numeric < 0) | (numeric > 100))
        invalid_count = int(invalid_mask.sum())
        if invalid_count == 0:
            continue

        df[col] = numeric.mask(invalid_mask)
        replaced_counts[col] = invalid_count

    return replaced_counts


def _sanitize_dataframe_impl(
    df: pd.DataFrame,
    keep: list[str] | None = None,
    drop: list[str] | None = None,
    *,
    allow_identifiers: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    keep_set = set(keep or [])
    user_drop_set = set(drop or [])

    rules_applied: list[str] = []
    to_drop: set[str] = set()

    # Always preserve calendarDate.
    calendar_col = "calendarDate"

    # Rule 1: Sensitive/identifier columns based on column names.
    sensitive_patterns = default_sensitive_column_patterns()
    sensitive_by_name: set[str] = set()
    for col in df.columns:
        if col == calendar_col:
            continue
        if any(p.search(col) for p in sensitive_patterns) or _looks_like_identifier_name(col):
            sensitive_by_name.add(col)

    if sensitive_by_name:
        rules_applied.append("drop_sensitive_columns_by_name")
        if not allow_identifiers:
            to_drop |= sensitive_by_name

    # Rule 1b: GUID-like values.
    guid_like: set[str] = set()
    if not allow_identifiers:
        for col in df.columns:
            if col == calendar_col:
                continue
            if _looks_like_guid_column(df[col]):
                guid_like.add(col)
        if guid_like:
            rules_applied.append("drop_guid_like_value_columns")
            to_drop |= guid_like

    # Rule 2: Redundant metadata.
    metadata_drop = {"version", "source"}
    meta_cols = {c for c in df.columns if c != calendar_col and c in metadata_drop}
    if meta_cols:
        rules_applied.append("drop_redundant_metadata_columns")
        to_drop |= meta_cols

    # Rule 2b: Nested duplicates of calendarDate.
    dup_cols = {c for c in df.columns if _is_calendar_duplicate(c)}
    if dup_cols:
        rules_applied.append("drop_nested_calendarDate_duplicates")
        to_drop |= dup_cols

    # Apply keep exceptions for non-identifier rules only.
    if keep_set:
        rules_applied.append("apply_keep_exceptions")
        if allow_identifiers:
            to_drop -= keep_set
        else:
            # Keep can prevent dropping metadata / duplicates, but not identifiers.
            to_drop = {c for c in to_drop if c not in keep_set or c in sensitive_by_name or c in guid_like}

    # Apply explicit user drop list (highest priority after calendarDate).
    if user_drop_set:
        rules_applied.append("apply_explicit_drop_list")
        to_drop |= user_drop_set

    to_drop.discard(calendar_col)

    kept_cols = [c for c in df.columns if c not in to_drop]
    if calendar_col in kept_cols:
        kept_cols = [calendar_col] + [c for c in kept_cols if c != calendar_col]

    out = df.loc[:, kept_cols].copy()
    stress_replacements = _normalize_stress_levels(out)

    if stress_replacements:
        rules_applied.append("normalize_stress_levels_out_of_range_to_null")

    report: dict[str, Any] = {
        "dropped_columns": sorted(to_drop),
        "kept_columns": list(out.columns),
        "rules_applied": rules_applied,
    }
    if stress_replacements:
        report["value_replacements"] = {
            "rule": "stress_levels_must_be_in_0_100",
            "replaced_to_null_by_column": dict(sorted(stress_replacements.items())),
        }
    return out, report


def sanitize_dataframe(
    df: pd.DataFrame,
    keep: list[str] | None = None,
    drop: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Sanitize a DataFrame by dropping sensitive identifiers and redundant metadata.

    This function is intentionally conservative: identifier-like columns are always dropped,
    even if listed in keep.
    """
    return _sanitize_dataframe_impl(df, keep=keep, drop=drop, allow_identifiers=False)


def sanitize_parquet_file(
    input_path: Path,
    output_path: Path,
    *,
    allow_identifiers: bool = False,
) -> dict[str, Any]:
    """Read a parquet, sanitize it, and write to output_path.

    Returns the report dict for this file.
    """
    df = pd.read_parquet(input_path)
    sanitized, report = _sanitize_dataframe_impl(df, allow_identifiers=allow_identifiers)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sanitized.to_parquet(output_path, index=False, engine="pyarrow")

    report["input_path"] = str(input_path)
    report["output_path"] = str(output_path)
    report["rows"] = int(len(df))
    report["cols_before"] = int(df.shape[1])
    report["cols_after"] = int(sanitized.shape[1])
    return report


def write_sanitize_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    report = dict(report)
    report.setdefault(
        "generated_at_utc",
        datetime.now(timezone.utc).isoformat(),
    )
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
