from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


FIT_EPOCH_S = 631065600

HEART_RATE_COLUMNS = ["timestamp_utc", "heart_rate", "heart_rate_status"]
STRESS_COLUMNS = ["timestamp_utc", "stress_level_raw", "stress_level", "stress_status"]
SEMANTIC_WINDOW_COLUMNS = [
    "calendarDate",
    "local_utc_offset_minutes",
    "local_utc_offset_source",
    "sleep_start_utc",
    "sleep_end_utc",
    "next_sleep_start_utc",
    "sleep_start_local",
    "sleep_end_local",
    "next_sleep_start_local",
    "sleep_duration_hours",
    "wake_duration_hours",
]


@dataclass(frozen=True)
class MonitoringExtract:
    """Decoded canonical monitoring rows from one FIT message bundle."""

    heart_rate_rows: list[dict[str, Any]]
    stress_rows: list[dict[str, Any]]


@dataclass(frozen=True)
class MonitoringMaterializationSummary:
    """Aggregate summary for a monitoring FIT materialization run."""

    fit_files_seen: int
    monitoring_files_decoded: int
    decode_errors: int
    heart_rate_rows: int
    stress_rows: int
    heart_rate_output_path: Path
    stress_output_path: Path


def resolve_timestamp_16(last_fit_timestamp: int | None, timestamp_16: int) -> int | None:
    """Reconstruct a full FIT timestamp from a 16-bit monitoring timestamp."""
    if last_fit_timestamp is None:
        return None

    candidate = (int(last_fit_timestamp) & ~0xFFFF) | int(timestamp_16)
    if candidate < int(last_fit_timestamp):
        candidate += 0x10000
    return candidate


def classify_heart_rate_value(value: int) -> str:
    """Classify Garmin monitoring heart-rate values for canonical storage."""
    return "valid" if int(value) > 0 else "zero_or_unmeasurable"


def classify_stress_value(value: int) -> tuple[str, int | None]:
    """Classify Garmin stress values without treating status codes as stress."""
    raw_value = int(value)
    if 0 <= raw_value <= 100:
        return "valid", raw_value
    if raw_value < 0:
        return "unmeasurable", None
    return "status_value", None


def _coerce_utc_datetime(value: Any) -> datetime | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _fit_seconds_from_datetime(value: datetime) -> int:
    utc_value = _coerce_utc_datetime(value)
    if utc_value is None:
        raise ValueError("Expected a datetime-like FIT timestamp")
    return int(utc_value.timestamp()) - FIT_EPOCH_S


def _datetime_from_fit_seconds(fit_seconds: int) -> datetime:
    return datetime.fromtimestamp(int(fit_seconds) + FIT_EPOCH_S, tz=timezone.utc)


def _fit_type(messages: Mapping[str, Any]) -> str | None:
    file_ids = messages.get("file_id_mesgs")
    if not isinstance(file_ids, list) or not file_ids:
        return None
    first = file_ids[0]
    return first.get("type") if isinstance(first, Mapping) else None


def is_monitoring_fit_messages(messages: Mapping[str, Any]) -> bool:
    """Return whether a decoded FIT message bundle is a monitoring file."""
    return _fit_type(messages) in {"monitoring_b", "monitoring"}


