from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from garmin_analytics.monitoring import (
    MonitoringCoreConfig,
    build_monitoring_analysis_windows,
    build_monitoring_feature_catalog,
    build_monitoring_features_full,
    build_monitoring_quality_index,
    build_monitoring_quality_windows,
    select_monitoring_core_features,
)


FORBIDDEN_FEATURE_TOKENS = [
    "p05",
    "p95",
    "trimmed_mean",
    "medium_or_high",
    "first_30m_after_wake",
    "first_2h_after_wake",
    "last_2h_before_sleep",
    "last_4h_before_sleep",
    "endpoint",
    "end_minus_start",
    "coverage_fraction",
    "valid_count",
    "total_count",
    "max_gap_minutes",
    "minutes_to_first_valid",
    "minutes_from_last_valid_to_end",
    "raw_minus_1",
    "raw_minus_2",
    "large_motion_proxy",
    "activation_" + "score",
    "activation_" + "band",
    "wake_" + "activation",
    "dominant_" + "frequency",
    "dominant_" + "period",
]


def _utc(value: str) -> pd.Timestamp:
    return pd.Timestamp(value, tz="UTC")


def _window_frame(
    *,
    calendar_date: str = "2024-03-01",
    sleep_start: str = "2024-03-01 22:00",
    sleep_end: str = "2024-03-02 06:00",
    next_observed_sleep_start: str | None = "2024-03-02 22:00",
    next_sleep_status: str = "observed_within_cutoff",
    offset_minutes: int = 0,
) -> pd.DataFrame:
    sleep_start_utc = _utc(sleep_start)
    sleep_end_utc = _utc(sleep_end)
    observed_next_utc = _utc(next_observed_sleep_start) if next_observed_sleep_start is not None else pd.NaT
    accepted_next_utc = observed_next_utc if next_sleep_status == "observed_within_cutoff" else pd.NaT
    observed_wake_duration = (
        (observed_next_utc - sleep_end_utc).total_seconds() / 3600.0
        if pd.notna(observed_next_utc)
        else np.nan
    )
    wake_duration = (
        (accepted_next_utc - sleep_end_utc).total_seconds() / 3600.0
        if pd.notna(accepted_next_utc)
        else np.nan
    )
    return pd.DataFrame(
        {
            "calendarDate": [calendar_date],
            "local_utc_offset_minutes": [offset_minutes],
            "local_utc_offset_source": ["fixture"],
            "sleep_start_utc": [sleep_start_utc],
            "sleep_end_utc": [sleep_end_utc],
            "next_observed_sleep_start_utc": [observed_next_utc],
            "next_sleep_start_utc": [accepted_next_utc],
            "sleep_start_local": [pd.Timestamp(sleep_start) + pd.Timedelta(minutes=offset_minutes)],
            "sleep_end_local": [pd.Timestamp(sleep_end) + pd.Timedelta(minutes=offset_minutes)],
            "next_observed_sleep_start_local": [
                pd.Timestamp(next_observed_sleep_start) + pd.Timedelta(minutes=offset_minutes)
                if next_observed_sleep_start is not None
                else pd.NaT
            ],
            "next_sleep_start_local": [
                pd.Timestamp(next_observed_sleep_start) + pd.Timedelta(minutes=offset_minutes)
                if next_sleep_status == "observed_within_cutoff" and next_observed_sleep_start is not None
                else pd.NaT
            ],
            "next_sleep_status": [next_sleep_status],
            "sleep_duration_hours": [(sleep_end_utc - sleep_start_utc).total_seconds() / 3600.0],
            "observed_wake_duration_hours": [observed_wake_duration],
            "wake_duration_hours": [wake_duration],
        }
    )


def _minute_monitoring_rows(
    start: str,
    periods: int,
    *,
    heart_rates: list[int] | None = None,
    stress_values: list[int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    timestamps = pd.date_range(_utc(start), periods=periods, freq="min")
    if heart_rates is None:
        heart_rates = [60 + (idx % 40) for idx in range(periods)]
    if stress_values is None:
        stress_values = [20 + (idx % 70) for idx in range(periods)]
    heart_rate = pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "heart_rate": heart_rates[:periods],
            "heart_rate_status": ["valid"] * periods,
        }
    )
    stress = pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "stress_level_raw": stress_values[:periods],
            "stress_level": [999] * periods,
            "stress_status": ["unmeasurable"] * periods,
        }
    )
    return heart_rate, stress


