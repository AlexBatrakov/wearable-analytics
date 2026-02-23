from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

import garmin_analytics.cli as cli_module
from garmin_analytics.cli import app


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow")


def test_build_daily_merges_sleep_and_preserves_uds_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_module, "get_processed_dir", lambda: tmp_path)

    uds_df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "totalSteps": [1000, 2000, 3000],
        }
    )
    sleep_df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-03"],
            "sleepOverallScore": [80, 75],
        }
    )

    _write_parquet(uds_df, tmp_path / "daily_uds.parquet")
    _write_parquet(sleep_df, tmp_path / "sleep.parquet")

    runner = CliRunner()
    result = runner.invoke(app, ["build-daily"])

    assert result.exit_code == 0, result.output
    out_path = tmp_path / "daily.parquet"
    assert out_path.exists()

    daily = pd.read_parquet(out_path)
    assert len(daily) == len(uds_df)
    assert list(pd.to_datetime(daily["calendarDate"]).dt.strftime("%Y-%m-%d")) == [
        "2025-01-01",
        "2025-01-02",
        "2025-01-03",
    ]
    assert int(daily["sleepOverallScore"].notna().sum()) == 2
    assert pd.isna(daily.loc[1, "sleepOverallScore"])


@pytest.mark.parametrize("dup_in", ["daily_uds.parquet", "sleep.parquet"])
def test_build_daily_fails_fast_on_duplicate_calendar_date(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dup_in: str,
) -> None:
    monkeypatch.setattr(cli_module, "get_processed_dir", lambda: tmp_path)

    uds_df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02"],
            "totalSteps": [1000, 2000],
        }
    )
    sleep_df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02"],
            "sleepOverallScore": [80, 70],
        }
    )

    if dup_in == "daily_uds.parquet":
        uds_df = pd.concat([uds_df, uds_df.iloc[[1]]], ignore_index=True)
    else:
        sleep_df = pd.concat([sleep_df, sleep_df.iloc[[1]]], ignore_index=True)

    _write_parquet(uds_df, tmp_path / "daily_uds.parquet")
    _write_parquet(sleep_df, tmp_path / "sleep.parquet")

    runner = CliRunner()
    result = runner.invoke(app, ["build-daily"])

    assert result.exit_code == 1
    assert "duplicate calendarDate" in result.output
    assert not (tmp_path / "daily.parquet").exists()
