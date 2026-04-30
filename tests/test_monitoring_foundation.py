from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from garmin_analytics.monitoring import (
    FIT_EPOCH_S,
    build_monitoring_daily_features,
    build_semantic_sleep_windows,
    classify_stress_value,
    extract_monitoring_messages,
    normalize_heart_rate_frame,
    normalize_stress_frame,
    resolve_timestamp_16,
)


def _utc(value: str) -> pd.Timestamp:
    return pd.Timestamp(value, tz="UTC")


def test_resolve_timestamp_16_reconstructs_wraparound() -> None:
    assert resolve_timestamp_16(None, 1) is None
    assert resolve_timestamp_16(0x0001FFFE, 0x0001) == 0x00020001
    assert resolve_timestamp_16(0x00010010, 0x0020) == 0x00010020


def test_extract_monitoring_messages_aligns_timestamp_16_and_status_values() -> None:
    base = datetime.fromtimestamp(FIT_EPOCH_S + 0x0001FFFE, tz=timezone.utc)
    messages = {
        "file_id_mesgs": [{"type": "monitoring_b"}],
        "monitoring_mesgs": [
            {"timestamp": base, "heart_rate": 72},
            {"timestamp_16": 0x0001, "heart_rate": 0},
        ],
        "stress_level_mesgs": [
            {"stress_level_time": base, "stress_level_value": -1},
            {"stress_level_time": base + pd.Timedelta(minutes=1), "stress_level_value": 55},
            {"stress_level_time": base + pd.Timedelta(minutes=2), "stress_level_value": 101},
        ],
    }

    extract = extract_monitoring_messages(messages)

    assert [row["heart_rate_status"] for row in extract.heart_rate_rows] == [
        "valid",
        "zero_or_unmeasurable",
    ]
    assert extract.heart_rate_rows[1]["timestamp_utc"] == datetime.fromtimestamp(
        FIT_EPOCH_S + 0x00020001, tz=timezone.utc
    )
    assert [row["stress_status"] for row in extract.stress_rows] == [
        "unmeasurable",
        "valid",
        "status_value",
    ]
    assert [row["stress_level"] for row in extract.stress_rows] == [None, 55, None]
    assert classify_stress_value(100) == ("valid", 100)
    assert classify_stress_value(-2) == ("unmeasurable", None)


def test_normalization_recomputes_status_from_numeric_values() -> None:
    timestamps = pd.date_range("2024-01-01", periods=3, freq="min", tz="UTC")
    heart_rate = normalize_heart_rate_frame(
        pd.DataFrame(
            {
                "timestamp_utc": timestamps,
                "heart_rate": [72, 0, -5],
                "heart_rate_status": ["zero_or_unmeasurable", "valid", "valid"],
            }
        )
    )
    stress = normalize_stress_frame(
        pd.DataFrame(
            {
                "timestamp_utc": timestamps,
                "stress_level_raw": [10, -1, 101],
                "stress_level": [999, 80, 90],
                "stress_status": ["unmeasurable", "valid", "valid"],
            }
        )
    )

    assert list(heart_rate["heart_rate_status"]) == [
        "valid",
        "zero_or_unmeasurable",
        "zero_or_unmeasurable",
    ]
    assert list(stress["stress_status"]) == ["valid", "unmeasurable", "status_value"]
    assert list(stress["stress_level"]) == [10, pd.NA, pd.NA]


