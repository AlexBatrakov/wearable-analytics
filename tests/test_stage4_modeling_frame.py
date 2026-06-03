from __future__ import annotations

import pandas as pd

from garmin_analytics.modeling.stage4 import (
    STAGE4_NON_MODELING_LABEL,
    STAGE4_PRIMARY_TARGET,
    STAGE4_SLEEP_START_CONTEXT_FEATURE,
    STAGE4_SPLIT_COLUMN,
    Stage4ModelingFrameConfig,
    assign_past_random_valid_future_test,
    build_stage4_feature_set_catalog,
    build_stage4_sleep_modeling_frame,
    feature_set_summary,
)


def _timestamp_seconds(ts: str) -> int:
    return int(pd.Timestamp(ts).timestamp())


def _quality_frame(n_rows: int = 10) -> pd.DataFrame:
    rows = []
    for i in range(n_rows):
        date = pd.Timestamp("2025-01-01") + pd.Timedelta(days=i)
        next_sleep = pd.Timestamp("2025-01-01 22:30:00", tz="UTC") + pd.Timedelta(days=i)
        rows.append(
            {
                "analysis_window_id": f"window_{i:02d}",
                "calendarDate": date,
                "next_sleep_start_utc": next_sleep,
                "next_sleep_start_local": next_sleep.tz_convert(None) + pd.Timedelta(hours=1),
                "boundary_confidence": "observed",
                "modeling_recovery_v0_eligible": 1 if i != 1 else 0,
                "next_sleep_status": "observed_within_cutoff",
                "wake_end_source": "observed_next_sleep",
                "wake_start_utc": next_sleep - pd.Timedelta(hours=14),
                "wake_end_utc": next_sleep,
                "sleep_duration_hours": 8.0,
                "wake_duration_hours": 14.0,
                "pre_sleep_4h_usable": 1,
            }
        )
    return pd.DataFrame(rows)


def _sleep_frame(n_rows: int = 10) -> pd.DataFrame:
    rows = []
    for i in range(n_rows):
        start = pd.Timestamp("2025-01-01 22:30:00", tz="UTC") + pd.Timedelta(days=i)
        end = start + pd.Timedelta(hours=7, minutes=30)
        rows.append(
            {
                "calendarDate": start.tz_convert(None).normalize(),
                "sleepStartTimestampGMT": _timestamp_seconds(str(start)),
                "sleepEndTimestampGMT": _timestamp_seconds(str(end)),
                "avgSleepStress": 10.0 + i,
                "sleepRecoveryScore": 80.0 - i,
                "sleepOverallScore": 85.0 - i,
                "sleepQualityScore": 82.0 - i,
            }
        )
    return pd.DataFrame(rows)


def _monitoring_core_frame(n_rows: int = 10) -> pd.DataFrame:
    rows = []
    for i in range(n_rows):
        rows.append(
            {
                "analysis_window_id": f"window_{i:02d}",
                "calendarDate": pd.Timestamp("2025-01-01") + pd.Timedelta(days=i),
                "sleep_hr_mean": 52.0 + i,
                "wake_hr_mean": 72.0 + i,
                "wake_stress_mean": 45.0 + i,
                "wake_q1_hr_mean": 74.0 + i,
                "pre_sleep_4h_stress_mean": 40.0 + i,
                "hr_wake_mean_minus_sleep_mean": 20.0,
            }
        )
    return pd.DataFrame(rows)


def _monitoring_full_frame(n_rows: int = 10) -> pd.DataFrame:
    rows = []
    for i in range(n_rows):
        rows.append(
            {
                "analysis_window_id": f"window_{i:02d}",
                "calendarDate": pd.Timestamp("2025-01-01") + pd.Timedelta(days=i),
                "sleep_hr_mean": 52.0 + i,
                "wake_hr_mean": 72.0 + i,
                "wake_stress_mean": 45.0 + i,
                "wake_q1_hr_mean": 74.0 + i,
                "pre_sleep_4h_stress_mean": 40.0 + i,
                "wake_constant_feature": 1.0,
                "wake_mostly_missing_feature": None if i < 8 else float(i),
            }
        )
    return pd.DataFrame(rows)


