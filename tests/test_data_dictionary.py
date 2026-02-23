from __future__ import annotations

import json

import pandas as pd

from garmin_analytics.reports.data_dictionary import (
    build_data_dictionary,
    build_markdown_report,
    write_dictionary_reports,
)


def test_data_dictionary_stats_and_inference() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "totalDistanceMeters": [1000, 2000, None],
            "stepsMaybeZero": [0, 100, None],
            "constantMetric": [5, 5, None],
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
    assert distance_row["non_null_pct"] == (2 / 3) * 100
    assert distance_row["missing_pct"] == (1 / 3) * 100
    assert distance_row["min"] == 1000.0
    assert distance_row["p05"] == 1050.0
    assert distance_row["p25"] == 1250.0
    assert distance_row["max"] == 2000.0
    assert distance_row["p75"] == 1750.0
    assert distance_row["p95"] == 1950.0
    assert distance_row["inferred_unit"] == "Meters"
    assert bool(distance_row["is_constant"]) is False
    assert distance_row["zero_pct"] == 0.0
    assert distance_row["first_non_null_date"] == "2025-01-01"
    assert distance_row["last_non_null_date"] == "2025-01-02"
    assert distance_row["coverage_span_days"] == 2
    assert distance_row["coverage_within_span_pct"] == 100.0
    assert bool(distance_row["used_in_eda"]) is True
    assert distance_row["analysis_priority"] in {"high", "medium", "low"}

    zero_row = dd[dd["column"] == "stepsMaybeZero"].iloc[0]
    assert zero_row["zero_pct"] == 50.0
    assert bool(zero_row["is_constant"]) is False

    const_row = dd[dd["column"] == "constantMetric"].iloc[0]
    assert bool(const_row["is_constant"]) is True
    assert const_row["zero_pct"] == 0.0

    sleep_row = dd[dd["column"] == "deepSleepSeconds"].iloc[0]
    assert sleep_row["inferred_unit"] == "Seconds"

    spo2_row = dd[dd["column"] == "averageSPO2"].iloc[0]
    assert spo2_row["inferred_unit"] == "percent"

    spo2_hr_row = dd[dd["column"] == "spo2SleepAverageHR"].iloc[0] if "spo2SleepAverageHR" in dd["column"].values else None
    if spo2_hr_row is not None:
        assert spo2_hr_row["inferred_unit"] == "bpm"

    hr_ts_row = dd[dd["column"] == "restingHeartRateTimestamp"].iloc[0]
    assert hr_ts_row["inferred_unit"] == "ms"

    dur_row = dd[dd["column"] == "durationInMilliseconds"].iloc[0]
    assert dur_row["inferred_unit"] == "Milliseconds"

    hyd_row = dd[dd["column"] == "hydration_valueInML"].iloc[0]
    assert hyd_row["inferred_unit"] == "mL"

    resp_row = dd[dd["column"] == "respiration_avgWakingRespirationValue"].iloc[0]
    assert resp_row["inferred_unit"] == "brpm"
    assert bool(resp_row["candidate_model_feature"]) is True

    note_row = dd[dd["column"] == "note"].iloc[0]
    examples = json.loads(note_row["example_values"])
    assert len(examples) <= 2

    # Curated annotations should be present for quality-related columns.
    sleep_start_row = dd[dd["column"] == "calendarDate"].iloc[0]
    assert bool(sleep_start_row["used_in_quality"]) is False


def test_markdown_report_includes_decision_sections() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "totalSteps": [1000, None, 2000],
            "stressTotalDurationSeconds": [80000, None, 72000],
            "bodyBatteryEndOfDay": [20, 30, None],
            "sleepStartTimestampGMT": [1704067200, None, 1704236400],
            "sleepEndTimestampGMT": [1704096000, None, 1704265200],
            "sleepOverallScore": [80, None, 70],
        }
    )
    dd = build_data_dictionary(df, max_sample_values=2)
    md = build_markdown_report(dd, df)

    assert "## Executive summary" in md
    assert "## Key analysis signals" in md
    assert "## Quality-relevant columns" in md
    assert "## Quality-readiness rationale" in md
    assert "totalSteps" in md
    assert "stressTotalDurationSeconds" in md


def test_markdown_report_warns_on_identifier_like_columns() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01"],
            "uuid": ["99e8b35af9c44d238186246e83e97d65"],
            "totalSteps": [1000],
        }
    )
    dd = build_data_dictionary(df, max_sample_values=2)
    md = build_markdown_report(dd, df)

    assert "WARNING" in md
    assert "uuid" in md


def test_markdown_summary_mode_omits_group_appendix(tmp_path) -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02"],
            "totalSteps": [1000, 2000],
            "sleepStartTimestampGMT": [1704067200, None],
            "sleepEndTimestampGMT": [1704096000, None],
        }
    )
    dd = build_data_dictionary(df, max_sample_values=2)

    md_summary = build_markdown_report(dd, df, mode="summary")
    assert "## Key analysis signals" in md_summary
    assert "## Missingness summary (top 20)" in md_summary
    assert "## Columns by group" not in md_summary

    csv_path, full_md, summary_md = write_dictionary_reports(dd, df, tmp_path, markdown_mode="both")
    assert csv_path.exists()
    assert full_md is not None and full_md.exists()
    assert summary_md is not None and summary_md.exists()


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
    assert start_row["first_non_null_date"] is None
    assert end_row["last_non_null_date"] is None


def test_unit_inference_timestamp_and_hr_edge_cases() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02"],
            "respiration_latestRespirationTimeGMT": ["2025-01-01T22:00:00.0", None],
            "latestSpo2ValueReadingTimeGmt": ["2025-01-01T21:30:00.0", "2025-01-02T21:45:00.0"],
            "spo2SleepMeasurementEndTimestampGMT": [1704153600, 1704240000],
            "spo2SleepAverageHR": [51.0, 49.0],
            "respiration_algorithmVersion": [100, 100],
        }
    )
    dd = build_data_dictionary(df, max_sample_values=2)

    r_resp_time = dd[dd["column"] == "respiration_latestRespirationTimeGMT"].iloc[0]
    assert r_resp_time["inferred_unit"] == "datetime"
    assert r_resp_time["notes"] == "ISO datetime string"

    r_spo2_time = dd[dd["column"] == "latestSpo2ValueReadingTimeGmt"].iloc[0]
    assert r_spo2_time["inferred_unit"] == "datetime"
    assert r_spo2_time["notes"] == "ISO datetime string"

    r_spo2_sleep_end = dd[dd["column"] == "spo2SleepMeasurementEndTimestampGMT"].iloc[0]
    assert r_spo2_sleep_end["inferred_unit"] == "s"
    assert r_spo2_sleep_end["notes"] == "epoch seconds timestamp"

    r_spo2_avg_hr = dd[dd["column"] == "spo2SleepAverageHR"].iloc[0]
    assert r_spo2_avg_hr["inferred_unit"] == "bpm"

    r_algo = dd[dd["column"] == "respiration_algorithmVersion"].iloc[0]
    assert r_algo["inferred_unit"] == ""