def test_build_semantic_sleep_windows_applies_local_noon_cutoff() -> None:
    sleep_df = pd.DataFrame(
        {
            "calendarDate": ["2024-01-01", "2024-01-02", "2024-01-04", "2024-01-06"],
            "sleepStartTimestampGMT": [
                int(_utc("2024-01-01 22:00").timestamp()),
                int(_utc("2024-01-02 22:30").timestamp()),
                int(_utc("2024-01-04 10:30").timestamp()),
                int(_utc("2024-01-06 23:00").timestamp()),
            ],
            "sleepEndTimestampGMT": [
                int(_utc("2024-01-02 06:00").timestamp()),
                int(_utc("2024-01-03 06:30").timestamp()),
                int(_utc("2024-01-04 18:30").timestamp()),
                int(_utc("2024-01-07 07:00").timestamp()),
            ],
        }
    )
    daily_df = pd.DataFrame(
        {
            "calendarDate": ["2024-01-01", "2024-01-02", "2024-01-04", "2024-01-06"],
            "wellnessStartTimeGmt": [
                "2024-01-01T00:00:00.0",
                "2024-01-02T00:00:00.0",
                "2024-01-04T00:00:00.0",
                "2024-01-06T00:00:00.0",
            ],
            "wellnessStartTimeLocal": [
                "2024-01-01T02:00:00.0",
                "2024-01-02T01:00:00.0",
                "2024-01-04T01:00:00.0",
                "2024-01-06T01:00:00.0",
            ],
            "wellnessEndTimeGmt": [
                "2024-01-02T00:00:00.0",
                "2024-01-03T00:00:00.0",
                "2024-01-05T00:00:00.0",
                "2024-01-07T00:00:00.0",
            ],
            "wellnessEndTimeLocal": [
                "2024-01-02T02:00:00.0",
                "2024-01-03T01:00:00.0",
                "2024-01-05T01:00:00.0",
                "2024-01-07T01:00:00.0",
            ],
        }
    )

    windows = build_semantic_sleep_windows(sleep_df, daily_df=daily_df)
    utc_only_windows = build_semantic_sleep_windows(sleep_df)

    assert len(windows) == 4
    assert len(utc_only_windows) == 4
    assert utc_only_windows["local_utc_offset_minutes"].isna().all()
    assert set(utc_only_windows["local_utc_offset_source"]) == {"missing"}
    assert windows.loc[0, "sleep_duration_hours"] == 8.0
    assert windows.loc[0, "wake_duration_hours"] == 16.5
    assert windows.loc[0, "observed_wake_duration_hours"] == 16.5
    assert windows.loc[0, "next_sleep_start_utc"] == _utc("2024-01-02 22:30")
    assert windows.loc[0, "next_observed_sleep_start_utc"] == _utc("2024-01-02 22:30")
    assert windows.loc[0, "next_sleep_status"] == "observed_within_cutoff"
    assert windows.loc[1, "next_sleep_status"] == "observed_within_cutoff"
    assert windows.loc[1, "next_sleep_start_utc"] == _utc("2024-01-04 10:30")
    assert windows.loc[1, "next_sleep_start_local"] == pd.Timestamp("2024-01-04 11:30")
    assert windows.loc[2, "next_observed_sleep_start_utc"] == _utc("2024-01-06 23:00")
    assert pd.isna(windows.loc[2, "next_sleep_start_utc"])
    assert pd.isna(windows.loc[2, "wake_duration_hours"])
    assert windows.loc[2, "observed_wake_duration_hours"] == 52.5
    assert windows.loc[2, "next_sleep_status"] == "missing_after_cutoff"
    assert pd.isna(windows.loc[3, "next_observed_sleep_start_utc"])
    assert pd.isna(windows.loc[3, "next_sleep_start_utc"])
    assert windows.loc[3, "next_sleep_status"] == "no_following_observed_sleep"
    assert list(windows["local_utc_offset_minutes"]) == [120, 60, 60, 60]
    assert set(windows["local_utc_offset_source"]) == {"start_end_agree"}
    assert windows.loc[0, "sleep_start_local"] == pd.Timestamp("2024-01-02 00:00")
    assert windows.loc[0, "sleep_end_local"] == pd.Timestamp("2024-01-02 08:00")
    assert windows.loc[0, "next_sleep_start_local"] == pd.Timestamp("2024-01-02 23:30")


