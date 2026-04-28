from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from garmin_analytics.monitoring import (
    build_monitoring_daily_features,
    build_monitoring_feature_catalog,
    build_monitoring_feature_library,
)


def _utc(value: str) -> pd.Timestamp:
    return pd.Timestamp(value, tz="UTC")


def _fixture_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    windows = pd.DataFrame(
        {
            "calendarDate": ["2024-02-01"],
            "local_utc_offset_minutes": [0],
            "local_utc_offset_source": ["fixture"],
            "sleep_start_utc": [_utc("2024-02-01 00:00")],
            "sleep_end_utc": [_utc("2024-02-01 00:08")],
            "next_sleep_start_utc": [_utc("2024-02-01 00:16")],
            "sleep_start_local": [pd.Timestamp("2024-02-01 00:00")],
            "sleep_end_local": [pd.Timestamp("2024-02-01 00:08")],
            "next_sleep_start_local": [pd.Timestamp("2024-02-01 00:16")],
            "sleep_duration_hours": [8 / 60],
            "wake_duration_hours": [8 / 60],
        }
    )
    heart_rate = pd.DataFrame(
        {
            "timestamp_utc": [
                _utc("2024-02-01 00:00"),
                _utc("2024-02-01 00:01"),
                _utc("2024-02-01 00:02"),
                _utc("2024-02-01 00:04"),
                _utc("2024-02-01 00:07"),
                _utc("2024-02-01 00:08"),
                _utc("2024-02-01 00:09"),
                _utc("2024-02-01 00:10"),
                _utc("2024-02-01 00:11"),
                _utc("2024-02-01 00:12"),
                _utc("2024-02-01 00:15"),
            ],
            "heart_rate": [50, 55, 60, 65, 70, 45, 52, 62, 72, 92, 101],
            "heart_rate_status": ["valid"] * 11,
        }
    )
    stress = pd.DataFrame(
        {
            "timestamp_utc": [
                _utc("2024-02-01 00:00"),
                _utc("2024-02-01 00:01"),
                _utc("2024-02-01 00:02"),
                _utc("2024-02-01 00:04"),
                _utc("2024-02-01 00:07"),
                _utc("2024-02-01 00:08"),
                _utc("2024-02-01 00:09"),
                _utc("2024-02-01 00:10"),
                _utc("2024-02-01 00:11"),
                _utc("2024-02-01 00:12"),
                _utc("2024-02-01 00:15"),
            ],
            "stress_level_raw": [80, 70, 20, 10, 5, 30, 55, -1, -2, 85, 20],
            "stress_level": [999] * 11,
            "stress_status": ["unmeasurable"] * 11,
        }
    )
    foundation = build_monitoring_daily_features(heart_rate, stress, windows)
    foundation["foundation_marker"] = 1.23
    return heart_rate, stress, windows, foundation


def _feature_row() -> pd.Series:
    return _feature_frame().iloc[0]


def _feature_frame() -> pd.DataFrame:
    heart_rate, stress, windows, foundation = _fixture_inputs()
    features = build_monitoring_feature_library(
        heart_rate,
        stress,
        windows,
        foundation,
        max_hr_bpm=100,
        gap_break_minutes=2,
        min_valid_minutes=1,
        min_paired_minutes=3,
    )
    assert len(features) == 1
    return features


def test_feature_library_preserves_foundation_and_adds_distribution_states_and_zones() -> None:
    row = _feature_row()

    assert row["foundation_marker"] == 1.23
    assert row["sleep_hr_min"] == 50
    assert row["sleep_hr_max"] == 70
    assert row["sleep_hr_range"] == 20
    assert row["wake_hr_frac_below_zone1"] == pytest.approx(1 / 6)
    assert row["wake_hr_frac_zone1_50_60"] == pytest.approx(1 / 6)
    assert row["wake_hr_frac_zone2_60_70"] == pytest.approx(1 / 6)
    assert row["wake_hr_frac_zone3_70_80"] == pytest.approx(1 / 6)
    assert row["wake_hr_frac_zone4_80_90"] == pytest.approx(0)
    assert row["wake_hr_frac_zone5_90_100"] == pytest.approx(1 / 6)
    assert row["wake_hr_frac_above_mhr"] == pytest.approx(1 / 6)
    assert row["wake_stress_frac_resting_0_25"] == pytest.approx(1 / 4)
    assert row["wake_stress_frac_low_26_50"] == pytest.approx(1 / 4)
    assert row["wake_stress_frac_medium_51_75"] == pytest.approx(1 / 4)
    assert row["wake_stress_frac_high_76_100"] == pytest.approx(1 / 4)
    assert row["wake_stress_mean"] == pytest.approx((30 + 55 + 85 + 20) / 4)
    assert row["sleep_hr_histogram_entropy"] == pytest.approx(
        -((2 / 5) * np.log2(2 / 5) + (2 / 5) * np.log2(2 / 5) + (1 / 5) * np.log2(1 / 5))
    )
    assert row["sleep_stress_histogram_entropy"] == pytest.approx(
        -((3 / 5) * np.log2(3 / 5) + (1 / 5) * np.log2(1 / 5) + (1 / 5) * np.log2(1 / 5))
    )
    dynamic_counts, _edges = np.histogram([50, 55, 60, 65, 70], bins=10)
    dynamic_probabilities = dynamic_counts[dynamic_counts > 0] / dynamic_counts.sum()
    dynamic_entropy = float(-(dynamic_probabilities * np.log2(dynamic_probabilities)).sum())
    assert row["sleep_hr_histogram_entropy"] != pytest.approx(dynamic_entropy)


