from __future__ import annotations

from pathlib import Path

import pandas as pd

from garmin_analytics.demo import write_public_demo_dataset


def test_write_public_demo_dataset_creates_parquet(tmp_path) -> None:
    output_path = write_public_demo_dataset(output_dir=tmp_path)

    assert output_path == tmp_path / "daily_sanitized.parquet"
    assert output_path.exists()

    df = pd.read_parquet(output_path)
    assert len(df) == 12
    assert "calendarDate" in df.columns
    assert "totalSteps" in df.columns
    assert "sleepOverallScore" in df.columns
    assert str(df["calendarDate"].dtype).startswith("datetime64")

    sample_root = Path(__file__).resolve().parents[1] / "examples" / "public_demo"
    assert (sample_root / "daily_sanitized_sample.csv").exists()
