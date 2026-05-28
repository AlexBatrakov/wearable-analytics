# Data Dictionary

Generated at (UTC): 2026-05-28T08:38:48.532472+00:00
Dataset shape: rows=677, columns=176
Date range: 2023-05-26 to 2026-05-18

## Executive summary

- Analysis priority counts: {'medium': 107, 'low': 47, 'high': 22}

## Key analysis signals

| column | inferred_group | inferred_unit | non_null_pct | missing_pct | is_constant | zero_pct | first_non_null_date | last_non_null_date | used_in_quality | used_in_eda | candidate_model_feature | analysis_priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| totalSteps | steps_distance |  | 94.682 | 5.318 | false | 0 | 2023-05-26 | 2026-05-18 | true | true | true | high |  |
| totalDistanceMeters | steps_distance | Meters | 94.682 | 5.318 | false | 0 | 2023-05-26 | 2026-05-18 | false | true | true | high |  |
| activeKilocalories | calories | Kilocalories | 100 | 0 | false | 7.09 | 2023-05-26 | 2026-05-18 | false | true | true | high |  |
| restingHeartRate | heart_rate | bpm | 94.239 | 5.761 | false | 0 | 2023-05-26 | 2026-05-18 | true | true | true | high |  |
| minHeartRate | heart_rate | bpm | 94.978 | 5.022 | false | 0 | 2023-05-26 | 2026-05-18 | true | true | true | high |  |
| maxHeartRate | heart_rate | bpm | 94.978 | 5.022 | false | 0 | 2023-05-26 | 2026-05-18 | true | true | true | high |  |
| stressTotalDurationSeconds | stress | Seconds | 100 | 0 | false | 0 | 2023-05-26 | 2026-05-18 | true | true | true | high |  |
| stressAwakeDurationSeconds | stress | Seconds | 100 | 0 | false | 0 | 2023-05-26 | 2026-05-18 | false | true | true | high |  |
| bodyBatteryStartOfDay | body_battery |  | 94.978 | 5.022 | false | 0 | 2023-05-26 | 2026-05-18 | false | true | true | high |  |
| bodyBatteryEndOfDay | body_battery |  | 86.263 | 13.737 | false | 0 | 2023-05-26 | 2026-05-17 | true | true | true | high |  |
| sleepStartTimestampGMT | sleep | s | 82.127 | 17.873 | false | 0 | 2023-05-27 | 2026-05-18 | true | true | true | high | epoch seconds timestamp |
| sleepEndTimestampGMT | sleep | s | 82.127 | 17.873 | false | 0 | 2023-05-27 | 2026-05-18 | true | true | true | high | epoch seconds timestamp |
| deepSleepSeconds | sleep | Seconds | 82.127 | 17.873 | false | 0.18 | 2023-05-27 | 2026-05-18 | false | true | true | high |  |
| lightSleepSeconds | sleep | Seconds | 82.127 | 17.873 | false | 0 | 2023-05-27 | 2026-05-18 | false | true | true | high |  |
| remSleepSeconds | sleep | Seconds | 80.945 | 19.055 | false | 0 | 2023-05-27 | 2026-05-18 | false | true | true | high |  |
| awakeSleepSeconds | sleep | Seconds | 82.127 | 17.873 | false | 11.691 | 2023-05-27 | 2026-05-18 | false | true | true | high |  |
| averageRespiration | respiration | brpm | 80.059 | 19.941 | false | 0 | 2023-05-27 | 2026-05-18 | false | true | true | high |  |
| avgSleepStress | stress |  | 82.127 | 17.873 | false | 0 | 2023-05-27 | 2026-05-18 | false | true | true | high |  |
| sleepOverallScore | sleep |  | 81.979 | 18.021 | false | 0 | 2023-05-27 | 2026-05-18 | false | true | true | high |  |
| sleepQualityScore | sleep |  | 81.979 | 18.021 | false | 0 | 2023-05-27 | 2026-05-18 | false | true | true | high |  |
| sleepDurationScore | sleep |  | 81.979 | 18.021 | false | 0.18 | 2023-05-27 | 2026-05-18 | false | true | true | high |  |
| sleepRecoveryScore | sleep |  | 81.979 | 18.021 | false | 3.964 | 2023-05-27 | 2026-05-18 | false | true | true | high |  |

## Quality-relevant columns

