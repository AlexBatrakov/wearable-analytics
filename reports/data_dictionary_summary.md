# Data Dictionary

Generated at (UTC): 2026-02-23T15:02:15.401709+00:00
Dataset shape: rows=580, columns=176
Date range: 2023-05-26 to 2026-02-05

## Executive summary

- Analysis priority counts: {'medium': 107, 'low': 47, 'high': 22}

## Key analysis signals

| column | inferred_group | inferred_unit | non_null_pct | missing_pct | is_constant | zero_pct | first_non_null_date | last_non_null_date | used_in_quality | used_in_eda | candidate_model_feature | analysis_priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| totalSteps | steps_distance |  | 94.138 | 5.862 | false | 0 | 2023-05-26 | 2026-02-05 | true | true | true | high |  |
| totalDistanceMeters | steps_distance | Meters | 94.138 | 5.862 | false | 0 | 2023-05-26 | 2026-02-05 | false | true | true | high |  |
| activeKilocalories | calories | Kilocalories | 100 | 0 | false | 7.759 | 2023-05-26 | 2026-02-05 | false | true | true | high |  |
| restingHeartRate | heart_rate | bpm | 93.621 | 6.379 | false | 0 | 2023-05-26 | 2026-02-05 | true | true | true | high |  |
| minHeartRate | heart_rate | bpm | 94.483 | 5.517 | false | 0 | 2023-05-26 | 2026-02-05 | true | true | true | high |  |
| maxHeartRate | heart_rate | bpm | 94.483 | 5.517 | false | 0 | 2023-05-26 | 2026-02-05 | true | true | true | high |  |
| stressTotalDurationSeconds | stress | Seconds | 100 | 0 | false | 0 | 2023-05-26 | 2026-02-05 | true | true | true | high |  |
| stressAwakeDurationSeconds | stress | Seconds | 100 | 0 | false | 0 | 2023-05-26 | 2026-02-05 | false | true | true | high |  |
| bodyBatteryStartOfDay | body_battery |  | 94.483 | 5.517 | false | 0 | 2023-05-26 | 2026-02-05 | false | true | true | high |  |
| bodyBatteryEndOfDay | body_battery |  | 85.69 | 14.31 | false | 0 | 2023-05-26 | 2026-02-04 | true | true | true | high |  |
| sleepStartTimestampGMT | sleep | s | 81.724 | 18.276 | false | 0 | 2023-05-27 | 2026-02-05 | true | true | true | high | epoch seconds timestamp |
| sleepEndTimestampGMT | sleep | s | 81.724 | 18.276 | false | 0 | 2023-05-27 | 2026-02-05 | true | true | true | high | epoch seconds timestamp |
| deepSleepSeconds | sleep | Seconds | 81.724 | 18.276 | false | 0 | 2023-05-27 | 2026-02-05 | false | true | true | high |  |
| lightSleepSeconds | sleep | Seconds | 81.724 | 18.276 | false | 0 | 2023-05-27 | 2026-02-05 | false | true | true | high |  |
| remSleepSeconds | sleep | Seconds | 80.517 | 19.483 | false | 0 | 2023-05-27 | 2026-02-05 | false | true | true | high |  |
| awakeSleepSeconds | sleep | Seconds | 81.724 | 18.276 | false | 10.97 | 2023-05-27 | 2026-02-05 | false | true | true | high |  |
| averageRespiration | respiration | brpm | 79.483 | 20.517 | false | 0 | 2023-05-27 | 2026-02-05 | false | true | true | high |  |
| avgSleepStress | stress |  | 81.724 | 18.276 | false | 0 | 2023-05-27 | 2026-02-05 | false | true | true | high |  |
| sleepOverallScore | sleep |  | 81.552 | 18.448 | false | 0 | 2023-05-27 | 2026-02-05 | false | true | true | high |  |
| sleepQualityScore | sleep |  | 81.552 | 18.448 | false | 0 | 2023-05-27 | 2026-02-05 | false | true | true | high |  |
| sleepDurationScore | sleep |  | 81.552 | 18.448 | false | 0.211 | 2023-05-27 | 2026-02-05 | false | true | true | high |  |
| sleepRecoveryScore | sleep |  | 81.552 | 18.448 | false | 3.171 | 2023-05-27 | 2026-02-05 | false | true | true | high |  |

## Quality-relevant columns