def extract_monitoring_messages(messages: Mapping[str, Any]) -> MonitoringExtract:
    """Extract canonical HR and stress rows from decoded Garmin FIT messages."""
    heart_rate_rows: list[dict[str, Any]] = []
    stress_rows: list[dict[str, Any]] = []
    last_fit_timestamp: int | None = None

    monitoring_messages = messages.get("monitoring_mesgs", [])
    if isinstance(monitoring_messages, list):
        for record in monitoring_messages:
            if not isinstance(record, Mapping):
                continue

            timestamp = _coerce_utc_datetime(record.get("timestamp"))
            if timestamp is not None:
                last_fit_timestamp = _fit_seconds_from_datetime(timestamp)
            elif "timestamp_16" in record and record.get("timestamp_16") is not None:
                last_fit_timestamp = resolve_timestamp_16(
                    last_fit_timestamp, int(record["timestamp_16"])
                )

            heart_rate = record.get("heart_rate")
            if heart_rate is None or last_fit_timestamp is None:
                continue

            heart_rate_value = int(heart_rate)
            heart_rate_rows.append(
                {
                    "timestamp_utc": _datetime_from_fit_seconds(last_fit_timestamp),
                    "heart_rate": heart_rate_value,
                    "heart_rate_status": classify_heart_rate_value(heart_rate_value),
                }
            )

    stress_messages = messages.get("stress_level_mesgs", [])
    if isinstance(stress_messages, list):
        for record in stress_messages:
            if not isinstance(record, Mapping):
                continue

            timestamp = _coerce_utc_datetime(
                record.get("stress_level_time") or record.get("timestamp")
            )
            raw_value = record.get("stress_level_value")
            if timestamp is None or raw_value is None:
                continue

            stress_raw = int(raw_value)
            stress_status, stress_value = classify_stress_value(stress_raw)
            stress_rows.append(
                {
                    "timestamp_utc": timestamp,
                    "stress_level_raw": stress_raw,
                    "stress_level": stress_value,
                    "stress_status": stress_status,
                }
            )

    return MonitoringExtract(heart_rate_rows=heart_rate_rows, stress_rows=stress_rows)


def _load_fit_sdk() -> Any:
    try:
        import garmin_fit_sdk as fit_sdk
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Monitoring FIT ingest requires the optional package 'garmin-fit-sdk'. "
            "Install project requirements before running ingest-monitoring-fit."
        ) from exc
    return fit_sdk


def _decode_fit_messages(path: Path, fit_sdk: Any) -> Mapping[str, Any]:
    messages, _errors = fit_sdk.Decoder(fit_sdk.Stream.from_file(str(path))).read()
    return messages


def _empty_heart_rate_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_utc": pd.Series(dtype="datetime64[ns, UTC]"),
            "heart_rate": pd.Series(dtype="Int64"),
            "heart_rate_status": pd.Series(dtype="string"),
        }
    )


def _empty_stress_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_utc": pd.Series(dtype="datetime64[ns, UTC]"),
            "stress_level_raw": pd.Series(dtype="Int64"),
            "stress_level": pd.Series(dtype="Int64"),
            "stress_status": pd.Series(dtype="string"),
        }
    )


def normalize_heart_rate_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize a heart-rate table to the canonical monitoring contract."""
    if df.empty:
        return _empty_heart_rate_frame()
    out = df.copy()
    out["timestamp_utc"] = pd.to_datetime(out["timestamp_utc"], errors="coerce", utc=True)
    out["heart_rate"] = pd.to_numeric(out["heart_rate"], errors="coerce").astype("Int64")
    out["heart_rate_status"] = out["heart_rate"].map(
        lambda value: classify_heart_rate_value(int(value)) if pd.notna(value) else pd.NA
    )
    out["heart_rate_status"] = out["heart_rate_status"].astype("string")
    out = out.dropna(subset=["timestamp_utc", "heart_rate"])
    return out.reindex(columns=HEART_RATE_COLUMNS).sort_values("timestamp_utc").reset_index(drop=True)


def normalize_stress_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize a stress table to the canonical monitoring contract."""
    if df.empty:
        return _empty_stress_frame()
    out = df.copy()
    out["timestamp_utc"] = pd.to_datetime(out["timestamp_utc"], errors="coerce", utc=True)
    out["stress_level_raw"] = pd.to_numeric(out["stress_level_raw"], errors="coerce").astype("Int64")
    classified = out["stress_level_raw"].map(
        lambda value: classify_stress_value(int(value)) if pd.notna(value) else (pd.NA, pd.NA)
    )
    out["stress_status"] = classified.map(lambda item: item[0])
    out["stress_level"] = classified.map(lambda item: item[1])
    out["stress_level"] = out["stress_level"].astype("Int64")
    out["stress_status"] = out["stress_status"].astype("string")
    out = out.dropna(subset=["timestamp_utc", "stress_level_raw"])
    return out.reindex(columns=STRESS_COLUMNS).sort_values("timestamp_utc").reset_index(drop=True)


