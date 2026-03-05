from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from garmin_analytics.sql import build_sql_mart, run_sql_directory

duckdb = pytest.importorskip("duckdb")


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow")


def _make_daily_frame() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=14, freq="D")
    return pd.DataFrame(
        {
            "calendarDate": dates,
            "totalSteps": [3000 + i * 400 for i in range(len(dates))],
            "totalDistanceMeters": [2500 + i * 300 for i in range(len(dates))],
            "activeKilocalories": [350 + i * 5 for i in range(len(dates))],
            "awakeAverageStressLevel": [42 + (i % 7) * 3 for i in range(len(dates))],
            "maxHeartRate": [120 + (i % 5) * 4 for i in range(len(dates))],
            "bodyBatteryLowest": [25 + (i % 6) for i in range(len(dates))],
        }
    )


def _make_sleep_frame() -> pd.DataFrame:
    dates = pd.date_range("2025-01-02", periods=14, freq="D")
    return pd.DataFrame(
        {
            "calendarDate": dates,
            "sleepRecoveryScore": [70 + (i % 8) for i in range(len(dates))],
            "sleepOverallScore": [72 + (i % 7) for i in range(len(dates))],
            "sleepQualityScore": [68 + (i % 9) for i in range(len(dates))],
            "avgSleepStress": [12 + (i % 5) for i in range(len(dates))],
            "sleepStartTimestampGMT": [1_735_776_000 + i * 86_400 for i in range(len(dates))],
            "sleepEndTimestampGMT": [1_735_804_800 + i * 86_400 for i in range(len(dates))],
        }
    )


def _make_sleep_frame_alias_only() -> pd.DataFrame:
    frame = _make_sleep_frame().drop(columns=["avgSleepStress"]).copy()
    frame["sleepAverageStressLevel"] = [12 + (i % 5) for i in range(len(frame))]
    return frame


def _make_quality_frame() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=14, freq="D")
    labels = ["good", "good", "partial", "good", "bad", "good", "good"]
    return pd.DataFrame(
        {
            "calendarDate": dates,
            "day_quality_label_strict": [labels[i % len(labels)] for i in range(len(dates))],
            "valid_day_strict": [i % 5 != 4 for i in range(len(dates))],
            "corrupted_stress_only_day": [i % 11 == 0 for i in range(len(dates))],
        }
    )


def test_build_sql_mart_creates_expected_tables_and_views(tmp_path: Path) -> None:
    daily_path = tmp_path / "daily_sanitized.parquet"
    sleep_path = tmp_path / "sleep_sanitized.parquet"
    quality_path = tmp_path / "daily_quality.parquet"
    db_path = tmp_path / "analytics.duckdb"

    _write_parquet(_make_daily_frame(), daily_path)
    _write_parquet(_make_sleep_frame(), sleep_path)
    _write_parquet(_make_quality_frame(), quality_path)

    summary = build_sql_mart(
        db_path=db_path,
        daily_path=daily_path,
        sleep_path=sleep_path,
        quality_path=quality_path,
    )

    assert summary.db_path == db_path
    assert summary.fact_daily_rows == 14
    assert summary.fact_sleep_rows == 14
    assert summary.fact_quality_rows == 14
    assert summary.day_to_next_sleep_rows == 14

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        day_to_next = conn.execute(
            """
            SELECT day_date, next_sleep_date, nextsleep_recovery_score
            FROM vw_day_to_next_sleep
            ORDER BY day_date
            LIMIT 1
            """
        ).fetchone()
        assert str(day_to_next[0]) == "2025-01-01"
        assert str(day_to_next[1]) == "2025-01-02"
        assert float(day_to_next[2]) == 70.0
    finally:
        conn.close()


def test_build_sql_mart_can_fallback_to_daily_columns(tmp_path: Path) -> None:
    daily_path = tmp_path / "daily_sanitized.parquet"
    db_path = tmp_path / "analytics.duckdb"

    df = _make_daily_frame().copy()
    df["sleepRecoveryScore"] = [65 + (i % 6) for i in range(len(df))]
    df["sleepOverallScore"] = [70 + (i % 5) for i in range(len(df))]
    df["day_quality_label_strict"] = ["good"] * len(df)
    df["valid_day_strict"] = [True] * len(df)
    df["corrupted_stress_only_day"] = [False] * len(df)
    _write_parquet(df, daily_path)

    summary = build_sql_mart(
        db_path=db_path,
        daily_path=daily_path,
        sleep_path=None,
        quality_path=None,
    )

    assert summary.sleep_source is None
    assert summary.quality_source is None
    assert summary.fact_sleep_rows == len(df)
    assert summary.fact_quality_rows == len(df)


