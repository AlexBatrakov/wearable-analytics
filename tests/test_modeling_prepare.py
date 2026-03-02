from __future__ import annotations

import pandas as pd

from garmin_analytics.modeling.prepare import (
    add_modeling_features,
    add_binary_quantile_target,
    add_binary_threshold_target,
    build_recovery_modeling_frame,
    resolve_recovery_feature_columns,
)


def test_add_modeling_features_builds_stage3_aliases() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01"],
            "activeSeconds": [3600],
            "highlyActiveSeconds": [1800],
            "bodyBattery_chargedValue": [42],
            "bodyBattery_drainedValue": [30],
            "sleepStartTimestampGMT": [1735693200],
            "sleepEndTimestampGMT": [1735722000],
            "allDayStress_AWAKE_averageStressLevel": [55],
            "allDayStress_AWAKE_lowDuration": [7200],
            "allDayStress_AWAKE_mediumDuration": [3600],
            "allDayStress_AWAKE_highDuration": [1800],
            "allDayStress_AWAKE_restDuration": [14400],
            "allDayStress_AWAKE_uncategorizedDuration": [1800],
            "allDayStress_AWAKE_activityDuration": [3600],
            "allDayStress_AWAKE_totalDuration": [32400],
        }
    )

    out = add_modeling_features(df)

    assert float(out.loc[0, "active_hours"]) == 1.0
    assert float(out.loc[0, "highly_active_hours"]) == 0.5
    assert float(out.loc[0, "bodyBatteryNetBalance"]) == 12.0
    assert float(out.loc[0, "awakeAverageStressLevel"]) == 55.0
    assert float(out.loc[0, "awakeLowStressHours"]) == 2.0
    assert float(out.loc[0, "awakeHighStressHours"]) == 0.5
    assert round(float(out.loc[0, "awakeRestShare"]), 4) == round(4.0 / 9.0, 4)
    assert round(float(out.loc[0, "sleep_opportunity_hours"]), 4) == 8.0
    assert "sleep_start_hour_local_wrapped" in out.columns
    assert "weekday_name" in out.columns
    assert "is_weekend" in out.columns


def test_build_recovery_modeling_frame_aligns_next_night_targets() -> None:
    daily_df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "totalSteps": [5000, 7000, 4000],
            "activeSeconds": [2400, 3600, 1800],
            "allDayStress_AWAKE_averageStressLevel": [50, 40, 60],
            "sleepStartTimestampGMT": [1735779600, 1735866000, 1735952400],
            "sleepEndTimestampGMT": [1735808400, 1735894800, 1735981200],
            "sleepRecoveryScore": [72, 81, 65],
            "sleepOverallScore": [80, 88, 74],
            "sleepQualityScore": [82, 91, 77],
            "avgSleepStress": [18.0, 12.5, 21.0],
        }
    )
    quality_df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "valid_day_strict": [True, True, True],
            "valid_day_loose": [True, True, True],
            "corrupted_stress_only_day": [False, False, False],
            "has_sleep": [True, True, True],
        }
    )

    modeled = build_recovery_modeling_frame(daily_df, quality_df, low_recovery_threshold=70.0)

    assert list(modeled["calendarDate"].dt.strftime("%Y-%m-%d")) == ["2025-01-01", "2025-01-02", "2025-01-03"]
    assert float(modeled.loc[0, "target_sleepRecoveryScore_next_night"]) == 81.0
    assert int(modeled.loc[0, "target_low_recovery_next_night"]) == 0
    assert float(modeled.loc[1, "target_sleepRecoveryScore_next_night"]) == 65.0
    assert int(modeled.loc[1, "target_low_recovery_next_night"]) == 1
    assert float(modeled.loc[0, "target_sleepOverallScore_next_night"]) == 88.0
    assert float(modeled.loc[0, "target_sleepQualityScore_next_night"]) == 91.0
    assert float(modeled.loc[0, "target_avgSleepStress_next_night"]) == 12.5
    assert pd.isna(modeled.loc[2, "target_sleepRecoveryScore_next_night"])
    assert "nextsleep_sleep_opportunity_hours" in modeled.columns


def test_resolve_recovery_feature_columns_filters_to_existing_columns() -> None:
    frame = pd.DataFrame(
        {
            "totalSteps": [1],
            "restingHeartRate": [50],
            "awakeAverageStressLevel": [40],
            "nextsleep_sleep_start_hour_local_wrapped": [-1.0],
        }
    )

    cols = resolve_recovery_feature_columns(frame, tiers=("tier1", "tier2"), include_schedule=True)

    assert cols == [
        "totalSteps",
        "restingHeartRate",
        "awakeAverageStressLevel",
        "nextsleep_sleep_start_hour_local_wrapped",
    ]


def test_resolve_recovery_feature_columns_supports_compact_stress_tier() -> None:
    frame = pd.DataFrame(
        {
            "totalSteps": [1],
            "awakeAverageStressLevel": [40],
            "awakeRestShare": [0.3],
            "awakeMeasuredHours": [14.0],
        }
    )

    cols = resolve_recovery_feature_columns(frame, tiers=("tier1", "tier2_compact"))

    assert cols == [
        "totalSteps",
        "awakeAverageStressLevel",
        "awakeMeasuredHours",
        "awakeRestShare",
    ]


def test_add_binary_threshold_target_supports_lower_and_upper_tails() -> None:
    frame = pd.DataFrame({"score": [10.0, 20.0, 30.0, None]})

    low = add_binary_threshold_target(
        frame,
        source_col="score",
        target_col="target_low",
        threshold=20.0,
        direction="lt",
    )
    high = add_binary_threshold_target(
        frame,
        source_col="score",
        target_col="target_high",
        threshold=20.0,
        direction="ge",
    )

    assert list(low["target_low"].astype("object")) == [1, 0, 0, pd.NA]
    assert list(high["target_high"].astype("object")) == [0, 1, 1, pd.NA]


def test_add_binary_quantile_target_returns_cutoff() -> None:
    frame = pd.DataFrame({"score": [10.0, 20.0, 30.0, 40.0]})

    out, cutoff = add_binary_quantile_target(
        frame,
        source_col="score",
        target_col="target_top_quartile",
        quantile=0.75,
        tail="upper",
        inclusive=True,
    )

    assert cutoff == 32.5
    assert list(out["target_top_quartile"].astype("object")) == [0, 0, 0, 1]
