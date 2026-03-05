from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from garmin_analytics.util.io import get_interim_dir, get_processed_dir


def _pick_existing_path(*candidates: Path) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return None


def _normalize_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def _coalesce_numeric(df: pd.DataFrame, candidates: tuple[str, ...]) -> pd.Series:
    out = pd.Series(pd.NA, index=df.index, dtype="Float64")
    for column in candidates:
        if column not in df.columns:
            continue
        parsed = pd.to_numeric(df[column], errors="coerce")
        out = out.where(out.notna(), parsed)
    return out


def _build_daily_extract(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["calendar_date"] = _normalize_date(df["calendarDate"])
    out["total_steps"] = pd.to_numeric(df.get("totalSteps"), errors="coerce")
    out["total_distance_meters"] = pd.to_numeric(df.get("totalDistanceMeters"), errors="coerce")
    out["active_kilocalories"] = pd.to_numeric(df.get("activeKilocalories"), errors="coerce")
    out["awake_average_stress_level"] = _coalesce_numeric(
        df,
        ("awakeAverageStressLevel", "allDayStress_AWAKE_averageStressLevel"),
    )
    out["max_heart_rate"] = pd.to_numeric(df.get("maxHeartRate"), errors="coerce")
    out["body_battery_lowest"] = _coalesce_numeric(
        df,
        ("bodyBatteryLowest", "bodyBatteryStat_LOWEST"),
    )
    return out.sort_values("calendar_date").drop_duplicates(subset=["calendar_date"])


def _build_sleep_extract(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["calendar_date"] = _normalize_date(df["calendarDate"])
    out["sleep_recovery_score"] = pd.to_numeric(df.get("sleepRecoveryScore"), errors="coerce")
    out["sleep_overall_score"] = pd.to_numeric(df.get("sleepOverallScore"), errors="coerce")
    out["sleep_quality_score"] = pd.to_numeric(df.get("sleepQualityScore"), errors="coerce")
    out["avg_sleep_stress"] = _coalesce_numeric(
        df,
        ("avgSleepStress", "sleepAverageStressLevel"),
    )
    out["sleep_start_ts_gmt"] = pd.to_numeric(df.get("sleepStartTimestampGMT"), errors="coerce")
    out["sleep_end_ts_gmt"] = pd.to_numeric(df.get("sleepEndTimestampGMT"), errors="coerce")
    return out.sort_values("calendar_date").drop_duplicates(subset=["calendar_date"])


def _build_quality_extract(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["calendar_date"] = _normalize_date(df["calendarDate"])
    out["day_quality_label_strict"] = df.get("day_quality_label_strict")
    out["valid_day_strict"] = df.get("valid_day_strict")
    out["corrupted_stress_only_day"] = df.get("corrupted_stress_only_day")
    return out.sort_values("calendar_date").drop_duplicates(subset=["calendar_date"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export compact CSV extracts for PostgreSQL showcase loading."
    )
    parser.add_argument(
        "--daily-path",
        type=Path,
        default=None,
        help="Daily source parquet (default: daily_sanitized.parquet, fallback: daily.parquet)",
    )
    parser.add_argument(
        "--sleep-path",
        type=Path,
        default=None,
        help="Sleep source parquet (default: sleep_sanitized.parquet, fallback: sleep.parquet)",
    )
    parser.add_argument(
        "--quality-path",
        type=Path,
        default=None,
        help="Quality source parquet (default: daily_quality.parquet; fallback: daily source)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=get_interim_dir() / "postgres_showcase",
        help="Output directory for CSV extracts.",
    )
    args = parser.parse_args()

    processed_dir = get_processed_dir()

    daily_path = args.daily_path or _pick_existing_path(
        processed_dir / "daily_sanitized.parquet",
        processed_dir / "daily.parquet",
    )
    if daily_path is None or not daily_path.exists():
        raise FileNotFoundError(
            "Missing daily parquet source. Expected daily_sanitized.parquet or daily.parquet."
        )

    sleep_path = args.sleep_path or _pick_existing_path(
        processed_dir / "sleep_sanitized.parquet",
        processed_dir / "sleep.parquet",
    )
    quality_path = args.quality_path or _pick_existing_path(processed_dir / "daily_quality.parquet")

    daily_df = pd.read_parquet(daily_path)
    sleep_df = pd.read_parquet(sleep_path) if sleep_path is not None and sleep_path.exists() else daily_df
    quality_df = pd.read_parquet(quality_path) if quality_path is not None and quality_path.exists() else daily_df

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    daily_csv = out_dir / "daily.csv"
    sleep_csv = out_dir / "sleep.csv"
    quality_csv = out_dir / "quality.csv"

    _build_daily_extract(daily_df).to_csv(daily_csv, index=False)
    _build_sleep_extract(sleep_df).to_csv(sleep_csv, index=False)
    _build_quality_extract(quality_df).to_csv(quality_csv, index=False)

    print(f"Wrote {daily_csv}")
    print(f"Wrote {sleep_csv}")
    print(f"Wrote {quality_csv}")


if __name__ == "__main__":
    main()
