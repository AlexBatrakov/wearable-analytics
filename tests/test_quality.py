from __future__ import annotations

import pandas as pd

from garmin_analytics.quality.quality import QualityConfig, apply_quality_labels, build_suspicious_days


def test_quality_flags_scores_and_labels() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "totalSteps": [5000, 300, None],
            "minHeartRate": [45, None, None],
            "maxHeartRate": [170, None, None],
            "restingHeartRate": [52, None, None],
            "stressTotalDurationSeconds": [80000, 2000, None],
            "stressAwakeDurationSeconds": [50000, 1000, None],
            "allDayStress_TOTAL_totalDuration": [80020, 3000, None],
            "allDayStress_AWAKE_totalDuration": [50040, 1300, None],
            "bodyBatteryStartOfDay": [80, 70, None],
            "bodyBatteryEndOfDay": [25, None, None],
            "sleepStartTimestampGMT": [1704067200, None, None],
            "sleepEndTimestampGMT": [1704096000, None, None],
        }
    )

    config = QualityConfig(
        steps_min=50,
        stress_any_min_seconds=21600,
        stress_full_min_seconds=72000,
        strict_min_score=4,
        loose_min_score=3,
        top_n=10,
    )
    out = apply_quality_labels(df, config)

    # Good day
    assert bool(out.loc[0, "has_steps"])
    assert bool(out.loc[0, "has_hr"])
    assert bool(out.loc[0, "has_stress_duration"])
    assert bool(out.loc[0, "has_bodybattery_end"])
    assert bool(out.loc[0, "has_sleep"])
    assert int(out.loc[0, "quality_score"]) == 5
    assert out.loc[0, "day_quality_label_strict"] == "good"
    assert out.loc[0, "day_quality_label_loose"] == "good"

    # Partial day
    assert bool(out.loc[1, "has_steps"])
    assert not bool(out.loc[1, "has_hr"])
    assert not bool(out.loc[1, "has_stress_duration"])
    assert not bool(out.loc[1, "has_bodybattery_end"])
    assert not bool(out.loc[1, "has_sleep"])
    assert int(out.loc[1, "quality_score"]) == 1
    assert out.loc[1, "day_quality_label_strict"] == "bad"
    assert out.loc[1, "day_quality_label_loose"] == "bad"

    # Bad day
    assert int(out.loc[2, "quality_score"]) == 0
    assert out.loc[2, "day_quality_label_strict"] == "bad"

    # Tolerance checks
    assert bool(out.loc[0, "stress_duration_matches_allDayStress_TOTAL"])
    assert not bool(out.loc[1, "stress_duration_matches_allDayStress_TOTAL"])


def test_quality_strict_vs_loose_and_suspicion_reasons() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02"],
            "totalSteps": [2000, None],
            "minHeartRate": [50, None],
            "stressTotalDurationSeconds": [30000, 1000],
            "bodyBatteryEndOfDay": [20, None],
            "sleepStartTimestampGMT": [None, None],
            "sleepEndTimestampGMT": [None, None],
        }
    )
    out = apply_quality_labels(df, QualityConfig(strict_min_score=4, loose_min_score=3, top_n=5))

    # Row 0: has_steps + has_hr + has_stress + bodybattery = 4, no sleep
    assert int(out.loc[0, "quality_score"]) == 4
    assert out.loc[0, "day_quality_label_strict"] == "good"
    assert out.loc[0, "day_quality_label_loose"] == "good"
    assert "has_sleep" in out.loc[0, "suspicion_reasons"]

    suspicious = build_suspicious_days(out, top_n=5)
    assert len(suspicious) == 2
    assert "suspicion_reasons" in suspicious.columns


def test_corrupted_stress_only_day_forced_bad() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2024-02-26"],
            "totalSteps": [None],
            "minHeartRate": [None],
            "maxHeartRate": [None],
            "restingHeartRate": [None],
            "stressTotalDurationSeconds": [86400],
            "bodyBatteryEndOfDay": [None],
            "sleepStartTimestampGMT": [None],
            "sleepEndTimestampGMT": [None],
        }
    )

    out = apply_quality_labels(df, QualityConfig(strict_min_score=4, loose_min_score=3, top_n=5))
    assert bool(out.loc[0, "corrupted_stress_only_day"])
    assert out.loc[0, "day_quality_label_strict"] == "bad"
    assert out.loc[0, "day_quality_label_loose"] == "bad"
    assert not bool(out.loc[0, "valid_day_strict"])
    assert not bool(out.loc[0, "valid_day_loose"])
    assert out.loc[0, "suspicion_reasons"].startswith("corrupted_stress_only_day")