def _full_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "column": "sleep_hr_mean",
                "family": "distribution/shape",
                "phase": "sleep",
                "window": "sleep_phase",
                "metric": "mean",
                "candidate_model_feature": True,
                "missing_pct": 0.0,
                "is_constant_non_null": False,
            },
            {
                "column": "wake_hr_mean",
                "family": "distribution/shape",
                "phase": "wake",
                "window": "wake_phase",
                "metric": "mean",
                "candidate_model_feature": True,
                "missing_pct": 0.0,
                "is_constant_non_null": False,
            },
            {
                "column": "wake_stress_mean",
                "family": "distribution/shape",
                "phase": "wake",
                "window": "wake_phase",
                "metric": "mean",
                "candidate_model_feature": True,
                "missing_pct": 0.0,
                "is_constant_non_null": False,
            },
            {
                "column": "wake_q1_hr_mean",
                "family": "relative windows",
                "phase": "wake",
                "window": "wake_q1",
                "metric": "mean",
                "candidate_model_feature": True,
                "missing_pct": 0.0,
                "is_constant_non_null": False,
            },
            {
                "column": "pre_sleep_4h_stress_mean",
                "family": "recovery/deactivation",
                "phase": "wake/pre-sleep",
                "window": "pre_sleep_4h",
                "metric": "mean",
                "candidate_model_feature": True,
                "missing_pct": 0.0,
                "is_constant_non_null": False,
            },
            {
                "column": "wake_constant_feature",
                "family": "distribution/shape",
                "phase": "wake",
                "window": "wake_phase",
                "metric": "constant",
                "candidate_model_feature": True,
                "missing_pct": 0.0,
                "is_constant_non_null": True,
            },
            {
                "column": "wake_mostly_missing_feature",
                "family": "distribution/shape",
                "phase": "wake",
                "window": "wake_phase",
                "metric": "sparse",
                "candidate_model_feature": True,
                "missing_pct": 80.0,
                "is_constant_non_null": False,
            },
        ]
    )


def _daily_frame(n_rows: int = 10) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "calendarDate": [pd.Timestamp("2025-01-01") + pd.Timedelta(days=i) for i in range(n_rows)],
            "totalSteps": [5000 + i for i in range(n_rows)],
            "totalDistanceMeters": [4000 + i for i in range(n_rows)],
            "activeKilocalories": [300 + i for i in range(n_rows)],
            "activeSeconds": [3600 + i for i in range(n_rows)],
            "highlyActiveSeconds": [900 + i for i in range(n_rows)],
            "moderateIntensityMinutes": [20 + i for i in range(n_rows)],
            "vigorousIntensityMinutes": [3 + i for i in range(n_rows)],
            "restingHeartRate": [55 + i for i in range(n_rows)],
            "minHeartRate": [45 + i for i in range(n_rows)],
            "maxHeartRate": [145 + i for i in range(n_rows)],
            "bodyBatteryLowest": [20 + i for i in range(n_rows)],
            "bodyBatteryHighest": [90 - i for i in range(n_rows)],
            "bodyBattery_chargedValue": [40 + i for i in range(n_rows)],
            "bodyBattery_drainedValue": [30 + i for i in range(n_rows)],
            "allDayStress_AWAKE_averageStressLevel": [50 + i for i in range(n_rows)],
        }
    )


def _daily_quality_frame(n_rows: int = 10) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "calendarDate": [pd.Timestamp("2025-01-01") + pd.Timedelta(days=i) for i in range(n_rows)],
            "valid_day_strict": [True] * n_rows,
            "valid_day_loose": [True] * n_rows,
            "corrupted_stress_only_day": [False] * n_rows,
            "has_sleep": [True] * n_rows,
        }
    )


def _build_result():
    return build_stage4_sleep_modeling_frame(
        monitoring_quality_df=_quality_frame(),
        monitoring_core_df=_monitoring_core_frame(),
        monitoring_full_df=_monitoring_full_frame(),
        sleep_df=_sleep_frame(),
        full_catalog_df=_full_catalog(),
        daily_df=_daily_frame(),
        daily_quality_df=_daily_quality_frame(),
        config=Stage4ModelingFrameConfig(random_state=7),
    )


def test_assign_past_random_valid_future_test_keeps_future_test_block() -> None:
    frame = pd.DataFrame(
        {
            "calendarDate": pd.date_range("2025-01-01", periods=20),
            "eligible": [1] * 20,
            "target": list(range(20)),
        }
    )

    split = assign_past_random_valid_future_test(
        frame,
        eligible_col="eligible",
        target_col="target",
        random_state=123,
    )

    assert split.value_counts().to_dict() == {"train": 14, "valid": 3, "test": 3}
    assert set(split.tail(3)) == {"test"}
    assert set(split.iloc[:-3]).issubset({"train", "valid"})
    assert split.equals(
        assign_past_random_valid_future_test(
            frame,
            eligible_col="eligible",
            target_col="target",
            random_state=123,
        )
    )