def _quality_index_for(
    heart_rate: pd.DataFrame,
    stress: pd.DataFrame,
    windows: pd.DataFrame,
    *,
    config: MonitoringCoreConfig | None = None,
) -> pd.DataFrame:
    analysis = build_monitoring_analysis_windows(windows, heart_rate, stress, config=config)
    quality_windows = build_monitoring_quality_windows(heart_rate, stress, analysis, config=config)
    return build_monitoring_quality_index(analysis, quality_windows, config=config)


def _small_feature_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    windows = _window_frame(
        calendar_date="2024-02-01",
        sleep_start="2024-02-01 00:00",
        sleep_end="2024-02-01 00:06",
        next_observed_sleep_start="2024-02-01 00:12",
    )
    heart_rates = [50, 55, 60, 65, 70, 75, 52, 55, 58, 51, 54, 57]
    stress_values = [10, 20, 40, 60, 80, -1, 10, 40, 60, 90, -2, -1]
    heart_rate, stress = _minute_monitoring_rows(
        "2024-02-01 00:00",
        12,
        heart_rates=heart_rates,
        stress_values=stress_values,
    )
    quality_index = _quality_index_for(
        heart_rate,
        stress,
        windows,
        config=MonitoringCoreConfig(min_valid_minutes=1, min_paired_minutes=2, sleep_min_hours=0, wake_min_hours=0),
    )
    quality_index["wake_duration_plausible"] = 1
    return heart_rate, stress, windows, quality_index


