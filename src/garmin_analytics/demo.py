from __future__ import annotations

from pathlib import Path

import pandas as pd


DEMO_NUMERIC_COLUMNS: tuple[str, ...] = (
    "totalSteps",
    "totalDistanceMeters",
    "activeKilocalories",
    "restingHeartRate",
    "minHeartRate",
    "maxHeartRate",
    "stressTotalDurationSeconds",
    "stressAwakeDurationSeconds",
    "allDayStress_TOTAL_totalDuration",
    "allDayStress_AWAKE_totalDuration",
    "bodyBatteryStartOfDay",
    "bodyBatteryEndOfDay",
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
    "awakeAverageStressLevel",
)


def _default_demo_csv_path() -> Path:
    return Path(__file__).resolve().parents[2] / "examples" / "public_demo" / "daily_sanitized_sample.csv"


def _normalize_demo_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "calendarDate" not in out.columns:
        raise ValueError("Demo sample is missing required column: calendarDate")

    out["calendarDate"] = pd.to_datetime(out["calendarDate"], errors="raise").dt.normalize()

    for col in DEMO_NUMERIC_COLUMNS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    for col in ("sleepStartTimestampGMT", "sleepEndTimestampGMT"):
        if col in out.columns:
            parsed = pd.to_datetime(out[col], errors="coerce", utc=True)
            epoch_seconds = pd.Series(pd.NA, index=out.index, dtype="Int64")
            mask = parsed.notna()
            epoch_seconds.loc[mask] = (
                parsed.loc[mask].astype("int64") // 1_000_000_000
            ).astype("int64")
            out[col] = epoch_seconds

    return out.convert_dtypes()


def write_public_demo_dataset(
    *,
    sample_csv_path: Path | None = None,
    output_dir: Path,
) -> Path:
    """Write the committed public sample as daily_sanitized.parquet."""
    csv_path = sample_csv_path or _default_demo_csv_path()
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing demo sample CSV: {csv_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path)
    demo_df = _normalize_demo_frame(df)

    output_path = output_dir / "daily_sanitized.parquet"
    demo_df.to_parquet(output_path, index=False, engine="pyarrow")
    return output_path