| column | dtype | non_null_pct | missing_pct | first_non_null_date | last_non_null_date | coverage_within_span_pct | inferred_group | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sleepEndTimestampGMT | Int64 | 81.724 | 18.276 | 2023-05-27 | 2026-02-05 | 81.865 | sleep | epoch seconds timestamp |
| sleepStartTimestampGMT | Int64 | 81.724 | 18.276 | 2023-05-27 | 2026-02-05 | 81.865 | sleep | epoch seconds timestamp |
| bodyBatteryEndOfDay | Int64 | 85.69 | 14.31 | 2023-05-26 | 2026-02-04 | 85.838 | body_battery |  |
| restingHeartRate | Int64 | 93.621 | 6.379 | 2023-05-26 | 2026-02-05 | 93.621 | heart_rate |  |
| totalSteps | Int64 | 94.138 | 5.862 | 2023-05-26 | 2026-02-05 | 94.138 | steps_distance |  |
| maxHeartRate | Int64 | 94.483 | 5.517 | 2023-05-26 | 2026-02-05 | 94.483 | heart_rate |  |
| minHeartRate | Int64 | 94.483 | 5.517 | 2023-05-26 | 2026-02-05 | 94.483 | heart_rate |  |
| stressTotalDurationSeconds | Int64 | 100 | 0 | 2023-05-26 | 2026-02-05 | 100 | stress |  |

## Quality-readiness rationale

- Quality uses `8` core columns/flags.
- Non-null coverage across these columns ranges from `81.724%` to `100%`.
- Median non-null coverage across quality-relevant columns: `93.879%`.
- Lowest-coverage quality inputs (expected to drive many partial/bad labels): sleepEndTimestampGMT (81.724% non-null), sleepStartTimestampGMT (81.724% non-null)
- Use this table to justify threshold choices and explain why some labels are dominated by missing sleep/body-battery coverage rather than parser failures.

## Missingness summary (top 20)

| column | dtype | non_null_pct | missing_pct | is_constant | first_non_null_date | last_non_null_date | inferred_group | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abnormalHeartRateAlertsCount | Int64 | 9.655 | 90.345 | false | 2023-05-28 | 2023-11-04 | heart_rate |  |
| allDayStress_ASLEEP_highDuration | Int64 | 18.276 | 81.724 | false | 2023-05-28 | 2026-01-29 | stress |  |
| bodyBatteryStat_SLEEPEND | Int64 | 28.793 | 71.207 | false | 2024-11-17 | 2026-02-05 | body_battery |  |
| bodyBatteryStat_SLEEPEND_statTimestamp | str | 28.793 | 71.207 | false | 2024-11-17 | 2026-02-05 | body_battery | ISO datetime string |
| bodyBatteryStat_SLEEPEND_bodyBatteryStatus | str | 28.793 | 71.207 | true | 2024-11-17 | 2026-02-05 | body_battery |  |
| bodyBatteryStat_SLEEPSTART | Int64 | 29.828 | 70.172 | false | 2024-06-21 | 2026-02-05 | body_battery |  |
| bodyBatteryStat_SLEEPSTART_bodyBatteryStatus | str | 29.828 | 70.172 | true | 2024-06-21 | 2026-02-05 | body_battery |  |
| bodyBatteryStat_SLEEPSTART_statTimestamp | str | 29.828 | 70.172 | false | 2024-06-21 | 2026-02-05 | body_battery | ISO datetime string |
| respiration_algorithmVersion | Int64 | 36.207 | 63.793 | true | 2024-08-14 | 2026-02-05 | respiration |  |
| restingCaloriesFromActivity | Int64 | 43.621 | 56.379 | false | 2023-05-26 | 2026-01-31 | calories |  |
| hydration_capped | boolean | 43.793 | 56.207 | true | 2023-05-26 | 2026-01-31 | hydration |  |
| hydration_goalInML | Float64 | 43.793 | 56.207 | false | 2023-05-26 | 2026-01-31 | hydration |  |
| hydration_adjustedGoalInML | Float64 | 43.793 | 56.207 | false | 2023-05-26 | 2026-01-31 | hydration |  |
| hydration_lastEntryTimestampLocal | str | 43.793 | 56.207 | false | 2023-05-26 | 2026-01-31 | hydration | ISO datetime string |
| hydration_activityIntakeInML | Int64 | 43.793 | 56.207 | true | 2023-05-26 | 2026-01-31 | hydration |  |
| hydration_sweatLossInML | Int64 | 43.793 | 56.207 | false | 2023-05-26 | 2026-01-31 | hydration |  |
| hydration_valueInML | Int64 | 43.793 | 56.207 | true | 2023-05-26 | 2026-01-31 | hydration |  |
| allDayStress_ASLEEP_stressTooActiveCount | Int64 | 47.241 | 52.759 | false | 2023-05-28 | 2026-02-05 | stress |  |
| allDayStress_ASLEEP_activityDuration | Int64 | 47.241 | 52.759 | false | 2023-05-28 | 2026-02-05 | stress |  |
| bodyBatteryStat_DURINGSLEEP_statTimestamp | str | 47.241 | 52.759 | false | 2023-12-18 | 2026-02-05 | body_battery | ISO datetime string |

## Notes

- This is the short decision-support report (`summary` mode).
- Use `data_dictionary.md` (full mode) for complete column-by-group appendix.