def test_build_monitoring_daily_features_keeps_foundation_columns_only() -> None:
    windows = pd.DataFrame(
        {
            "calendarDate": ["2024-01-01", "2024-01-02"],
            "local_utc_offset_minutes": [0, 0],
            "local_utc_offset_source": ["fixture", "fixture"],
            "sleep_start_utc": [_utc("2024-01-01 00:00"), _utc("2024-01-02 00:00")],
            "sleep_end_utc": [_utc("2024-01-01 00:03"), _utc("2024-01-02 00:03")],
            "next_observed_sleep_start_utc": [_utc("2024-01-01 00:06"), _utc("2024-01-10 00:00")],
            "next_sleep_start_utc": [_utc("2024-01-01 00:06"), pd.NaT],
            "sleep_start_local": [pd.Timestamp("2024-01-01 00:00"), pd.Timestamp("2024-01-02 00:00")],
            "sleep_end_local": [pd.Timestamp("2024-01-01 00:03"), pd.Timestamp("2024-01-02 00:03")],
            "next_observed_sleep_start_local": [
                pd.Timestamp("2024-01-01 00:06"),
                pd.Timestamp("2024-01-10 00:00"),
            ],
            "next_sleep_start_local": [pd.Timestamp("2024-01-01 00:06"), pd.NaT],
            "next_sleep_status": ["observed_within_cutoff", "missing_after_cutoff"],
            "sleep_duration_hours": [0.05, 0.05],
            "observed_wake_duration_hours": [0.05, 191.95],
            "wake_duration_hours": [0.05, pd.NA],
        }
    )
    heart_rate = pd.DataFrame(
        {
            "timestamp_utc": [
                _utc("2024-01-01 00:00"),
                _utc("2024-01-01 00:01"),
                _utc("2024-01-01 00:02"),
                _utc("2024-01-01 00:03"),
                _utc("2024-01-01 00:04"),
                _utc("2024-01-01 00:05"),
                _utc("2024-01-02 00:00"),
                _utc("2024-01-02 00:01"),
                _utc("2024-01-02 00:02"),
                _utc("2024-01-02 00:03"),
                _utc("2024-01-02 00:04"),
                _utc("2024-01-02 00:05"),
            ],
            "heart_rate": [50, 52, 0, 70, 90, 100, 55, 57, 58, 75, 80, 82],
            "heart_rate_status": [
                "valid",
                "valid",
                "zero_or_unmeasurable",
                "valid",
                "valid",
                "valid",
                "valid",
                "valid",
                "valid",
                "valid",
                "valid",
                "valid",
            ],
        }
    )
    stress = pd.DataFrame(
        {
            "timestamp_utc": [
                _utc("2024-01-01 00:00"),
                _utc("2024-01-01 00:01"),
                _utc("2024-01-01 00:02"),
                _utc("2024-01-01 00:03"),
                _utc("2024-01-01 00:04"),
                _utc("2024-01-01 00:05"),
                _utc("2024-01-02 00:00"),
                _utc("2024-01-02 00:01"),
                _utc("2024-01-02 00:02"),
                _utc("2024-01-02 00:03"),
                _utc("2024-01-02 00:04"),
                _utc("2024-01-02 00:05"),
            ],
            "stress_level_raw": [10, -1, 20, 30, 60, 80, 5, 6, 7, 20, 25, 30],
            "stress_level": [999, 999, 999, 999, 999, 999, 999, 999, 999, 999, 999, 999],
            "stress_status": [
                "unmeasurable",
                "valid",
                "unmeasurable",
                "unmeasurable",
                "unmeasurable",
                "unmeasurable",
                "unmeasurable",
                "unmeasurable",
                "unmeasurable",
                "unmeasurable",
                "unmeasurable",
                "unmeasurable",
            ],
        }
    )

    features = build_monitoring_daily_features(heart_rate, stress, windows)

    assert len(features) == 2
    first = features.loc[0]
    assert first["sleep_hr_valid_count"] == 2
    assert first["sleep_hr_coverage_fraction"] == 2 / 3
    assert first["sleep_stress_unmeasurable_fraction"] == 1 / 3
    assert first["sleep_stress_nonvalid_fraction"] == 1 / 3
    assert first["sleep_stress_status_value_fraction"] == 0
    assert first["wake_stress_mean"] == (30 + 60 + 80) / 3
    assert first["wake_hr_std"] == pd.Series([70, 90, 100]).std(ddof=0)
    assert first["sleep_stress_std"] == pd.Series([10, 20]).std(ddof=0)
    second = features.loc[1]
    assert second["sleep_hr_valid_count"] == 3
    assert second["wake_hr_total_count"] == 0
    assert second["wake_stress_total_count"] == 0
    assert pd.isna(second["wake_hr_mean"])
    assert second["next_sleep_status"] == "missing_after_cutoff"

    removed_columns = [
        "wake_" + "activation" + "_score_v0",
        "wake_" + "activation" + "_score_percentile_v0",
        "wake_" + "activation" + "_band_v0",
        "wake_stress_" + "fraction" + "_ge_60",
        "wake_hr_" + "fraction" + "_ge_85",
    ]
    assert not set(removed_columns) & set(features.columns)
