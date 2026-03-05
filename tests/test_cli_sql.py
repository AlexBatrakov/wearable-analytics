from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

import garmin_analytics.cli as cli_module
from garmin_analytics.cli import app

pytest.importorskip("duckdb")


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow")


def _seed_sources(processed_dir: Path) -> None:
    daily = pd.DataFrame(
        {
            "calendarDate": pd.date_range("2025-01-01", periods=5, freq="D"),
            "totalSteps": [5000, 6200, 7100, 4300, 8200],
            "totalDistanceMeters": [3800, 4300, 5100, 3000, 6000],
            "activeKilocalories": [380, 420, 470, 340, 520],
            "awakeAverageStressLevel": [45, 52, 60, 48, 55],
            "maxHeartRate": [124, 132, 140, 128, 135],
            "bodyBatteryLowest": [28, 25, 23, 30, 24],
        }
    )
    sleep = pd.DataFrame(
        {
            "calendarDate": pd.date_range("2025-01-02", periods=5, freq="D"),
            "sleepRecoveryScore": [72, 70, 68, 75, 73],
            "sleepOverallScore": [74, 72, 70, 76, 75],
            "sleepQualityScore": [73, 71, 69, 77, 74],
            "avgSleepStress": [14, 16, 18, 13, 15],
            "sleepStartTimestampGMT": [1_735_776_000 + i * 86_400 for i in range(5)],
            "sleepEndTimestampGMT": [1_735_804_800 + i * 86_400 for i in range(5)],
        }
    )
    quality = pd.DataFrame(
        {
            "calendarDate": pd.date_range("2025-01-01", periods=5, freq="D"),
            "day_quality_label_strict": ["good", "good", "partial", "good", "bad"],
            "valid_day_strict": [True, True, False, True, False],
            "corrupted_stress_only_day": [False, False, False, False, True],
        }
    )

    _write_parquet(daily, processed_dir / "daily_sanitized.parquet")
    _write_parquet(sleep, processed_dir / "sleep_sanitized.parquet")
    _write_parquet(quality, processed_dir / "daily_quality.parquet")


@pytest.mark.usefixtures("monkeypatch")
def test_build_sql_mart_command_creates_duckdb(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processed_dir = tmp_path / "processed"
    _seed_sources(processed_dir)

    monkeypatch.setattr(cli_module, "get_processed_dir", lambda: processed_dir)

    runner = CliRunner()
    result = runner.invoke(app, ["build-sql-mart"])

    assert result.exit_code == 0, result.output
    assert (processed_dir / "analytics.duckdb").exists()
    assert "fact_daily" in result.output


@pytest.mark.usefixtures("monkeypatch")
def test_run_sql_portfolio_command_exports_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processed_dir = tmp_path / "processed"
    reports_dir = tmp_path / "reports"
    _seed_sources(processed_dir)

    monkeypatch.setattr(cli_module, "get_processed_dir", lambda: processed_dir)
    monkeypatch.setattr(cli_module, "get_repo_root", lambda: tmp_path)

    query_dir = Path(__file__).resolve().parents[1] / "sql" / "duckdb"
    runner = CliRunner()

    build_result = runner.invoke(app, ["build-sql-mart", "--db-path", str(processed_dir / "analytics.duckdb")])
    assert build_result.exit_code == 0, build_result.output

    run_result = runner.invoke(
        app,
        [
            "run-sql-portfolio",
            "--db-path",
            str(processed_dir / "analytics.duckdb"),
            "--query-dir",
            str(query_dir),
            "--out-dir",
            str(reports_dir / "sql" / "duckdb"),
        ],
    )

    assert run_result.exit_code == 0, run_result.output
    out_files = sorted((reports_dir / "sql" / "duckdb").glob("*.csv"))
    assert len(out_files) >= 10