def test_gap_aware_variability_and_episodes_break_on_large_gaps() -> None:
    row = _feature_row()

    assert row["sleep_hr_diff_valid_pair_count"] == 3
    assert row["sleep_hr_diff_gap_break_count"] == 1
    assert row["sleep_hr_mean_abs_diff"] == pytest.approx(5)
    assert row["sleep_hr_longest_missing_gap_minutes"] == pytest.approx(2)
    assert row["sleep_hr_missing_gap_count"] == 2
    assert row["wake_stress_diff_gap_break_count"] == 2
    assert row["wake_stress_high_episode_count"] == 1
    assert row["wake_stress_high_total_minutes"] == 1
    assert row["wake_stress_high_time_to_first_minutes"] == pytest.approx(4)
    assert row["wake_stress_elevated_episode_count"] == 2
    assert row["wake_hr_zone1_plus_episode_count"] == 2
    assert row["wake_hr_zone1_plus_total_minutes"] == 5


def test_windows_recovery_contrast_coupling_and_raw_status_features() -> None:
    row = _feature_row()

    assert row["wake_q1_hr_mean"] == pytest.approx((45 + 52) / 2)
    assert row["pre_sleep_4h_hr_mean"] == pytest.approx((45 + 52 + 62 + 72 + 92 + 101) / 6)
    assert row["sleep_stress_time_to_low_stress_minutes"] == pytest.approx(2)
    assert row["wake_stress_raw_minus_1_count"] == 1
    assert row["wake_stress_raw_minus_2_count"] == 1
    assert row["wake_stress_large_motion_proxy_minutes"] == 1
    assert row["wake_stress_large_motion_proxy_fraction"] == pytest.approx(1 / 6)
    assert row["wake_paired_hr_stress_valid_minutes"] == 4
    assert row["wake_paired_hr_stress_coverage_fraction"] == pytest.approx(4 / 8)
    assert row["wake_frac_hr_zone1_plus_stress_elevated"] == pytest.approx(2 / 4)
    assert row["wake_frac_hr_zone1_plus_stress_low_or_resting"] == pytest.approx(1 / 4)
    assert row["wake_frac_hr_below_zone1_stress_high"] == pytest.approx(0)
    assert row["stress_wake_high_fraction_minus_sleep"] == pytest.approx((1 / 4) - (1 / 5))


def test_feature_catalog_classifies_columns_and_dataset_diagnostics() -> None:
    features = _feature_frame()
    features["all_null_probe"] = np.nan
    features["mostly_missing_probe"] = [1.0]
    features = pd.concat(
        [
            features,
            features.assign(
                calendarDate=pd.Timestamp("2024-02-02"),
                mostly_missing_probe=np.nan,
                wake_stress_frac_high_76_100=0.0,
            ),
        ],
        ignore_index=True,
    )

    catalog = build_monitoring_feature_catalog(features)
    by_column = catalog.set_index("column")

    assert len(catalog) == features.shape[1]
    assert by_column.loc["calendarDate", "family"] == "identity/window metadata"
    assert by_column.loc["sleep_hr_coverage_fraction", "family"] == "foundation coverage"
    assert by_column.loc["sleep_hr_histogram_entropy", "family"] == "distribution/shape"
    assert "fixed maximum-heart-rate zone bins" in by_column.loc["sleep_hr_histogram_entropy", "description"]
    assert by_column.loc["wake_stress_frac_high_76_100", "family"] == "stress state fractions"
    assert by_column.loc["wake_hr_frac_zone2_60_70", "family"] == "HR MHR zones"
    assert by_column.loc["wake_paired_hr_stress_valid_minutes", "family"] == "HR/stress coupling"
    assert by_column.loc["wake_stress_raw_minus_2_fraction", "family"] == "raw stress status"
    assert bool(by_column.loc["all_null_probe", "is_all_null"])
    assert bool(by_column.loc["mostly_missing_probe", "is_constant_non_null"])
    assert by_column.loc["mostly_missing_probe", "missing_pct"] == pytest.approx(50.0)
    assert by_column.loc["wake_hr_frac_zone4_80_90", "unit"] == "fraction 0..1"
    assert bool(by_column.loc["calendarDate", "candidate_model_feature"]) is False
