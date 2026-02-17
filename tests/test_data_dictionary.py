from __future__ import annotations

import json

import pandas as pd

from garmin_analytics.reports.data_dictionary import build_data_dictionary


def test_data_dictionary_stats_and_inference() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "totalDistanceMeters": [1000, 2000, None],
            "deepSleepSeconds": [3600, 1800, 5400],
            "averageSPO2": [98, 96, 94],
            "restingHeartRateTimestamp": [1685138400000, None, 1685311200000],
            "durationInMilliseconds": [86400000, 7200000, None],
            "hydration_valueInML": [500, None, 250],
            "respiration_avgWakingRespirationValue": [14, 16, None],
            "note": ["a", None, "b"],
        }
    )

    dd = build_data_dictionary(df, max_sample_values=2)

    distance_row = dd[dd["column"] == "totalDistanceMeters"].iloc[0]
    assert distance_row["missing_pct"] == (1 / 3) * 100
    assert distance_row["min"] == 1000.0
    assert distance_row["max"] == 2000.0
    assert distance_row["inferred_unit"] == "Meters"

    sleep_row = dd[dd["column"] == "deepSleepSeconds"].iloc[0]
    assert sleep_row["inferred_unit"] == "Seconds"

    spo2_row = dd[dd["column"] == "averageSPO2"].iloc[0]
    assert spo2_row["inferred_unit"] == "percent"

    hr_ts_row = dd[dd["column"] == "restingHeartRateTimestamp"].iloc[0]
    assert hr_ts_row["inferred_unit"] == "ms"

    dur_row = dd[dd["column"] == "durationInMilliseconds"].iloc[0]
    assert dur_row["inferred_unit"] == "Milliseconds"

    hyd_row = dd[dd["column"] == "hydration_valueInML"].iloc[0]
    assert hyd_row["inferred_unit"] == "mL"

    resp_row = dd[dd["column"] == "respiration_avgWakingRespirationValue"].iloc[0]
    assert resp_row["inferred_unit"] == "brpm"

    note_row = dd[dd["column"] == "note"].iloc[0]
    examples = json.loads(note_row["example_values"])
    assert len(examples) <= 2


def test_timestamp_missingness_and_nonnull_guard() -> None:
    df = pd.DataFrame(
        {
            "sleepStartTimestampGMT": ["2023-05-27T00:48:00.0", None],
            "sleepEndTimestampGMT": [None, "2023-05-27T08:42:00.0"],
        }
    )

    dd = build_data_dictionary(df, max_sample_values=2)
    start_row = dd[dd["column"] == "sleepStartTimestampGMT"].iloc[0]
    end_row = dd[dd["column"] == "sleepEndTimestampGMT"].iloc[0]

    assert start_row["missing_count"] == 1
    assert end_row["missing_count"] == 1
    assert start_row["missing_pct"] < 100
    assert end_row["missing_pct"] < 100