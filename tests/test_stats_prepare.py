from __future__ import annotations

import pandas as pd

from garmin_analytics.stats.prepare import (
    add_sleep_onset_weekday,
    build_stat_validation_frames,
)


def test_add_sleep_onset_weekday_shifts_calendar_date_back_one_day() -> None:
    frame = pd.DataFrame({"calendarDate": ["2025-01-06", "2025-01-07"]})

    out = add_sleep_onset_weekday(frame)

    assert list(out["sleep_onset_date"].dt.strftime("%Y-%m-%d")) == ["2025-01-05", "2025-01-06"]
    assert list(out["sleep_onset_weekday_name"].astype(str)) == ["Sunday", "Monday"]


def test_build_stat_validation_frames_creates_required_slices() -> None:
    daily_df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "totalSteps": [5000, 7000, 4000],
            "activeSeconds": [2400, 3600, 1800],
            "allDayStress_AWAKE_averageStressLevel": [50, 40, 60],
            "sleepStartTimestampGMT": [1735779600, 1735866000, 1735952400],
            "sleepEndTimestampGMT": [1735808400, 1735894800, 1735981200],
            "sleepRecoveryScore": [72, 81, 65],
            "sleepAverageStressLevel": [18.0, 14.0, 20.0],
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

    frames = build_stat_validation_frames(daily_df, quality_df)

    assert set(frames) == {"day_strict", "sleep_onset", "day_nextsleep"}
    assert "awakeAverageStressLevel" in frames["day_strict"].columns
    assert "sleep_onset_weekday_name" in frames["sleep_onset"].columns
    assert "nextsleep_sleepRecoveryScore" in frames["day_nextsleep"].columns
    assert "nextsleep_sleepAverageStressLevel" in frames["day_nextsleep"].columns
    assert float(frames["day_nextsleep"].loc[0, "nextsleep_sleepRecoveryScore"]) == 81.0
    assert float(frames["day_nextsleep"].loc[0, "nextsleep_sleepAverageStressLevel"]) == 14.0
