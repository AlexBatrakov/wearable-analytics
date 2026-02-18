from __future__ import annotations

import pandas as pd

from garmin_analytics.eda.prepare import add_derived_features, build_eda_frames


def test_build_eda_frames_join_and_filters() -> None:
    daily_df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "totalSteps": [5000, 1000, 200],
        }
    )
    quality_df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "valid_day_strict": [True, True, False],
            "corrupted_stress_only_day": [False, True, False],
            "has_sleep": [True, False, True],
        }
    )

    frames = build_eda_frames(daily_df, quality_df)

    assert len(frames["df_all"]) == 3
    assert len(frames["df_strict"]) == 1
    assert len(frames["df_sleep"]) == 2
    assert set(frames.keys()) == {"df_all", "df_strict", "df_sleep"}


def test_add_derived_features_core_metrics() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01"],
            "stressTotalDurationSeconds": [7200],
            "stressAwakeDurationSeconds": [3600],
            "allDayStress_TOTAL_averageStressLevel": [35],
            "allDayStress_TOTAL_totalDuration": [86000],
            "allDayStress_TOTAL_stressDuration": [12000],
            "allDayStress_TOTAL_restDuration": [62000],
            "allDayStress_TOTAL_lowDuration": [8000],
            "allDayStress_TOTAL_mediumDuration": [6000],
            "allDayStress_TOTAL_highDuration": [3000],
            "allDayStress_TOTAL_activityDuration": [5000],
            "allDayStress_TOTAL_uncategorizedDuration": [2000],
            "totalSteps": [4000],
            "totalDistanceMeters": [3000],
            "activeSeconds": [1800],
            "bodyBatteryStartOfDay": [80],
            "bodyBatteryEndOfDay": [30],
            "deepSleepSeconds": [3600],
            "lightSleepSeconds": [7200],
            "remSleepSeconds": [1800],
            "awakeSleepSeconds": [600],
            "latestSpo2Value": [97],
            "lowestSpo2Value": [92],
        }
    )

    out = add_derived_features(df)

    assert float(out.loc[0, "stress_hours"]) == 2.0
    assert float(out.loc[0, "awake_stress_hours"]) == 1.0
    assert float(out.loc[0, "steps_k"]) == 4.0
    assert float(out.loc[0, "distance_km"]) == 3.0
    assert float(out.loc[0, "active_hours"]) == 0.5
    assert float(out.loc[0, "bb_delta"]) == -50.0
    assert float(out.loc[0, "sleep_total_seconds"]) == 13200.0
    assert float(out.loc[0, "sleep_total_hours"]) == 13200.0 / 3600.0
    assert float(out.loc[0, "sleep_efficiency"]) == (3600 + 7200 + 1800) / 13200
    assert float(out.loc[0, "spo2_gap"]) == 5.0

    assert int(out.loc[0, "stress_total_avg_level"]) == 35
    assert int(out.loc[0, "stress_total_total_duration_s"]) == 86000
    assert int(out.loc[0, "stress_total_stress_duration_s"]) == 12000
    assert int(out.loc[0, "stress_total_rest_s"]) == 62000
    assert int(out.loc[0, "stress_total_low_s"]) == 8000
    assert int(out.loc[0, "stress_total_med_s"]) == 6000
    assert int(out.loc[0, "stress_total_high_s"]) == 3000
    assert int(out.loc[0, "stress_total_activity_s"]) == 5000
    assert int(out.loc[0, "stress_total_uncat_s"]) == 2000