| column | dtype | non_null_pct | missing_pct | first_non_null_date | last_non_null_date | coverage_within_span_pct | inferred_group | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sleepEndTimestampGMT | Int64 | 82.127 | 17.873 | 2023-05-27 | 2026-05-18 | 82.249 | sleep | epoch seconds timestamp |
| sleepStartTimestampGMT | Int64 | 82.127 | 17.873 | 2023-05-27 | 2026-05-18 | 82.249 | sleep | epoch seconds timestamp |
| bodyBatteryEndOfDay | Int64 | 86.263 | 13.737 | 2023-05-26 | 2026-05-17 | 86.391 | body_battery |  |
| restingHeartRate | Int64 | 94.239 | 5.761 | 2023-05-26 | 2026-05-18 | 94.239 | heart_rate |  |
| totalSteps | Int64 | 94.682 | 5.318 | 2023-05-26 | 2026-05-18 | 94.682 | steps_distance |  |
| maxHeartRate | Int64 | 94.978 | 5.022 | 2023-05-26 | 2026-05-18 | 94.978 | heart_rate |  |
| minHeartRate | Int64 | 94.978 | 5.022 | 2023-05-26 | 2026-05-18 | 94.978 | heart_rate |  |
| stressTotalDurationSeconds | Int64 | 100 | 0 | 2023-05-26 | 2026-05-18 | 100 | stress |  |

## Quality-readiness rationale

- Quality uses `8` core columns/flags.
- Non-null coverage across these columns ranges from `82.127%` to `100%`.
- Median non-null coverage across quality-relevant columns: `94.461%`.
- Lowest-coverage quality inputs (expected to drive many partial/bad labels): sleepEndTimestampGMT (82.127% non-null), sleepStartTimestampGMT (82.127% non-null)
- Use this table to justify threshold choices and explain why some labels are dominated by missing sleep/body-battery coverage rather than parser failures.

## Missingness summary (top 20)

| column | dtype | non_null_pct | missing_pct | is_constant | first_non_null_date | last_non_null_date | inferred_group | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abnormalHeartRateAlertsCount | Int64 | 8.272 | 91.728 | false | 2023-05-28 | 2023-11-04 | heart_rate |  |
| allDayStress_ASLEEP_highDuration | Int64 | 21.566 | 78.434 | false | 2023-05-28 | 2026-05-14 | stress |  |
| bodyBatteryStat_SLEEPEND | Int64 | 36.632 | 63.368 | false | 2024-11-17 | 2026-05-18 | body_battery |  |
| bodyBatteryStat_SLEEPEND_bodyBatteryStatus | str | 36.632 | 63.368 | true | 2024-11-17 | 2026-05-18 | body_battery |  |
| bodyBatteryStat_SLEEPEND_statTimestamp | str | 36.632 | 63.368 | false | 2024-11-17 | 2026-05-18 | body_battery | ISO datetime string |
| bodyBatteryStat_SLEEPSTART | Int64 | 37.518 | 62.482 | false | 2024-06-21 | 2026-05-18 | body_battery |  |
| bodyBatteryStat_SLEEPSTART_bodyBatteryStatus | str | 37.518 | 62.482 | true | 2024-06-21 | 2026-05-18 | body_battery |  |
| bodyBatteryStat_SLEEPSTART_statTimestamp | str | 37.518 | 62.482 | false | 2024-06-21 | 2026-05-18 | body_battery | ISO datetime string |
| restingCaloriesFromActivity | Int64 | 42.984 | 57.016 | false | 2023-05-26 | 2026-05-18 | calories |  |
| hydration_sweatLossInML | Int64 | 43.131 | 56.869 | false | 2023-05-26 | 2026-05-18 | hydration |  |
| hydration_valueInML | Int64 | 43.131 | 56.869 | true | 2023-05-26 | 2026-05-18 | hydration |  |
| hydration_lastEntryTimestampLocal | str | 43.131 | 56.869 | false | 2023-05-26 | 2026-05-18 | hydration | ISO datetime string |
| hydration_goalInML | Float64 | 43.131 | 56.869 | false | 2023-05-26 | 2026-05-18 | hydration |  |
| hydration_capped | boolean | 43.131 | 56.869 | true | 2023-05-26 | 2026-05-18 | hydration |  |
| hydration_adjustedGoalInML | Float64 | 43.131 | 56.869 | false | 2023-05-26 | 2026-05-18 | hydration |  |
| hydration_activityIntakeInML | Int64 | 43.131 | 56.869 | true | 2023-05-26 | 2026-05-18 | hydration |  |
| respiration_algorithmVersion | Int64 | 45.052 | 54.948 | true | 2024-08-14 | 2026-05-18 | respiration |  |
| allDayStress_ASLEEP_activityDuration | Int64 | 47.858 | 52.142 | false | 2023-05-28 | 2026-05-13 | stress |  |
| allDayStress_ASLEEP_stressTooActiveCount | Int64 | 47.858 | 52.142 | false | 2023-05-28 | 2026-05-13 | stress |  |
| bodyBatteryStat_DURINGSLEEP_statTimestamp | str | 52.437 | 47.563 | false | 2023-12-18 | 2026-05-18 | body_battery | ISO datetime string |

## Notes

- This is the short decision-support report (`summary` mode).
- Use `data_dictionary.md` (full mode) for complete column-by-group appendix.