def test_stage4_frame_aligns_targets_by_exact_next_sleep_start() -> None:
    result = _build_result()
    frame = result.frame

    assert frame.shape[0] == 10
    assert float(frame.loc[0, STAGE4_PRIMARY_TARGET]) == 10.0
    assert float(frame.loc[0, "target_sleepRecoveryScore_next_sleep"]) == 80.0
    assert float(frame.loc[0, "target_sleep_opportunity_hours_next_sleep"]) == 7.5
    assert float(frame.loc[0, "target_sleep_start_hour_local_wrapped_next_sleep"]) == -0.5
    assert float(frame.loc[0, STAGE4_SLEEP_START_CONTEXT_FEATURE]) == -0.5
    assert int(frame.loc[1, "modeling_recovery_v0_eligible"]) == 0
    assert frame.loc[1, STAGE4_SPLIT_COLUMN] == STAGE4_NON_MODELING_LABEL


def test_stage4_feature_sets_follow_wake_presleep_contract() -> None:
    result = _build_result()
    feature_sets = result.feature_sets

    core_cols = set(feature_sets["monitoring_core_wake_pre_sleep"].columns)
    assert {"wake_hr_mean", "wake_q1_hr_mean", "pre_sleep_4h_stress_mean"}.issubset(core_cols)
    assert STAGE4_SLEEP_START_CONTEXT_FEATURE in core_cols
    assert "sleep_hr_mean" not in core_cols
    assert "hr_wake_mean_minus_sleep_mean" not in core_cols

    full_cols = set(feature_sets["monitoring_full_wake_pre_sleep"].columns)
    assert {"wake_hr_mean", "wake_stress_mean", "pre_sleep_4h_stress_mean"}.issubset(full_cols)
    assert STAGE4_SLEEP_START_CONTEXT_FEATURE in full_cols
    assert "sleep_hr_mean" not in full_cols
    assert "wake_constant_feature" not in full_cols
    assert "wake_mostly_missing_feature" not in full_cols


def test_stage4_aggregate_features_are_prefixed_and_reviewed_for_combined_set() -> None:
    result = _build_result()
    aggregate_cols = set(result.feature_sets["aggregate_stage3_baseline"].columns)
    combined_cols = set(result.feature_sets["aggregate_plus_monitoring_full"].columns)

    assert "agg__totalSteps" in aggregate_cols
    assert "agg__awakeAverageStressLevel" in aggregate_cols
    assert "agg__moderateIntensityMinutes" in aggregate_cols
    assert "agg__vigorousIntensityMinutes" in aggregate_cols
    assert STAGE4_SLEEP_START_CONTEXT_FEATURE in aggregate_cols
    assert "agg__activeSeconds" not in aggregate_cols
    assert "agg__highlyActiveSeconds" not in aggregate_cols
    assert "agg__dayofweek" not in aggregate_cols
    assert "agg__day_of_week" not in aggregate_cols
    assert "agg__is_weekend" not in aggregate_cols
    assert "agg__weekday_name" in aggregate_cols
    assert not any(column.startswith("agg__allDayStress_AWAKE_") for column in aggregate_cols)
    assert "agg__totalSteps" in combined_cols
    assert "agg__moderateIntensityMinutes" in combined_cols
    assert "agg__vigorousIntensityMinutes" in combined_cols
    assert STAGE4_SLEEP_START_CONTEXT_FEATURE in combined_cols
    assert "agg__awakeAverageStressLevel" not in combined_cols
    assert "wake_hr_mean" in combined_cols

    review = result.aggregate_candidate_review.set_index("aggregate_feature")
    assert bool(review.loc["agg__totalSteps", "include_in_aggregate_plus_monitoring_full"])
    assert not bool(review.loc["agg__awakeAverageStressLevel", "include_in_aggregate_plus_monitoring_full"])


def test_stage4_feature_catalog_and_summary_are_auditable() -> None:
    result = _build_result()
    catalog = build_stage4_feature_set_catalog(
        result.frame,
        result.feature_sets,
        full_catalog_df=_full_catalog(),
        aggregate_candidate_review=result.aggregate_candidate_review,
    )
    summary = feature_set_summary(result.frame, result.feature_sets)

    assert {"feature_set", "feature", "missing_pct", "family"}.issubset(catalog.columns)
    assert set(summary["feature_set"]) == set(result.feature_sets)
    assert int(summary.loc[summary["feature_set"] == "monitoring_full_wake_pre_sleep", "features"].iloc[0]) == 5