def test_build_sql_mart_uses_awake_stress_fallback_column(tmp_path: Path) -> None:
    daily_path = tmp_path / "daily_sanitized.parquet"
    sleep_path = tmp_path / "sleep_sanitized.parquet"
    quality_path = tmp_path / "daily_quality.parquet"
    db_path = tmp_path / "analytics.duckdb"

    daily = _make_daily_frame().rename(
        columns={"awakeAverageStressLevel": "allDayStress_AWAKE_averageStressLevel"}
    )
    _write_parquet(daily, daily_path)
    _write_parquet(_make_sleep_frame(), sleep_path)
    _write_parquet(_make_quality_frame(), quality_path)

    build_sql_mart(
        db_path=db_path,
        daily_path=daily_path,
        sleep_path=sleep_path,
        quality_path=quality_path,
    )

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        count_non_null = conn.execute(
            "SELECT COUNT(day_awake_average_stress) FROM vw_day_to_next_sleep"
        ).fetchone()[0]
    finally:
        conn.close()

    assert int(count_non_null) == len(daily)


def test_build_sql_mart_uses_sleep_stress_fallback_column(tmp_path: Path) -> None:
    daily_path = tmp_path / "daily_sanitized.parquet"
    sleep_path = tmp_path / "sleep_sanitized.parquet"
    quality_path = tmp_path / "daily_quality.parquet"
    db_path = tmp_path / "analytics.duckdb"

    _write_parquet(_make_daily_frame(), daily_path)
    _write_parquet(_make_sleep_frame_alias_only(), sleep_path)
    _write_parquet(_make_quality_frame(), quality_path)

    build_sql_mart(
        db_path=db_path,
        daily_path=daily_path,
        sleep_path=sleep_path,
        quality_path=quality_path,
    )

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        count_non_null = conn.execute(
            "SELECT COUNT(nextsleep_avg_sleep_stress) FROM vw_day_to_next_sleep"
        ).fetchone()[0]
    finally:
        conn.close()

    assert int(count_non_null) == 14


def test_run_sql_directory_smoke_on_portfolio_queries(tmp_path: Path) -> None:
    daily_path = tmp_path / "daily_sanitized.parquet"
    sleep_path = tmp_path / "sleep_sanitized.parquet"
    quality_path = tmp_path / "daily_quality.parquet"
    db_path = tmp_path / "analytics.duckdb"

    _write_parquet(_make_daily_frame(), daily_path)
    _write_parquet(_make_sleep_frame(), sleep_path)
    _write_parquet(_make_quality_frame(), quality_path)

    build_sql_mart(
        db_path=db_path,
        daily_path=daily_path,
        sleep_path=sleep_path,
        quality_path=quality_path,
    )

    query_dir = Path(__file__).resolve().parents[1] / "sql" / "duckdb"
    out_dir = tmp_path / "sql_out"

    results = run_sql_directory(db_path=db_path, query_dir=query_dir, output_dir=out_dir)

    assert len(results) >= 10
    for result in results:
        assert result.output_csv_path.exists()
        assert result.columns >= 1


def test_run_sql_directory_handles_sleep_stress_alias_only(tmp_path: Path) -> None:
    daily_path = tmp_path / "daily_sanitized.parquet"
    sleep_path = tmp_path / "sleep_sanitized.parquet"
    quality_path = tmp_path / "daily_quality.parquet"
    db_path = tmp_path / "analytics.duckdb"

    _write_parquet(_make_daily_frame(), daily_path)
    _write_parquet(_make_sleep_frame_alias_only(), sleep_path)
    _write_parquet(_make_quality_frame(), quality_path)

    build_sql_mart(
        db_path=db_path,
        daily_path=daily_path,
        sleep_path=sleep_path,
        quality_path=quality_path,
    )

    query_dir = Path(__file__).resolve().parents[1] / "sql" / "duckdb"
    out_dir = tmp_path / "sql_out_alias"
    results = run_sql_directory(db_path=db_path, query_dir=query_dir, output_dir=out_dir)

    query_07 = next(result for result in results if result.query_path.name == "07_sleep_duration_bands.sql")
    assert query_07.rows >= 1