def extract_monitoring_fit_directory(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Decode monitoring FIT files under a Garmin Uploaded Files directory."""
    fit_sdk = _load_fit_sdk()
    fit_paths = sorted(Path(input_dir).rglob("*.fit"))
    heart_rate_rows: list[dict[str, Any]] = []
    stress_rows: list[dict[str, Any]] = []
    monitoring_files_decoded = 0
    decode_errors = 0

    for path in fit_paths:
        try:
            messages = _decode_fit_messages(path, fit_sdk)
        except Exception:
            decode_errors += 1
            continue

        if not is_monitoring_fit_messages(messages):
            continue

        monitoring_files_decoded += 1
        extract = extract_monitoring_messages(messages)
        heart_rate_rows.extend(extract.heart_rate_rows)
        stress_rows.extend(extract.stress_rows)

    summary = {
        "fit_files_seen": len(fit_paths),
        "monitoring_files_decoded": monitoring_files_decoded,
        "decode_errors": decode_errors,
    }
    return (
        normalize_heart_rate_frame(pd.DataFrame(heart_rate_rows)),
        normalize_stress_frame(pd.DataFrame(stress_rows)),
        summary,
    )


def materialize_monitoring_fit(
    input_dir: Path,
    output_dir: Path,
) -> MonitoringMaterializationSummary:
    """Decode monitoring FIT files and write canonical HR/stress parquets."""
    heart_rate_df, stress_df, run_summary = extract_monitoring_fit_directory(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    heart_rate_path = output_dir / "monitoring_heart_rate.parquet"
    stress_path = output_dir / "monitoring_stress.parquet"
    heart_rate_df.to_parquet(heart_rate_path, index=False, engine="pyarrow")
    stress_df.to_parquet(stress_path, index=False, engine="pyarrow")

    return MonitoringMaterializationSummary(
        fit_files_seen=run_summary["fit_files_seen"],
        monitoring_files_decoded=run_summary["monitoring_files_decoded"],
        decode_errors=run_summary["decode_errors"],
        heart_rate_rows=len(heart_rate_df),
        stress_rows=len(stress_df),
        heart_rate_output_path=heart_rate_path,
        stress_output_path=stress_path,
    )


def _epoch_seconds_to_utc(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return pd.to_datetime(numeric, unit="s", errors="coerce", utc=True)


def _parse_garmin_clock_series(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    parsed_numeric = pd.to_datetime(numeric, unit="s", errors="coerce")
    parsed_text = pd.to_datetime(series.where(numeric.isna()), errors="coerce")
    return parsed_numeric.where(parsed_numeric.notna(), parsed_text)


def _offset_minutes_from_pair(local: pd.Series, gmt: pd.Series) -> pd.Series:
    local_ts = _parse_garmin_clock_series(local)
    gmt_ts = _parse_garmin_clock_series(gmt)
    offset = (local_ts - gmt_ts).dt.total_seconds() / 60.0
    return offset.round().astype("Int64")


def derive_local_utc_offsets(daily_df: pd.DataFrame | None) -> pd.DataFrame:
    """Derive per-date local UTC offsets from Garmin local/GMT wellness pairs."""
    columns = ["calendarDate", "local_utc_offset_minutes", "local_utc_offset_source"]
    if daily_df is None or daily_df.empty or "calendarDate" not in daily_df.columns:
        return pd.DataFrame(columns=columns)

    daily = daily_df.copy()
    daily["calendarDate"] = pd.to_datetime(daily["calendarDate"], errors="coerce").dt.normalize()
    daily = daily.dropna(subset=["calendarDate"])
    required = {
        "wellnessStartTimeGmt",
        "wellnessStartTimeLocal",
        "wellnessEndTimeGmt",
        "wellnessEndTimeLocal",
    }
    if not required.issubset(daily.columns):
        offsets = daily[["calendarDate"]].copy()
        offsets["local_utc_offset_minutes"] = pd.Series(pd.NA, index=offsets.index, dtype="Int64")
        offsets["local_utc_offset_source"] = "missing"
        return offsets.drop_duplicates("calendarDate", keep="last").reset_index(drop=True)

    start_offset = _offset_minutes_from_pair(
        daily["wellnessStartTimeLocal"],
        daily["wellnessStartTimeGmt"],
    )
    end_offset = _offset_minutes_from_pair(
        daily["wellnessEndTimeLocal"],
        daily["wellnessEndTimeGmt"],
    )

    rows: list[dict[str, Any]] = []
    for date_value, start_value, end_value in zip(daily["calendarDate"], start_offset, end_offset, strict=False):
        start_valid = pd.notna(start_value)
        end_valid = pd.notna(end_value)
        if start_valid and end_valid and int(start_value) == int(end_value):
            offset = int(start_value)
            source = "start_end_agree"
        elif start_valid and end_valid:
            offset = int(start_value)
            source = "start_end_disagree_using_start"
        elif start_valid:
            offset = int(start_value)
            source = "start_only"
        elif end_valid:
            offset = int(end_value)
            source = "end_only"
        else:
            offset = pd.NA
            source = "missing"
        rows.append(
            {
                "calendarDate": date_value,
                "local_utc_offset_minutes": offset,
                "local_utc_offset_source": source,
            }
        )

    offsets = pd.DataFrame.from_records(rows, columns=columns)
    offsets["local_utc_offset_minutes"] = offsets["local_utc_offset_minutes"].astype("Int64")
    return offsets.drop_duplicates("calendarDate", keep="last").reset_index(drop=True)


def _utc_plus_offset_to_local(utc_values: pd.Series, offsets: pd.Series) -> pd.Series:
    shifted = utc_values + pd.to_timedelta(pd.to_numeric(offsets, errors="coerce"), unit="m")
    if getattr(shifted.dt, "tz", None) is not None:
        return shifted.dt.tz_localize(None)
    return shifted


def build_semantic_sleep_windows(sleep_df: pd.DataFrame, daily_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build complete sleep-end-to-next-sleep semantic windows from sleep rows."""
    required = {"calendarDate", "sleepStartTimestampGMT", "sleepEndTimestampGMT"}
    missing = sorted(required - set(sleep_df.columns))
    if missing:
        raise ValueError(f"Missing sleep columns: {missing}")

    windows = pd.DataFrame(
        {
            "calendarDate": pd.to_datetime(sleep_df["calendarDate"], errors="coerce").dt.normalize(),
            "sleep_start_utc": _epoch_seconds_to_utc(sleep_df["sleepStartTimestampGMT"]),
            "sleep_end_utc": _epoch_seconds_to_utc(sleep_df["sleepEndTimestampGMT"]),
        }
    )
    windows = windows.dropna(subset=["calendarDate", "sleep_start_utc", "sleep_end_utc"])
    windows = windows.sort_values(["sleep_start_utc", "calendarDate"]).drop_duplicates(
        "calendarDate", keep="last"
    )
    windows = windows.sort_values("calendarDate").reset_index(drop=True)
    offsets = derive_local_utc_offsets(daily_df)
    if offsets.empty:
        windows["local_utc_offset_minutes"] = pd.Series(pd.NA, index=windows.index, dtype="Int64")
        windows["local_utc_offset_source"] = "missing"
    else:
        windows = windows.merge(offsets, on="calendarDate", how="left")
        windows["local_utc_offset_minutes"] = windows["local_utc_offset_minutes"].astype("Int64")
        windows["local_utc_offset_source"] = windows["local_utc_offset_source"].fillna("missing")

    windows["next_sleep_start_utc"] = windows["sleep_start_utc"].shift(-1)
    next_offset = windows["local_utc_offset_minutes"].shift(-1)
    windows["sleep_start_local"] = _utc_plus_offset_to_local(
        windows["sleep_start_utc"], windows["local_utc_offset_minutes"]
    )
    windows["sleep_end_local"] = _utc_plus_offset_to_local(
        windows["sleep_end_utc"], windows["local_utc_offset_minutes"]
    )
    windows["next_sleep_start_local"] = _utc_plus_offset_to_local(
        windows["next_sleep_start_utc"], next_offset
    )

    seconds_per_hour = 3600.0
    windows["sleep_duration_hours"] = (
        windows["sleep_end_utc"] - windows["sleep_start_utc"]
    ).dt.total_seconds() / seconds_per_hour
    windows["wake_duration_hours"] = (
        windows["next_sleep_start_utc"] - windows["sleep_end_utc"]
    ).dt.total_seconds() / seconds_per_hour

    valid = (
        (windows["sleep_duration_hours"] > 0)
        & (windows["wake_duration_hours"] > 0)
        & windows["next_sleep_start_utc"].notna()
    )
    return windows.loc[valid, SEMANTIC_WINDOW_COLUMNS].reset_index(drop=True)


def _indexed_by_timestamp(df: pd.DataFrame, timestamp_col: str = "timestamp_utc") -> pd.DataFrame:
    out = df.copy()
    out[timestamp_col] = pd.to_datetime(out[timestamp_col], errors="coerce", utc=True)
    out = out.dropna(subset=[timestamp_col]).sort_values(timestamp_col)
    return out.set_index(timestamp_col, drop=False)


def _time_slice(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if df.empty:
        return df
    subset = df.loc[start:end]
    if subset.empty:
        return subset
    return subset.loc[(subset.index >= start) & (subset.index < end)]


def _series_stats(values: pd.Series, prefix: str) -> dict[str, float | int]:
    numeric = pd.to_numeric(values, errors="coerce").dropna().astype(float)
    record: dict[str, float | int] = {f"{prefix}_valid_count": int(len(numeric))}
    if numeric.empty:
        for suffix in ["mean", "median", "std", "p75", "p90"]:
            record[f"{prefix}_{suffix}"] = np.nan
        return record

    record.update(
        {
            f"{prefix}_mean": float(numeric.mean()),
            f"{prefix}_median": float(numeric.median()),
            f"{prefix}_std": float(numeric.std(ddof=0)),
            f"{prefix}_p75": float(numeric.quantile(0.75)),
            f"{prefix}_p90": float(numeric.quantile(0.90)),
        }
    )
    return record


def _coverage_fraction(valid_count: int, duration_hours: float) -> float:
    expected_points = max(float(duration_hours) * 60.0, 0.0)
    if expected_points <= 0:
        return np.nan
    return float(min(valid_count / expected_points, 1.0))


def _phase_features(
    phase: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    duration_hours: float,
    heart_rate_df: pd.DataFrame,
    stress_df: pd.DataFrame,
) -> dict[str, float | int]:
    hr_subset = _time_slice(heart_rate_df, start, end)
    stress_subset = _time_slice(stress_df, start, end)

    hr_valid = hr_subset.loc[hr_subset["heart_rate_status"] == "valid", "heart_rate"]
    stress_valid = stress_subset.loc[stress_subset["stress_status"] == "valid", "stress_level"]
    stress_unmeasurable_count = int((stress_subset["stress_status"] == "unmeasurable").sum())
    stress_status_value_count = int((stress_subset["stress_status"] == "status_value").sum())
    stress_nonvalid_count = int((stress_subset["stress_status"] != "valid").sum())

    record: dict[str, float | int] = {
        f"{phase}_hr_total_count": int(len(hr_subset)),
        f"{phase}_stress_total_count": int(len(stress_subset)),
        f"{phase}_stress_unmeasurable_count": stress_unmeasurable_count,
        f"{phase}_stress_status_value_count": stress_status_value_count,
        f"{phase}_stress_nonvalid_count": stress_nonvalid_count,
    }
    record.update(_series_stats(hr_valid, f"{phase}_hr"))
    record.update(_series_stats(stress_valid, f"{phase}_stress"))
    record[f"{phase}_hr_coverage_fraction"] = _coverage_fraction(
        int(record[f"{phase}_hr_valid_count"]), duration_hours
    )
    record[f"{phase}_stress_coverage_fraction"] = _coverage_fraction(
        int(record[f"{phase}_stress_valid_count"]), duration_hours
    )
    record[f"{phase}_stress_unmeasurable_fraction"] = (
        stress_unmeasurable_count / len(stress_subset) if len(stress_subset) else np.nan
    )
    record[f"{phase}_stress_status_value_fraction"] = (
        stress_status_value_count / len(stress_subset) if len(stress_subset) else np.nan
    )
    record[f"{phase}_stress_nonvalid_fraction"] = (
        stress_nonvalid_count / len(stress_subset) if len(stress_subset) else np.nan
    )
    return record


def build_monitoring_daily_features(
    heart_rate_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    semantic_windows_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute minimal sleep/wake monitoring features for semantic days."""
    if semantic_windows_df.empty:
        return pd.DataFrame()

    hr = _indexed_by_timestamp(normalize_heart_rate_frame(heart_rate_df))
    stress = _indexed_by_timestamp(normalize_stress_frame(stress_df))
    windows = semantic_windows_df.copy()
    for column in ["sleep_start_utc", "sleep_end_utc", "next_sleep_start_utc"]:
        windows[column] = pd.to_datetime(windows[column], errors="coerce", utc=True)
    windows["calendarDate"] = pd.to_datetime(windows["calendarDate"], errors="coerce").dt.normalize()
    if "local_utc_offset_minutes" not in windows.columns:
        windows["local_utc_offset_minutes"] = pd.Series(pd.NA, index=windows.index, dtype="Int64")
    if "local_utc_offset_source" not in windows.columns:
        windows["local_utc_offset_source"] = "missing"
    for column in ["sleep_start_local", "sleep_end_local", "next_sleep_start_local"]:
        if column not in windows.columns:
            windows[column] = pd.NaT
    required_columns = [
        "calendarDate",
        "sleep_start_utc",
        "sleep_end_utc",
        "next_sleep_start_utc",
        "sleep_duration_hours",
        "wake_duration_hours",
    ]
    windows = windows.dropna(subset=required_columns).sort_values("calendarDate")

    records: list[dict[str, Any]] = []
    for row in windows.itertuples(index=False):
        record: dict[str, Any] = {
            "calendarDate": row.calendarDate,
            "local_utc_offset_minutes": row.local_utc_offset_minutes,
            "local_utc_offset_source": row.local_utc_offset_source,
            "sleep_start_utc": row.sleep_start_utc,
            "sleep_end_utc": row.sleep_end_utc,
            "next_sleep_start_utc": row.next_sleep_start_utc,
            "sleep_start_local": row.sleep_start_local,
            "sleep_end_local": row.sleep_end_local,
            "next_sleep_start_local": row.next_sleep_start_local,
            "sleep_duration_hours": float(row.sleep_duration_hours),
            "wake_duration_hours": float(row.wake_duration_hours),
        }
        record.update(
            _phase_features(
                "sleep",
                row.sleep_start_utc,
                row.sleep_end_utc,
                float(row.sleep_duration_hours),
                hr,
                stress,
            )
        )
        record.update(
            _phase_features(
                "wake",
                row.sleep_end_utc,
                row.next_sleep_start_utc,
                float(row.wake_duration_hours),
                hr,
                stress,
            )
        )
        records.append(record)

    return pd.DataFrame.from_records(records).sort_values("calendarDate").reset_index(drop=True)


def build_monitoring_foundation_summary_markdown(
    heart_rate_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    semantic_windows_df: pd.DataFrame,
    feature_df: pd.DataFrame,
) -> str:
    """Build a privacy-safe aggregate monitoring foundation report."""
    hr = normalize_heart_rate_frame(heart_rate_df)
    stress = normalize_stress_frame(stress_df)

    def _date_range(df: pd.DataFrame) -> str:
        if df.empty:
            return "n/a"
        dates = pd.to_datetime(df["timestamp_utc"], errors="coerce", utc=True).dropna()
        if dates.empty:
            return "n/a"
        return f"{dates.min().date()} to {dates.max().date()}"

    stress_status_counts = stress["stress_status"].value_counts(dropna=False).to_dict()
    coverage_lines: list[str] = []
    for column in [
        "sleep_hr_coverage_fraction",
        "wake_hr_coverage_fraction",
        "sleep_stress_coverage_fraction",
        "wake_stress_coverage_fraction",
    ]:
        if column in feature_df.columns and not feature_df.empty:
            value = pd.to_numeric(feature_df[column], errors="coerce").median()
            coverage_lines.append(f"- `{column}` median: `{value:.3f}`")

    stress_diagnostic_lines: list[str] = []
    for column in [
        "sleep_stress_unmeasurable_fraction",
        "sleep_stress_status_value_fraction",
        "sleep_stress_nonvalid_fraction",
        "wake_stress_unmeasurable_fraction",
        "wake_stress_status_value_fraction",
        "wake_stress_nonvalid_fraction",
    ]:
        if column in feature_df.columns and not feature_df.empty:
            value = pd.to_numeric(feature_df[column], errors="coerce").median()
            stress_diagnostic_lines.append(f"- `{column}` median: `{value:.3f}`")

    offset_source_counts = (
        semantic_windows_df["local_utc_offset_source"].value_counts(dropna=False).to_dict()
        if "local_utc_offset_source" in semantic_windows_df.columns and not semantic_windows_df.empty
        else {}
    )
    offset_rows = (
        int(pd.to_numeric(semantic_windows_df["local_utc_offset_minutes"], errors="coerce").notna().sum())
        if "local_utc_offset_minutes" in semantic_windows_df.columns and not semantic_windows_df.empty
        else 0
    )

    lines = [
        "# Monitoring Foundation Summary",
        "",
        "This report summarizes the local minute-level monitoring foundation built from Garmin FIT monitoring files. It contains only aggregate counts and feature-level diagnostics.",
        "",
        "## Outputs",
        "",
        "- `data/processed/monitoring_heart_rate.parquet`",
        "- `data/processed/monitoring_stress.parquet`",
        "- `data/processed/semantic_sleep_windows.parquet`",
        "- `data/processed/monitoring_daily_features.parquet`",
        "",
        "## Canonical Tables",
        "",
        f"- Heart-rate rows: `{len(hr):,}`",
        f"- Heart-rate date range: `{_date_range(hr)}`",
        f"- Stress rows: `{len(stress):,}`",
        f"- Stress date range: `{_date_range(stress)}`",
        f"- Stress status counts: `{stress_status_counts}`",
        "",
        "## Semantic Windows",
        "",
        f"- Complete semantic sleep/wake windows: `{len(semantic_windows_df):,}`",
    ]

    if not semantic_windows_df.empty:
        sleep_median = pd.to_numeric(
            semantic_windows_df["sleep_duration_hours"], errors="coerce"
        ).median()
        wake_median = pd.to_numeric(semantic_windows_df["wake_duration_hours"], errors="coerce").median()
        lines.extend(
            [
                f"- Median sleep duration hours: `{sleep_median:.2f}`",
                f"- Median wake duration hours: `{wake_median:.2f}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Local-Time Offset Metadata",
            "",
            f"- Windows with local UTC offset: `{offset_rows:,}`",
            f"- Local UTC offset source counts: `{offset_source_counts}`",
            "",
            "## Baseline Features",
            "",
            f"- Feature rows: `{len(feature_df):,}`",
            "",
            "## Coverage Diagnostics",
            "",
        ]
    )
    lines.extend(coverage_lines or ["- No coverage diagnostics available."])
    lines.extend(
        [
            "",
            "## Stress Status Diagnostics",
            "",
        ]
    )
    lines.extend(stress_diagnostic_lines or ["- No stress status diagnostics available."])
    lines.extend(
        [
            "",
            "## Scope Notes",
            "",
            "- Stress values outside `0..100` are preserved as raw status values and excluded from numeric stress metrics.",
            "- This packet intentionally stops at HR/stress monitoring, semantic windows, coverage diagnostics, and a minimal baseline feature table.",
            "- Activity FIT files, movement monitoring, unknown FIT message families, cluster labels, and sleep-rhythm claims remain out of scope.",
            "",
        ]
    )
    return "\n".join(lines)