def _hr_confirmed_minus_2_inputs(
    heart_rates: list[int],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    windows = _window_frame(
        calendar_date="2024-04-01",
        sleep_start="2024-04-01 00:00",
        sleep_end="2024-04-01 00:01",
        next_observed_sleep_start="2024-04-01 00:07",
    )
    heart_rate, stress = _minute_monitoring_rows(
        "2024-04-01 00:01",
        6,
        heart_rates=heart_rates,
        stress_values=[10, 40, 80, -2, -2, -1],
    )
    quality_index = _quality_index_for(
        heart_rate,
        stress,
        windows,
        config=MonitoringCoreConfig(min_valid_minutes=1, min_paired_minutes=2, sleep_min_hours=0, wake_min_hours=0),
    )
    quality_index["wake_duration_plausible"] = 1
    return heart_rate, stress, quality_index


def _assert_no_forbidden_columns(frame: pd.DataFrame) -> None:
    bad = [column for column in frame.columns if any(token in column for token in FORBIDDEN_FEATURE_TOKENS)]
    assert bad == []


def test_analysis_windows_keep_normal_observed_next_sleep() -> None:
    windows = _window_frame(next_observed_sleep_start="2024-03-02 22:00")
    heart_rate, stress = _minute_monitoring_rows("2024-03-02 06:00", 60)

    analysis = build_monitoring_analysis_windows(windows, heart_rate, stress)

    assert len(analysis) == 1
    row = analysis.iloc[0]
    assert row["next_sleep_status"] == "observed_within_cutoff"
    assert row["next_sleep_start_known"] == 1
    assert row["wake_end_known"] == 1
    assert row["boundary_confidence"] == "observed"
    assert row["wake_end_source"] == "observed_next_sleep"
    assert row["wake_duration_hours"] == pytest.approx(16)


def test_analysis_windows_accept_late_after_cutoff_sleep_with_plausible_duration() -> None:
    windows = _window_frame(
        calendar_date="2024-06-08",
        sleep_start="2024-06-08 01:00",
        sleep_end="2024-06-08 13:00",
        next_observed_sleep_start="2024-06-09 15:00",
        next_sleep_status="missing_after_cutoff",
    )
    heart_rate, stress = _minute_monitoring_rows("2024-06-08 13:00", 60)

    analysis = build_monitoring_analysis_windows(windows, heart_rate, stress)

    assert len(analysis) == 1
    row = analysis.iloc[0]
    assert row["analysis_window_id"] == "2024-06-08_0001_late_observed"
    assert row["boundary_confidence"] == "observed_late_within_duration"
    assert row["wake_end_source"] == "observed_next_sleep_after_cutoff_within_duration"
    assert row["wake_end_known"] == 1
    assert row["next_sleep_start_known"] == 1
    assert row["wake_duration_hours"] == pytest.approx(26)
    assert row["next_sleep_start_utc"] == row["next_observed_sleep_start_utc"]


def test_analysis_windows_do_not_noon_cap_missing_after_cutoff_without_split() -> None:
    windows = _window_frame(
        next_observed_sleep_start="2024-03-03 13:00",
        next_sleep_status="missing_after_cutoff",
    )
    heart_rate = pd.DataFrame(columns=["timestamp_utc", "heart_rate", "heart_rate_status"])
    stress = pd.DataFrame(columns=["timestamp_utc", "stress_level_raw", "stress_level", "stress_status"])

    analysis = build_monitoring_analysis_windows(windows, heart_rate, stress)

    assert len(analysis) == 1
    row = analysis.iloc[0]
    assert row["next_sleep_start_known"] == 0
    assert row["wake_end_known"] == 0
    assert row["boundary_confidence"] == "missing_next_sleep"
    assert row["wake_end_source"] == "missing_after_cutoff_no_split"
    assert pd.isna(row["wake_end_utc"])
    assert pd.isna(row["wake_duration_hours"])
    assert row["observed_wake_duration_hours"] == pytest.approx(31)


def test_analysis_windows_split_one_glued_wake_interval_with_synthetic_midpoint() -> None:
    windows = _window_frame(
        next_observed_sleep_start="2024-03-03 22:00",
        next_sleep_status="missing_after_cutoff",
    )
    heart_rate, stress = _minute_monitoring_rows("2024-03-02 06:00", 60)

    analysis = build_monitoring_analysis_windows(windows, heart_rate, stress)

    assert len(analysis) == 2
    first, second = analysis.iloc[0], analysis.iloc[1]
    assert first["wake_end_source"] == "synthetic_midpoint_split"
    assert second["wake_end_source"] == "observed_next_sleep_after_split"
    assert first["next_sleep_start_known"] == 0
    assert second["next_sleep_start_known"] == 1
    assert first["wake_start_known"] == 1
    assert second["wake_start_known"] == 0
    assert pd.notna(first["synthetic_wake_split_utc"])
    assert first["synthetic_wake_split_utc"] == second["synthetic_wake_split_utc"]
    assert first["wake_duration_hours"] == pytest.approx(20)
    assert second["wake_duration_hours"] == pytest.approx(20)


def test_analysis_windows_avoid_split_when_split_day_collides_with_real_sleep_day() -> None:
    first = _window_frame(
        calendar_date="2024-03-01",
        sleep_start="2024-03-01 22:00",
        sleep_end="2024-03-02 06:00",
        next_observed_sleep_start="2024-03-03 22:00",
        next_sleep_status="missing_after_cutoff",
    )
    second = _window_frame(
        calendar_date="2024-03-03",
        sleep_start="2024-03-03 22:00",
        sleep_end="2024-03-04 06:00",
        next_observed_sleep_start="2024-03-04 22:00",
    )
    windows = pd.concat([first, second], ignore_index=True)
    heart_rate, stress = _minute_monitoring_rows("2024-03-02 06:00", 60)

    analysis = build_monitoring_analysis_windows(windows, heart_rate, stress)
    dates = pd.to_datetime(analysis["calendarDate"]).dt.normalize()

    assert len(analysis) == 2
    assert dates.duplicated().sum() == 0
    first_row = analysis.loc[analysis["analysis_window_id"].str.contains("2024-03-01_0001")].iloc[0]
    assert first_row["wake_end_source"] == "split_collision_existing_calendarDate"
    assert first_row["boundary_confidence"] == "missing_next_sleep"
    assert first_row["wake_end_known"] == 0
    assert pd.isna(first_row["wake_end_utc"])
    assert not analysis["analysis_window_id"].str.contains("split_b").any()


def test_analysis_windows_mark_very_long_gap_unsupported() -> None:
    windows = _window_frame(
        next_observed_sleep_start="2024-03-06 00:00",
        next_sleep_status="missing_after_cutoff",
    )
    heart_rate, stress = _minute_monitoring_rows("2024-03-02 06:00", 60)

    analysis = build_monitoring_analysis_windows(windows, heart_rate, stress)

    assert len(analysis) == 1
    row = analysis.iloc[0]
    assert row["unsupported_multi_day_gap"] == 1
    assert row["boundary_confidence"] == "unsupported_multi_day_gap"
    assert row["next_sleep_start_known"] == 0
    assert pd.isna(row["wake_end_utc"])


def test_quality_full_and_core_outputs_keep_unique_calendar_dates() -> None:
    first = _window_frame(
        calendar_date="2024-03-01",
        sleep_start="2024-03-01 22:00",
        sleep_end="2024-03-02 06:00",
        next_observed_sleep_start="2024-03-03 22:00",
        next_sleep_status="missing_after_cutoff",
    )
    second = _window_frame(
        calendar_date="2024-03-03",
        sleep_start="2024-03-03 22:00",
        sleep_end="2024-03-04 06:00",
        next_observed_sleep_start="2024-03-04 22:00",
    )
    windows = pd.concat([first, second], ignore_index=True)
    heart_rate, stress = _minute_monitoring_rows("2024-03-02 06:00", 60)
    config = MonitoringCoreConfig(min_valid_minutes=1, min_paired_minutes=2)

    analysis = build_monitoring_analysis_windows(windows, heart_rate, stress, config=config)
    quality_windows = build_monitoring_quality_windows(heart_rate, stress, analysis, config=config)
    quality_index = build_monitoring_quality_index(analysis, quality_windows, config=config)
    full = build_monitoring_features_full(
        heart_rate,
        stress,
        quality_index,
        max_hr_bpm=100,
        min_valid_minutes=1,
        min_paired_minutes=2,
    )
    core = select_monitoring_core_features(full)

    for frame in [quality_index, full, core]:
        dates = pd.to_datetime(frame["calendarDate"]).dt.normalize()
        assert dates.duplicated().sum() == 0


def test_quality_index_keeps_raw_stress_status_context_outside_feature_tables() -> None:
    windows = _window_frame()
    heart_rate, stress = _minute_monitoring_rows(
        "2024-03-01 22:00",
        1440,
        stress_values=([10, 40, 60, 90, -2, -1] * 240),
    )

    analysis = build_monitoring_analysis_windows(windows, heart_rate, stress)
    quality_windows = build_monitoring_quality_windows(heart_rate, stress, analysis)
    quality_index = build_monitoring_quality_index(analysis, quality_windows)

    wake_stress = quality_windows.loc[
        (quality_windows["window_name"] == "wake") & (quality_windows["signal"] == "stress")
    ].iloc[0]
    assert wake_stress["raw_minus_2_fraction"] == pytest.approx(1 / 6)
    assert wake_stress["raw_minus_2_with_hr_fraction"] == pytest.approx(1 / 6)
    assert wake_stress["raw_minus_2_without_hr_fraction"] == pytest.approx(0)
    assert wake_stress["active_proxy_fraction"] == pytest.approx(1 / 6)
    assert wake_stress["raw_valid_fraction"] == pytest.approx(4 / 6)
    assert quality_index.loc[0, "wake_stress_raw_minus_2_fraction"] == pytest.approx(1 / 6)
    assert quality_index.loc[0, "wake_stress_raw_minus_2_with_hr_fraction"] == pytest.approx(1 / 6)
    assert quality_index.loc[0, "wake_stress_raw_minus_2_without_hr_fraction"] == pytest.approx(0)
    assert quality_index.loc[0, "wake_stress_active_proxy_fraction"] == pytest.approx(1 / 6)
    assert quality_index.loc[0, "wake_duration_plausible"] == 1
    assert quality_index.loc[0, "wake_quarters_usable"] == 1


def test_stress_frac_active_uses_only_raw_minus_2_with_same_minute_valid_hr() -> None:
    heart_rate, stress, quality_index = _hr_confirmed_minus_2_inputs([50, 60, 70, 80, 0, 90])

    features = build_monitoring_features_full(
        heart_rate,
        stress,
        quality_index,
        max_hr_bpm=100,
        min_valid_minutes=1,
        min_paired_minutes=2,
    )
    row = features.iloc[0]

    assert row["wake_stress_frac_resting"] == pytest.approx(1 / 4)
    assert row["wake_stress_frac_low"] == pytest.approx(1 / 4)
    assert row["wake_stress_frac_medium"] == pytest.approx(0)
    assert row["wake_stress_frac_high"] == pytest.approx(1 / 4)
    assert row["wake_stress_frac_active"] == pytest.approx(1 / 4)
    assert row["wake_stress_mean"] == pytest.approx((10 + 40 + 80) / 3)
    assert row["wake_stress_active_has_event"] == 1
    assert row["wake_stress_active_episode_count"] == 1
    assert row["wake_stress_active_total_minutes"] == 1
    assert row["wake_stress_active_time_to_first_minutes"] == pytest.approx(3)
    assert quality_index.loc[0, "wake_stress_raw_minus_2_fraction"] == pytest.approx(2 / 6)
    assert quality_index.loc[0, "wake_stress_raw_minus_2_with_hr_fraction"] == pytest.approx(1 / 6)
    assert quality_index.loc[0, "wake_stress_raw_minus_2_without_hr_fraction"] == pytest.approx(1 / 6)
    assert quality_index.loc[0, "wake_stress_active_proxy_fraction"] == pytest.approx(1 / 6)


def test_raw_minus_2_without_same_minute_valid_hr_is_not_active_or_episode() -> None:
    heart_rate, stress, quality_index = _hr_confirmed_minus_2_inputs([50, 60, 70, 0, 0, 90])

    features = build_monitoring_features_full(
        heart_rate,
        stress,
        quality_index,
        max_hr_bpm=100,
        min_valid_minutes=1,
        min_paired_minutes=2,
    )
    row = features.iloc[0]

    assert row["wake_stress_frac_resting"] == pytest.approx(1 / 3)
    assert row["wake_stress_frac_low"] == pytest.approx(1 / 3)
    assert row["wake_stress_frac_medium"] == pytest.approx(0)
    assert row["wake_stress_frac_high"] == pytest.approx(1 / 3)
    assert row["wake_stress_frac_active"] == pytest.approx(0)
    assert row["wake_stress_mean"] == pytest.approx((10 + 40 + 80) / 3)
    assert row["wake_stress_active_has_event"] == 0
    assert row["wake_stress_active_episode_count"] == 0
    assert row["wake_stress_active_total_minutes"] == 0
    assert pd.isna(row["wake_stress_active_time_to_first_minutes"])
    assert quality_index.loc[0, "wake_stress_raw_minus_2_fraction"] == pytest.approx(2 / 6)
    assert quality_index.loc[0, "wake_stress_raw_minus_2_with_hr_fraction"] == pytest.approx(0)
    assert quality_index.loc[0, "wake_stress_raw_minus_2_without_hr_fraction"] == pytest.approx(2 / 6)
    assert quality_index.loc[0, "wake_stress_active_proxy_fraction"] == pytest.approx(0)


def test_full_features_use_fixed_entropy_active_stress_and_no_event_episode_policy() -> None:
    heart_rate, stress, _windows, quality_index = _small_feature_inputs()

    features = build_monitoring_features_full(
        heart_rate,
        stress,
        quality_index,
        max_hr_bpm=100,
        min_valid_minutes=1,
        min_paired_minutes=2,
    )
    row = features.iloc[0]

    assert features.shape[1] <= 400
    _assert_no_forbidden_columns(features)
    assert row["wake_stress_frac_resting"] == pytest.approx(1 / 5)
    assert row["wake_stress_frac_low"] == pytest.approx(1 / 5)
    assert row["wake_stress_frac_medium"] == pytest.approx(1 / 5)
    assert row["wake_stress_frac_high"] == pytest.approx(1 / 5)
    assert row["wake_stress_frac_active"] == pytest.approx(1 / 5)
    assert row["wake_hr_zone2_plus_has_event"] == 0
    assert row["wake_hr_zone2_plus_episode_count"] == 0
    assert row["wake_hr_zone2_plus_total_minutes"] == 0
    assert row["wake_hr_zone2_plus_mean_duration_minutes"] == 0
    assert row["wake_hr_zone2_plus_fragmentation_index"] == 0
    assert pd.isna(row["wake_hr_zone2_plus_time_to_first_minutes"])
    assert "wake_hr_zone2_plus_time_since_last_minutes" not in features.columns

    assert row["sleep_hr_histogram_entropy"] == pytest.approx(
        -((2 / 6) * np.log2(2 / 6) + (2 / 6) * np.log2(2 / 6) + (2 / 6) * np.log2(2 / 6))
    )
    dynamic_counts, _edges = np.histogram([50, 55, 60, 65, 70, 75], bins=10)
    dynamic_probabilities = dynamic_counts[dynamic_counts > 0] / dynamic_counts.sum()
    dynamic_entropy = float(-(dynamic_probabilities * np.log2(dynamic_probabilities)).sum())
    assert row["sleep_hr_histogram_entropy"] != pytest.approx(dynamic_entropy)
    assert row["sleep_stress_histogram_entropy"] == pytest.approx(
        -((2 / 5) * np.log2(2 / 5) + (1 / 5) * np.log2(1 / 5) * 3)
    )


def test_core_features_are_compact_subset_without_quality_columns() -> None:
    heart_rate, stress, _windows, quality_index = _small_feature_inputs()
    full = build_monitoring_features_full(
        heart_rate,
        stress,
        quality_index,
        max_hr_bpm=100,
        min_valid_minutes=1,
        min_paired_minutes=2,
    )
    core = select_monitoring_core_features(full)

    assert core.shape[1] <= 100
    assert set(["analysis_window_id", "calendarDate"]).issubset(core.columns)
    assert "wake_stress_frac_active" in core.columns
    assert "wake_q1_hr_mean" in core.columns
    assert "pre_sleep_4h_hr_early_minus_late" in core.columns
    _assert_no_forbidden_columns(core)


def test_window_dominated_by_raw_minus_2_has_quality_context_and_missing_numeric_stress() -> None:
    windows = _window_frame(
        calendar_date="2024-02-03",
        sleep_start="2024-02-03 00:00",
        sleep_end="2024-02-03 00:10",
        next_observed_sleep_start="2024-02-03 00:20",
    )
    heart_rate, stress = _minute_monitoring_rows(
        "2024-02-03 00:00",
        20,
        stress_values=[20] * 10 + [-2] * 10,
    )
    quality_index = _quality_index_for(
        heart_rate,
        stress,
        windows,
        config=MonitoringCoreConfig(min_valid_minutes=5, sleep_min_hours=0, wake_min_hours=0),
    )
    features = build_monitoring_features_full(
        heart_rate,
        stress,
        quality_index.assign(wake_duration_plausible=1),
        max_hr_bpm=100,
        min_valid_minutes=5,
        min_paired_minutes=2,
    )

    assert quality_index.loc[0, "wake_stress_raw_minus_2_fraction"] == pytest.approx(1.0)
    assert quality_index.loc[0, "wake_stress_raw_minus_2_with_hr_fraction"] == pytest.approx(1.0)
    assert quality_index.loc[0, "wake_stress_raw_minus_2_without_hr_fraction"] == pytest.approx(0.0)
    assert quality_index.loc[0, "wake_stress_active_proxy_fraction"] == pytest.approx(1.0)
    assert quality_index.loc[0, "wake_stress_coverage_fraction"] == pytest.approx(0.0)
    assert pd.isna(features.loc[0, "wake_stress_mean"])
    assert features.loc[0, "wake_stress_frac_active"] == pytest.approx(1.0)


def test_feature_catalog_classifies_cleaned_full_feature_columns() -> None:
    heart_rate, stress, _windows, quality_index = _small_feature_inputs()
    features = build_monitoring_features_full(
        heart_rate,
        stress,
        quality_index,
        max_hr_bpm=100,
        min_valid_minutes=1,
        min_paired_minutes=2,
    )
    catalog = build_monitoring_feature_catalog(features)
    by_column = catalog.set_index("column")

    assert len(catalog) == features.shape[1]
    assert by_column.loc["analysis_window_id", "family"] == "identity/window metadata"
    assert by_column.loc["sleep_hr_histogram_entropy", "family"] == "distribution/shape"
    assert "fixed maximum-heart-rate zone bins" in by_column.loc["sleep_hr_histogram_entropy", "description"]
    assert by_column.loc["wake_stress_frac_active", "family"] == "stress state fractions"
    assert "same-minute valid HR" in by_column.loc["wake_stress_frac_active", "description"]
    assert by_column.loc["wake_hr_frac_zone2", "family"] == "HR MHR zones"
    assert by_column.loc["wake_hr_zone2_plus_has_event", "family"] == "episodes/state structure"
    assert "no-event cases" in by_column.loc["wake_hr_zone2_plus_has_event", "description"]
    assert bool(by_column.loc["calendarDate", "candidate_model_feature"]) is False
