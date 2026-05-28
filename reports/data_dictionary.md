# Data Dictionary

Generated at (UTC): 2026-05-28T08:38:48.510159+00:00
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

## Missingness summary (top 30)

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
| bodyBatteryStat_DURINGSLEEP_bodyBatteryStatus | str | 52.437 | 47.563 | true | 2023-12-18 | 2026-05-18 | body_battery |  |
| bodyBatteryStat_DURINGSLEEP | Int64 | 52.437 | 47.563 | false | 2023-12-18 | 2026-05-18 | body_battery |  |
| remainingKilocalories | Int64 | 57.607 | 42.393 | false | 2023-05-26 | 2025-01-13 | calories |  |
| allDayStress_ASLEEP_mediumDuration | Int64 | 63.368 | 36.632 | false | 2023-05-27 | 2026-05-18 | stress |  |
| allDayStress_ASLEEP_stressOffWristCount | Int64 | 70.162 | 29.838 | false | 2023-05-27 | 2026-05-18 | stress |  |
| allDayStress_ASLEEP_uncategorizedDuration | Int64 | 70.162 | 29.838 | false | 2023-05-27 | 2026-05-18 | stress |  |
| isVigorousDay | boolean | 70.606 | 29.394 | false | 2023-12-13 | 2026-05-18 | other |  |
| spo2SleepAverageHR | float64 | 76.219 | 23.781 | false | 2023-05-28 | 2026-05-18 | sleep |  |
| spo2SleepMeasurementStartTimestampGMT | Int64 | 78.434 | 21.566 | false | 2023-05-28 | 2026-05-18 | sleep | epoch seconds timestamp |
| spo2SleepLowestSPO2 | Int64 | 78.434 | 21.566 | false | 2023-05-28 | 2026-05-18 | sleep |  |

## Columns by group

### body_battery

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bodyBatteryEndOfDay | Int64 | 86.263 | 13.737 | 49 | false | 0 | 2023-05-26 | 2026-05-17 | [36, 22, 19, 35, 24] | 5 | 5 | 6 | 14 | 22 | 36 | 72 |  |  |
| bodyBatteryHighest | Int64 | 94.978 | 5.022 | 86 | false | 0 | 2023-05-26 | 2026-05-18 | [70, 100, 93, 80, 82] | 5 | 33.1 | 67 | 82 | 95 | 100 | 100 |  |  |
| bodyBatteryLowest | Int64 | 94.978 | 5.022 | 38 | false | 0 | 2023-05-26 | 2026-05-18 | [36, 22, 8, 18, 24] | 5 | 5 | 5 | 7 | 15 | 25 | 80 |  |  |
| bodyBatteryStartOfDay | Int64 | 94.978 | 5.022 | 67 | false | 0 | 2023-05-26 | 2026-05-18 | [66, 36, 22, 19, 35] | 5 | 5 | 7 | 16 | 25 | 52 | 87 |  |  |
| bodyBatteryStat_DURINGSLEEP | Int64 | 52.437 | 47.563 | 76 | false | 0 | 2023-12-18 | 2026-05-18 | [60, 70, 37, 59, 71] | 1 | 32.7 | 61 | 71 | 80 | 91 | 95 |  |  |
| bodyBatteryStat_DURINGSLEEP_bodyBatteryStatus | str | 52.437 | 47.563 | 1 | true |  | 2023-12-18 | 2026-05-18 | ["MEASURED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_DURINGSLEEP_statTimestamp | str | 52.437 | 47.563 | 355 | false |  | 2023-12-18 | 2026-05-18 | ["2023-12-18T09:12:00.0", "2023-12-19T07:44:00.0", "2023-12-20T07:20:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_ENDOFDAY | Int64 | 86.263 | 13.737 | 49 | false | 0 | 2023-05-26 | 2026-05-17 | [36, 22, 19, 35, 24] | 5 | 5 | 6 | 14 | 22 | 36 | 72 |  |  |
| bodyBatteryStat_ENDOFDAY_bodyBatteryStatus | str | 86.263 | 13.737 | 2 | false |  | 2023-05-26 | 2026-05-17 | ["MEASURED", "MODELED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_ENDOFDAY_statTimestamp | str | 86.263 | 13.737 | 584 | false |  | 2023-05-26 | 2026-05-17 | ["2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "2023-05-28T22:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_HIGHEST | Int64 | 94.978 | 5.022 | 86 | false | 0 | 2023-05-26 | 2026-05-18 | [70, 100, 93, 80, 82] | 5 | 33.1 | 67 | 82 | 95 | 100 | 100 |  |  |
| bodyBatteryStat_HIGHEST_bodyBatteryStatus | str | 94.978 | 5.022 | 3 | false |  | 2023-05-26 | 2026-05-18 | ["MEASURED", "RESET", "MODELED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_HIGHEST_statTimestamp | str | 94.978 | 5.022 | 643 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T16:20:00.0", "2023-05-27T06:38:00.0", "2023-05-28T08:55:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_LOWEST | Int64 | 94.978 | 5.022 | 38 | false | 0 | 2023-05-26 | 2026-05-18 | [36, 22, 8, 18, 24] | 5 | 5 | 5 | 7 | 15 | 25 | 80 |  |  |
| bodyBatteryStat_LOWEST_bodyBatteryStatus | str | 94.978 | 5.022 | 3 | false |  | 2023-05-26 | 2026-05-18 | ["MEASURED", "MODELED", "RESET"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_LOWEST_statTimestamp | str | 94.978 | 5.022 | 642 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T21:55:00.0", "2023-05-27T21:57:00.0", "2023-05-28T00:50:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_MOSTRECENT | Int64 | 94.978 | 5.022 | 60 | false | 0 | 2023-05-26 | 2026-05-18 | [36, 22, 19, 35, 24] | 5 | 5 | 7 | 16 | 24 | 45 | 100 |  |  |
| bodyBatteryStat_MOSTRECENT_bodyBatteryStatus | str | 94.978 | 5.022 | 3 | false |  | 2023-05-26 | 2026-05-18 | ["MEASURED", "MODELED", "RESET"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_MOSTRECENT_statTimestamp | str | 94.978 | 5.022 | 643 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "2023-05-28T22:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_SLEEPEND | Int64 | 36.632 | 63.368 | 67 | false | 0 | 2024-11-17 | 2026-05-18 | [77, 83, 89, 56, 75] | 6 | 38.7 | 72 | 86 | 98 | 100 | 100 |  |  |
| bodyBatteryStat_SLEEPEND_bodyBatteryStatus | str | 36.632 | 63.368 | 1 | true |  | 2024-11-17 | 2026-05-18 | ["MEASURED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_SLEEPEND_statTimestamp | str | 36.632 | 63.368 | 248 | false |  | 2024-11-17 | 2026-05-18 | ["2024-11-17T11:34:00.0", "2024-11-18T07:51:00.0", "2024-11-19T07:46:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_SLEEPSTART | Int64 | 37.518 | 62.482 | 31 | false | 0 | 2024-06-21 | 2026-05-18 | [20, 5, 25, 22, 10] | 5 | 5 | 5 | 7 | 16 | 26.35 | 59 |  |  |
| bodyBatteryStat_SLEEPSTART_bodyBatteryStatus | str | 37.518 | 62.482 | 1 | true |  | 2024-06-21 | 2026-05-18 | ["MEASURED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_SLEEPSTART_statTimestamp | str | 37.518 | 62.482 | 254 | false |  | 2024-06-21 | 2026-05-18 | ["2024-06-20T23:16:00.0", "2024-08-08T21:12:00.0", "2024-08-09T23:39:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_STARTOFDAY | Int64 | 94.978 | 5.022 | 67 | false | 0 | 2023-05-26 | 2026-05-18 | [66, 36, 22, 19, 35] | 5 | 5 | 7 | 16 | 25 | 52 | 87 |  |  |
| bodyBatteryStat_STARTOFDAY_bodyBatteryStatus | str | 94.978 | 5.022 | 3 | false |  | 2023-05-26 | 2026-05-18 | ["RESET", "MEASURED", "MODELED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_STARTOFDAY_statTimestamp | str | 94.978 | 5.022 | 643 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T15:43:00.0", "2023-05-26T22:01:00.0", "2023-05-27T22:01:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBattery_bodyBatteryVersion | Int64 | 95.126 | 4.874 | 1 | true | 0 | 2023-05-26 | 2026-05-18 | [2] | 2 | 2 | 2 | 2 | 2 | 2 | 2 |  |  |
| bodyBattery_chargedValue | Int64 | 94.83 | 5.17 | 88 | false | 7.165 | 2023-05-26 | 2026-05-18 | [4, 65, 85, 84, 66] | 0 | 0 | 53 | 69.5 | 79 | 90 | 99 | percent |  |
| bodyBattery_drainedValue | Int64 | 94.83 | 5.17 | 93 | false | 0.935 | 2023-05-26 | 2026-05-18 | [34, 79, 88, 68, 77] | 0 | 14 | 50.25 | 68 | 79 | 90 | 98 | percent |  |

### calories

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activeKilocalories | Int64 | 100 | 0 | 446 | false | 7.09 | 2023-05-26 | 2026-05-18 | [199, 792, 698, 593, 351] | 0 | 0 | 113 | 286 | 517 | 873.8 | 2544 | Kilocalories |  |
| bmrKilocalories | Int64 | 100 | 0 | 104 | false | 0 | 2023-05-26 | 2026-05-18 | [1959, 1964, 1962, 1966, 1955] | 401 | 1680.8 | 1941 | 1965 | 2017 | 2023 | 2045 | Kilocalories |  |
| remainingKilocalories | Int64 | 57.607 | 42.393 | 316 | false | 0 | 2023-05-26 | 2025-01-13 | [2158, 2756, 2660, 2559, 2306] | 408 | 1901 | 2064.5 | 2241 | 2487.5 | 2889.5 | 4461 | Kilocalories |  |
| restingCaloriesFromActivity | Int64 | 42.984 | 57.016 | 105 | false | 0.344 | 2023-05-26 | 2026-05-18 | [0, 164, 50, 207, 157] | 0 | 17 | 24 | 38 | 64 | 141 | 653 | Kilocalories |  |
| totalKilocalories | Int64 | 100 | 0 | 480 | false | 0 | 2023-05-26 | 2026-05-18 | [2158, 2756, 2660, 2559, 2306] | 408 | 1901 | 2077 | 2257 | 2506 | 2872.2 | 4461 | Kilocalories |  |
| wellnessActiveKilocalories | Int64 | 100 | 0 | 446 | false | 7.09 | 2023-05-26 | 2026-05-18 | [199, 792, 698, 593, 351] | 0 | 0 | 113 | 286 | 517 | 873.8 | 2544 | Kilocalories |  |
| wellnessKilocalories | Int64 | 100 | 0 | 480 | false | 0 | 2023-05-26 | 2026-05-18 | [2158, 2756, 2660, 2559, 2306] | 408 | 1901 | 2077 | 2257 | 2506 | 2872.2 | 4461 | Kilocalories |  |
| wellnessTotalKilocalories | Int64 | 100 | 0 | 480 | false | 0 | 2023-05-26 | 2026-05-18 | [2158, 2756, 2660, 2559, 2306] | 408 | 1901 | 2077 | 2257 | 2506 | 2872.2 | 4461 | Kilocalories |  |

### flags_includes

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| includesActivityData | boolean | 100 | 0 | 2 | false |  | 2023-05-26 | 2026-05-18 | [true, false] |  |  |  |  |  |  |  |  |  |
| includesAllDayPulseOx | boolean | 100 | 0 | 2 | false |  | 2023-05-26 | 2026-05-18 | [false, true] |  |  |  |  |  |  |  |  |  |
| includesCalorieConsumedData | boolean | 100 | 0 | 1 | true |  | 2023-05-26 | 2026-05-18 | [false] |  |  |  |  |  |  |  |  |  |
| includesContinuousMeasurement | boolean | 100 | 0 | 1 | true |  | 2023-05-26 | 2026-05-18 | [false] |  |  |  |  |  |  |  |  |  |
| includesSingleMeasurement | boolean | 100 | 0 | 2 | false |  | 2023-05-26 | 2026-05-18 | [true, false] |  |  |  |  |  |  |  |  |  |
| includesSleepPulseOx | boolean | 100 | 0 | 2 | false |  | 2023-05-26 | 2026-05-18 | [false, true] |  |  |  |  |  |  |  |  |  |
| includesWellnessData | boolean | 100 | 0 | 1 | true |  | 2023-05-26 | 2026-05-18 | [true] |  |  |  |  |  |  |  |  |  |

### heart_rate

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abnormalHeartRateAlertsCount | Int64 | 8.272 | 91.728 | 10 | false | 0 | 2023-05-28 | 2023-11-04 | [3, 8, 1, 4, 6] | 1 | 1 | 1 | 2 | 3.25 | 7.25 | 18 | bpm |  |
| currentDayRestingHeartRate | Int64 | 94.239 | 5.761 | 27 | false | 0 | 2023-05-26 | 2026-05-18 | [63, 44, 43, 40, 42] | 36 | 39 | 43 | 45 | 47 | 51 | 86 | bpm |  |
| maxAvgHeartRate | Int64 | 94.978 | 5.022 | 97 | false | 0 | 2023-05-26 | 2026-05-18 | [126, 160, 175, 119, 120] | 69 | 97 | 116.5 | 130 | 145 | 162.9 | 183 | bpm |  |
| maxHeartRate | Int64 | 94.978 | 5.022 | 90 | false | 0 | 2023-05-26 | 2026-05-18 | [126, 160, 175, 119, 120] | 74 | 99.1 | 120 | 134 | 148 | 165.9 | 183 | bpm |  |
| minAvgHeartRate | Int64 | 94.978 | 5.022 | 41 | false | 0 | 2023-05-26 | 2026-05-18 | [55, 41, 40, 42, 39] | 31 | 38 | 41 | 43 | 46 | 56.9 | 77 | bpm |  |
| minHeartRate | Int64 | 94.978 | 5.022 | 39 | false | 0 | 2023-05-26 | 2026-05-18 | [55, 41, 40, 39, 38] | 31 | 38 | 40 | 42 | 45 | 55.9 | 76 | bpm |  |
| restingHeartRate | Int64 | 94.239 | 5.761 | 24 | false | 0 | 2023-05-26 | 2026-05-18 | [63, 54, 50, 48, 47] | 39 | 41 | 43 | 45 | 47 | 50 | 86 | bpm |  |
| restingHeartRateTimestamp | Int64 | 94.239 | 5.761 | 638 | false | 0 | 2023-05-26 | 2026-05-18 | [1685138400000, 1685224800000, 1685311200000, 1685397600000, 1685484000000] | 1685138400000 | 1687890240000 | 1699074000000 | 1717927200000 | 1762448400000 | 1775948382000 | 1779101460000 | ms | epoch millis |

### hydration

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hydration_activityIntakeInML | Int64 | 43.131 | 56.869 | 1 | true | 100 | 2023-05-26 | 2026-05-18 | [0] | 0 | 0 | 0 | 0 | 0 | 0 | 0 | mL |  |
| hydration_adjustedGoalInML | Float64 | 43.131 | 56.869 | 211 | false | 0 | 2023-05-26 | 2026-05-18 | [2847.056, 3691.0, 3101.0, 3863.0, 3674.0] | 2840 | 2906.55 | 2950 | 3003 | 3113.75 | 3502.85 | 5808 | mL |  |
| hydration_capped | boolean | 43.131 | 56.869 | 1 | true |  | 2023-05-26 | 2026-05-18 | [false] |  |  |  |  |  |  |  |  |  |
| hydration_goalInML | Float64 | 43.131 | 56.869 | 2 | false | 0 | 2023-05-26 | 2026-05-18 | [2839.056, 2840.0] | 2839.06 | 2840 | 2840 | 2840 | 2840 | 2840 | 2840 | mL |  |
| hydration_lastEntryTimestampLocal | str | 43.131 | 56.869 | 292 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T17:50:43.0", "2023-05-27T17:07:24.0", "2023-05-28T18:34:30.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| hydration_sweatLossInML | Int64 | 43.131 | 56.869 | 211 | false | 0.685 | 2023-05-26 | 2026-05-18 | [8, 851, 261, 1023, 834] | 0 | 66.55 | 110 | 163 | 273.75 | 662.85 | 2968 | mL |  |
| hydration_valueInML | Int64 | 43.131 | 56.869 | 1 | true | 100 | 2023-05-26 | 2026-05-18 | [0] | 0 | 0 | 0 | 0 | 0 | 0 | 0 | mL |  |

### other

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activeSeconds | Int64 | 100 | 0 | 616 | false | 5.761 | 2023-05-26 | 2026-05-18 | [1285, 6453, 1321, 5498, 3372] | 0 | 0 | 1120 | 2864 | 5078 | 9684.6 | 30402 | Seconds |  |
| awakeCount | Int64 | 82.127 | 17.873 | 7 | false | 45.504 | 2023-05-27 | 2026-05-18 | [0, 2, 1, 4, 3] | 0 | 0 | 0 | 1 | 1 | 3 | 7 |  |  |
| dailyStepGoal | Int64 | 100 | 0 | 361 | false | 0 | 2023-05-26 | 2026-05-18 | [7500, 8000, 8540, 7810, 7190] | 3120 | 4910 | 6020 | 7390 | 8590 | 10792 | 13470 |  |  |
| durationInMilliseconds | Int64 | 100 | 0 | 49 | false | 0 | 2023-05-26 | 2026-05-18 | [86400000, 80580000, 73860000, 63420000, 35520000] | 18240000 | 72576000 | 86400000 | 86400000 | 86400000 | 86400000 | 90000000 | Milliseconds |  |
| highlyActiveSeconds | Int64 | 100 | 0 | 467 | false | 6.204 | 2023-05-26 | 2026-05-18 | [797, 5638, 2700, 3993, 1751] | 0 | 0 | 87 | 275 | 1078 | 3043 | 6664 | Seconds |  |
| isVigorousDay | boolean | 70.606 | 29.394 | 2 | false |  | 2023-12-13 | 2026-05-18 | [false, true] |  |  |  |  |  |  |  |  |  |
| moderateIntensityMinutes | Int64 | 100 | 0 | 96 | false | 23.486 | 2023-05-26 | 2026-05-18 | [0, 113, 38, 135, 29] | 0 | 0 | 1 | 19 | 39 | 75 | 220 |  |  |
| restlessMomentCount | Int64 | 82.127 | 17.873 | 75 | false | 0 | 2023-05-27 | 2026-05-18 | [40, 36, 65, 67, 45] | 7 | 22 | 34 | 42 | 53 | 71.25 | 109 |  |  |
| retro | boolean | 82.127 | 17.873 | 1 | true |  | 2023-05-27 | 2026-05-18 | [false] |  |  |  |  |  |  |  |  |  |
| unmeasurableSeconds | Int64 | 82.127 | 17.873 | 27 | false | 87.59 | 2023-05-27 | 2026-05-18 | [0, 480, 900, 780, 540] | 0 | 0 | 0 | 0 | 0 | 1035 | 4200 | Seconds |  |
| userFloorsAscendedGoal | Int64 | 100 | 0 | 1 | true | 0 | 2023-05-26 | 2026-05-18 | [10] | 10 | 10 | 10 | 10 | 10 | 10 | 10 |  |  |
| userIntensityMinutesGoal | Int64 | 100 | 0 | 3 | false | 0 | 2023-05-26 | 2026-05-18 | [150, 300, 400] | 150 | 400 | 400 | 400 | 400 | 400 | 400 |  |  |
| vigorousIntensityMinutes | Int64 | 100 | 0 | 35 | false | 51.846 | 2023-05-26 | 2026-05-18 | [5, 8, 27, 0, 21] | 0 | 0 | 0 | 0 | 4 | 19 | 89 |  |  |
| wellnessEndTimeGmt | str | 100 | 0 | 677 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "2023-05-28T22:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| wellnessEndTimeLocal | str | 100 | 0 | 677 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-27T00:00:00.0", "2023-05-28T00:00:00.0", "2023-05-29T00:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| wellnessStartTimeGmt | str | 100 | 0 | 677 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-25T22:00:00.0", "2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| wellnessStartTimeLocal | str | 100 | 0 | 677 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T00:00:00.0", "2023-05-27T00:00:00.0", "2023-05-28T00:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |

### respiration

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| averageRespiration | float64 | 80.059 | 19.941 | 152 | false | 0 | 2023-05-27 | 2026-05-18 | [16.0, 15.0, 17.0, 18.0, 14.0] | 13 | 14.991 | 15.085 | 16 | 16.657 | 17.718 | 19 | brpm |  |
| highestRespiration | float64 | 80.059 | 19.941 | 11 | false | 0 | 2023-05-27 | 2026-05-18 | [22.0, 20.0, 24.0, 23.0, 21.0] | 17 | 20 | 21 | 22 | 23 | 25 | 27 | brpm |  |
| lowestRespiration | float64 | 80.059 | 19.941 | 8 | false | 0 | 2023-05-27 | 2026-05-18 | [12.0, 9.0, 11.0, 10.0, 13.0] | 7 | 8 | 9 | 10 | 11 | 12 | 14 | brpm |  |
| respiration_algorithmVersion | Int64 | 45.052 | 54.948 | 1 | true | 0 | 2024-08-14 | 2026-05-18 | [100] | 100 | 100 | 100 | 100 | 100 | 100 | 100 |  |  |
| respiration_avgWakingRespirationValue | Int64 | 94.83 | 5.17 | 8 | false | 0 | 2023-05-26 | 2026-05-18 | [13, 14, 15, 17, 16] | 11 | 13 | 13 | 14 | 14 | 15 | 18 | brpm |  |
| respiration_highestRespirationValue | Int64 | 94.83 | 5.17 | 14 | false | 0 | 2023-05-26 | 2026-05-18 | [15, 22, 20, 24, 23] | 12 | 20 | 21 | 22 | 23 | 25 | 27 | brpm |  |
| respiration_latestRespirationTimeGMT | str | 94.83 | 5.17 | 642 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T21:59:00.0", "2023-05-27T22:00:00.0", "2023-05-28T20:14:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| respiration_latestRespirationValue | Int64 | 94.83 | 5.17 | 14 | false | 0 | 2023-05-26 | 2026-05-18 | [14, 13, 15, 12, 16] | 9 | 12 | 13 | 14 | 15 | 19 | 22 | brpm |  |
| respiration_lowestRespirationValue | Int64 | 94.83 | 5.17 | 8 | false | 0 | 2023-05-26 | 2026-05-18 | [8, 11, 10, 9, 12] | 7 | 8 | 9 | 9 | 10 | 11 | 16 | brpm |  |

### sleep

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| awakeSleepSeconds | Int64 | 82.127 | 17.873 | 83 | false | 11.691 | 2023-05-27 | 2026-05-18 | [240, 1200, 720, 3960, 1680] | 0 | 0 | 120 | 600 | 1560 | 3870 | 9660 | Seconds |  |
| deepSleepSeconds | Int64 | 82.127 | 17.873 | 115 | false | 0.18 | 2023-05-27 | 2026-05-18 | [5220, 6120, 6420, 4320, 7200] | 0 | 3300 | 4860 | 5880 | 6795 | 8160 | 10140 | Seconds |  |
| lightSleepSeconds | Int64 | 82.127 | 17.873 | 256 | false | 0 | 2023-05-27 | 2026-05-18 | [16260, 14700, 19860, 14460, 21000] | 3660 | 9045 | 13740 | 16440 | 19320 | 24000 | 29400 | Seconds |  |
| remSleepSeconds | Int64 | 80.945 | 19.055 | 183 | false | 0 | 2023-05-27 | 2026-05-18 | [6720, 4620, 4740, 6180, 9300] | 120 | 2580 | 5205 | 7110 | 8880 | 11580 | 17400 | Seconds |  |
| sleepAwakeTimeScore | Int64 | 81.979 | 18.021 | 71 | false | 1.622 | 2023-05-27 | 2026-05-18 | [100, 80, 91, 34, 70] | 0 | 34 | 74 | 93 | 100 | 100 | 100 |  |  |
| sleepAwakeningsCountScore | Int64 | 81.979 | 18.021 | 6 | false | 0.721 | 2023-05-27 | 2026-05-18 | [100, 74, 87, 32, 61] | 0 | 61 | 87 | 87 | 100 | 100 | 100 |  |  |
| sleepCombinedAwakeScore | Int64 | 81.979 | 18.021 | 71 | false | 0.18 | 2023-05-27 | 2026-05-18 | [100, 77, 89, 33, 78] | 0 | 41.4 | 77 | 91 | 100 | 100 | 100 |  |  |
| sleepDeepScore | Int64 | 81.536 | 18.464 | 41 | false | 0 | 2023-05-27 | 2026-05-18 | [93, 100, 87, 96, 79] | 30 | 71 | 80 | 100 | 100 | 100 | 100 |  |  |
| sleepDurationScore | Int64 | 81.979 | 18.021 | 69 | false | 0.18 | 2023-05-27 | 2026-05-18 | [100, 79, 77, 53, 61] | 0 | 50.7 | 80.5 | 100 | 100 | 100 | 100 |  |  |
| sleepEndTimestampGMT | Int64 | 82.127 | 17.873 | 556 | false | 0 | 2023-05-27 | 2026-05-18 | [1685176920, 1685264159, 1685352240, 1685433900, 1685530018] | 1685176920 | 1687568880 | 1698368550 | 1716151320 | 1762176750 | 1775737410 | 1779085200 | s | epoch seconds timestamp |
| sleepFeedback | str | 82.127 | 17.873 | 31 | false |  | 2023-05-27 | 2026-05-18 | ["POSITIVE_HIGHLY_RECOVERING", "POSITIVE_RECOVERING", "NEGATIVE_LONG_BUT_DISC... |  |  |  |  |  |  |  |  |  |
| sleepInsight | str | 82.127 | 17.873 | 10 | false |  | 2023-05-27 | 2026-05-18 | ["NONE", "POSITIVE_LATE_BED_TIME", "POSITIVE_RESTFUL_DAY", "NEGATIVE_LATE_BED... |  |  |  |  |  |  |  |  |  |
| sleepInterruptionsScore | Int64 | 81.979 | 18.021 | 69 | false | 0 | 2023-05-27 | 2026-05-18 | [95, 78, 83, 86, 40] | 12 | 48 | 76 | 89 | 97 | 100 | 100 |  |  |
| sleepLightScore | Int64 | 81.536 | 18.464 | 45 | false | 0 | 2023-05-27 | 2026-05-18 | [92, 91, 80, 94, 77] | 26 | 71 | 84 | 94 | 100 | 100 | 100 |  |  |
| sleepOverallScore | Int64 | 81.979 | 18.021 | 64 | false | 0 | 2023-05-27 | 2026-05-18 | [98, 82, 90, 85, 69] | 18 | 49 | 77 | 84 | 90 | 97 | 100 |  |  |
| sleepQualityScore | Int64 | 81.979 | 18.021 | 56 | false | 0 | 2023-05-27 | 2026-05-18 | [97, 88, 89, 93, 75] | 29 | 60 | 78 | 85 | 91 | 97 | 100 |  |  |
| sleepRecoveryScore | Int64 | 81.979 | 18.021 | 50 | false | 3.964 | 2023-05-27 | 2026-05-18 | [100, 87, 99, 79, 84] | 0 | 44.2 | 71 | 79 | 93 | 100 | 100 |  |  |
| sleepRemScore | Int64 | 81.536 | 18.464 | 63 | false | 0.725 | 2023-05-27 | 2026-05-18 | [99, 74, 69, 100, 73] | 0 | 57 | 74 | 82 | 99 | 100 | 100 |  |  |
| sleepRestfulnessScore | Int64 | 81.979 | 18.021 | 61 | false | 0.18 | 2023-05-27 | 2026-05-18 | [79, 84, 64, 78, 73] | 0 | 57 | 73 | 83 | 92 | 100 | 100 |  |  |
| sleepStartTimestampGMT | Int64 | 82.127 | 17.873 | 556 | false | 0 | 2023-05-27 | 2026-05-18 | [1685148480, 1685236980, 1685320500, 1685408220, 1685488500] | 1685148480 | 1687546815 | 1698336015 | 1716111960 | 1762148205 | 1775705430 | 1779063720 | s | epoch seconds timestamp |
| sleepWindowConfirmationType | str | 82.127 | 17.873 | 1 | true |  | 2023-05-27 | 2026-05-18 | ["ENHANCED_CONFIRMED_FINAL"] |  |  |  |  |  |  |  |  |  |
| spo2SleepAverageHR | float64 | 76.219 | 23.781 | 30 | false | 0 | 2023-05-28 | 2026-05-18 | [50.0, 48.0, 45.0, 46.0, 47.0] | 40 | 45 | 48 | 51 | 54 | 60 | 78 | bpm |  |
| spo2SleepAverageSPO2 | float64 | 78.434 | 21.566 | 164 | false | 0 | 2023-05-28 | 2026-05-18 | [94.0, 92.0, 91.0, 93.0, 96.0] | 89 | 92 | 93.465 | 94.18 | 95 | 96.575 | 99 | percent |  |
| spo2SleepLowestSPO2 | Int64 | 78.434 | 21.566 | 21 | false | 0 | 2023-05-28 | 2026-05-18 | [83, 82, 84, 87, 86] | 74 | 78 | 82 | 84 | 86 | 89 | 94 | percent |  |
| spo2SleepMeasurementEndTimestampGMT | Int64 | 78.434 | 21.566 | 531 | false | 0 | 2023-05-28 | 2026-05-18 | [1685253540, 1685339940, 1685426400, 1685512800, 1685599140] | 1685253540 | 1687548240 | 1699297140 | 1717826340 | 1762714230 | 1775843970 | 1779084000 | s | epoch seconds timestamp |
| spo2SleepMeasurementStartTimestampGMT | Int64 | 78.434 | 21.566 | 531 | false | 0 | 2023-05-28 | 2026-05-18 | [1685237040, 1685320560, 1685408280, 1685488560, 1685577240] | 1685237040 | 1687522170 | 1699277580 | 1717807080 | 1762687950 | 1775815740 | 1779063780 | s | epoch seconds timestamp |

### spo2

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| averageSpo2Value | Int64 | 85.229 | 14.771 | 9 | false | 0 | 2023-05-28 | 2026-05-18 | [93, 92, 96, 95, 94] | 89 | 92 | 93 | 94 | 95 | 96 | 98 | percent |  |
| latestSpo2Value | Int64 | 85.524 | 14.476 | 22 | false | 0 | 2023-05-26 | 2026-05-18 | [97, 99, 95, 89, 84] | 78 | 87 | 92 | 95 | 98 | 100 | 100 | percent |  |
| latestSpo2ValueReadingTimeGmt | str | 85.524 | 14.476 | 579 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T17:33:00.0", "2023-05-27T17:50:00.0", "2023-05-28T05:59:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| latestSpo2ValueReadingTimeLocal | str | 85.524 | 14.476 | 579 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T19:33:00.0", "2023-05-27T19:50:00.0", "2023-05-28T07:59:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| lowestSpo2Value | Int64 | 85.524 | 14.476 | 23 | false | 0 | 2023-05-26 | 2026-05-18 | [95, 93, 83, 82, 84] | 71 | 78 | 82 | 84 | 86 | 88 | 95 | percent |  |

### steps_distance

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| floorsAscendedInMeters | Float64 | 100 | 0 | 454 | false | 21.418 | 2023-05-26 | 2026-05-18 | [0.0, 72.336, 10.617, 73.152, 25.298] | 0 | 0 | 3.518 | 27.432 | 46.75 | 91.6 | 1099.29 | Meters |  |
| floorsDescendedInMeters | Float64 | 100 | 0 | 532 | false | 21.566 | 2023-05-26 | 2026-05-18 | [0.0, 63.324, 11.024, 89.929, 17.887] | 0 | 0 | 2.805 | 24.142 | 44.579 | 88.36 | 1117.69 | Meters |  |
| totalDistanceMeters | Int64 | 94.682 | 5.318 | 624 | false | 0 | 2023-05-26 | 2026-05-18 | [863, 17337, 5044, 14366, 7196] | 7 | 265 | 2205 | 4530 | 7825 | 13052 | 35155 | Meters |  |
| totalSteps | Int64 | 94.682 | 5.318 | 625 | false | 0 | 2023-05-26 | 2026-05-18 | [1096, 20915, 5935, 17593, 9212] | 9 | 337 | 2913 | 5812 | 9919 | 16973 | 46718 |  |  |
| wellnessDistanceMeters | Int64 | 94.682 | 5.318 | 624 | false | 0 | 2023-05-26 | 2026-05-18 | [863, 17337, 5044, 14366, 7196] | 7 | 265 | 2205 | 4530 | 7825 | 13052 | 35155 | Meters |  |

### stress

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| allDayStress_ASLEEP_activityDuration | Int64 | 47.858 | 52.142 | 13 | false | 0 | 2023-05-28 | 2026-05-13 | [300, 180, 60, 240, 360] | 60 | 60 | 60 | 120 | 180 | 411 | 3960 |  |  |
| allDayStress_ASLEEP_averageStressLevel | Int64 | 81.241 | 18.759 | 41 | false | 0 | 2023-05-27 | 2026-05-18 | [6, 9, 8, 5, 11] | 3 | 6 | 10 | 14 | 18 | 27 | 70 |  |  |
| allDayStress_ASLEEP_averageStressLevelIntensity | Int64 | 81.241 | 18.759 | 33 | false | 0 | 2023-05-27 | 2026-05-18 | [6, 9, 8, 11, 10] | 4 | 7 | 10 | 13 | 17 | 23 | 69 |  |  |
| allDayStress_ASLEEP_highDuration | Int64 | 21.566 | 78.434 | 21 | false | 0 | 2023-05-28 | 2026-05-14 | [60, 120, 240, 180, 600] | 60 | 60 | 60 | 120 | 345 | 1035 | 5760 |  |  |
| allDayStress_ASLEEP_lowDuration | Int64 | 80.207 | 19.793 | 143 | false | 0 | 2023-05-27 | 2026-05-18 | [240, 1080, 1380, 300, 1800] | 60 | 180 | 780 | 1860 | 3840 | 8580 | 15960 |  |  |
| allDayStress_ASLEEP_maxStressLevel | Int64 | 81.241 | 18.759 | 75 | false | 0 | 2023-05-27 | 2026-05-18 | [51, 89, 54, 30, 45] | 16 | 35.45 | 54 | 66 | 76 | 89 | 97 |  |  |
| allDayStress_ASLEEP_mediumDuration | Int64 | 63.368 | 36.632 | 56 | false | 0 | 2023-05-27 | 2026-05-18 | [60, 240, 660, 540, 360] | 60 | 60 | 120 | 300 | 780 | 2316 | 15360 |  |  |
| allDayStress_ASLEEP_restDuration | Int64 | 81.241 | 18.759 | 316 | false | 0 | 2023-05-27 | 2026-05-18 | [27960, 24600, 29880, 25320, 38640] | 60 | 11328 | 21615 | 25800 | 29580 | 34620 | 40140 |  |  |
| allDayStress_ASLEEP_stressDuration | Int64 | 80.355 | 19.645 | 163 | false | 0 | 2023-05-27 | 2026-05-18 | [300, 1380, 1440, 1800, 360] | 60 | 240 | 900 | 2040 | 4560 | 10911 | 28140 |  |  |
| allDayStress_ASLEEP_stressIntensityCount | Int64 | 81.241 | 18.759 | 294 | false | 0 | 2023-05-27 | 2026-05-18 | [471, 433, 522, 427, 674] | 13 | 278.7 | 423.25 | 485 | 538 | 626.1 | 767 |  |  |
| allDayStress_ASLEEP_stressOffWristCount | Int64 | 70.162 | 29.838 | 70 | false | 0 | 2023-05-27 | 2026-05-18 | [4, 15, 5, 2, 17] | 1 | 1 | 4 | 11 | 24.5 | 55.3 | 98 |  |  |
| allDayStress_ASLEEP_stressTooActiveCount | Int64 | 47.858 | 52.142 | 13 | false | 0 | 2023-05-28 | 2026-05-13 | [5, 3, 1, 4, 6] | 1 | 1 | 1 | 2 | 3 | 6.85 | 66 |  |  |
| allDayStress_ASLEEP_totalDuration | Int64 | 81.241 | 18.759 | 289 | false | 0 | 2023-05-27 | 2026-05-18 | [28500, 27180, 31800, 25740, 41520] | 780 | 17601 | 26355 | 30120 | 33300 | 38613 | 49260 |  |  |
| allDayStress_ASLEEP_totalStressCount | Int64 | 81.241 | 18.759 | 289 | false | 0 | 2023-05-27 | 2026-05-18 | [475, 453, 530, 429, 692] | 13 | 293.35 | 439.25 | 502 | 555 | 643.55 | 821 |  |  |
| allDayStress_ASLEEP_totalStressIntensity | Int64 | 81.241 | 18.759 | 548 | false | 0 | 2023-05-27 | 2026-05-18 | [36558, 27751, 36026, 33586, 38653] | -17133 | 1933.95 | 15383.75 | 22134 | 30074.5 | 39125.25 | 52940 |  |  |
| allDayStress_ASLEEP_uncategorizedDuration | Int64 | 70.162 | 29.838 | 70 | false | 0 | 2023-05-27 | 2026-05-18 | [240, 900, 300, 120, 1020] | 60 | 60 | 240 | 660 | 1470 | 3318 | 5880 |  |  |
| allDayStress_AWAKE_activityDuration | Int64 | 94.83 | 5.17 | 284 | false | 0 | 2023-05-26 | 2026-05-18 | [5580, 17100, 9840, 14760, 12120] | 60 | 1623 | 6060 | 9420 | 12600 | 18477 | 64320 |  |  |
| allDayStress_AWAKE_averageStressLevel | Int64 | 94.83 | 5.17 | 71 | false | 0 | 2023-05-26 | 2026-05-18 | [50, 41, 58, 36, 38] | 8 | 35 | 46 | 56 | 64 | 77 | 91 |  |  |
| allDayStress_AWAKE_averageStressLevelIntensity | Int64 | 94.83 | 5.17 | 71 | false | 0 | 2023-05-26 | 2026-05-18 | [43, 33, 55, 30, 31] | 9 | 25.05 | 43 | 54 | 64 | 76 | 91 |  |  |
| allDayStress_AWAKE_highDuration | Int64 | 93.796 | 6.204 | 307 | false | 0 | 2023-05-26 | 2026-05-18 | [3120, 3660, 14340, 1200, 4860] | 60 | 1242 | 5610 | 9420 | 14790 | 24120 | 47580 |  |  |
| allDayStress_AWAKE_lowDuration | Int64 | 94.239 | 5.761 | 300 | false | 0 | 2023-05-26 | 2026-05-18 | [3660, 9420, 9660, 12420, 14340] | 60 | 1440 | 6060 | 10290 | 14085 | 20289 | 28980 |  |  |
| allDayStress_AWAKE_maxStressLevel | Int64 | 94.83 | 5.17 | 22 | false | 0 | 2023-05-26 | 2026-05-18 | [96, 97, 99, 90, 98] | 30 | 90 | 97 | 99 | 99 | 99 | 100 |  |  |
| allDayStress_AWAKE_mediumDuration | Int64 | 94.682 | 5.318 | 276 | false | 0 | 2023-05-26 | 2026-05-18 | [4740, 9420, 6780, 7680, 7860] | 60 | 2100 | 7800 | 10680 | 13980 | 19140 | 31500 |  |  |
| allDayStress_AWAKE_restDuration | Int64 | 91.581 | 8.419 | 265 | false | 0 | 2023-05-26 | 2026-05-18 | [3420, 13440, 7200, 15000, 18900] | 60 | 240 | 2025 | 4800 | 10020 | 25083 | 46980 |  |  |
| allDayStress_AWAKE_stressDuration | Int64 | 94.83 | 5.17 | 404 | false | 0 | 2023-05-26 | 2026-05-18 | [11520, 22500, 30780, 21300, 27060] | 120 | 10215 | 26835 | 33030 | 38280 | 46494 | 72780 |  |  |
| allDayStress_AWAKE_stressIntensityCount | Int64 | 94.83 | 5.17 | 413 | false | 0 | 2023-05-26 | 2026-05-18 | [249, 599, 633, 605, 766] | 2 | 256.4 | 569.25 | 666 | 753 | 937.65 | 1399 |  |  |
| allDayStress_AWAKE_stressOffWristCount | Int64 | 99.705 | 0.295 | 230 | false | 0 | 2023-05-26 | 2026-05-18 | [26, 55, 174, 48, 36] | 1 | 12.7 | 29 | 49 | 102 | 768.6 | 1440 |  |  |
| allDayStress_AWAKE_stressTooActiveCount | Int64 | 94.83 | 5.17 | 284 | false | 0 | 2023-05-26 | 2026-05-18 | [93, 285, 164, 246, 202] | 1 | 27.05 | 101 | 157 | 210 | 307.95 | 1072 |  |  |
| allDayStress_AWAKE_totalDuration | Int64 | 100 | 0 | 389 | false | 0 | 2023-05-26 | 2026-05-18 | [22080, 56340, 58260, 53940, 60240] | 1080 | 26112 | 49920 | 54960 | 60180 | 85992 | 89820 |  |  |
| allDayStress_AWAKE_totalStressCount | Int64 | 100 | 0 | 389 | false | 0 | 2023-05-26 | 2026-05-18 | [368, 939, 971, 899, 1004] | 18 | 435.2 | 832 | 916 | 1003 | 1433.2 | 1497 |  |  |
| allDayStress_AWAKE_totalStressIntensity | Int64 | 94.83 | 5.17 | 640 | false | 0 | 2023-05-26 | 2026-05-18 | [-6142, -6824, -26075, -4452, -6960] | -76210 | -44417.6 | -32706.5 | -23599.5 | -14148.75 | -596.4 | 45292 |  |  |
| allDayStress_AWAKE_uncategorizedDuration | Int64 | 99.705 | 0.295 | 230 | false | 0 | 2023-05-26 | 2026-05-18 | [1560, 3300, 10440, 2880, 2160] | 60 | 762 | 1740 | 2940 | 6120 | 46116 | 86400 |  |  |
| allDayStress_TOTAL_activityDuration | Int64 | 94.83 | 5.17 | 284 | false | 0 | 2023-05-26 | 2026-05-18 | [5580, 17100, 10140, 14940, 12120] | 60 | 1800 | 6180 | 9660 | 12825 | 18537 | 64320 |  |  |
| allDayStress_TOTAL_averageStressLevel | Int64 | 94.83 | 5.17 | 68 | false | 0 | 2023-05-26 | 2026-05-18 | [50, 25, 38, 23, 26] | 8 | 25.05 | 33 | 38 | 45 | 60.95 | 91 |  |  |
| allDayStress_TOTAL_averageStressLevelIntensity | Int64 | 94.83 | 5.17 | 62 | false | 0 | 2023-05-26 | 2026-05-18 | [43, 18, 25, 20, 22] | 9 | 20 | 24 | 27.5 | 37 | 60.9 | 91 |  |  |
| allDayStress_TOTAL_highDuration | Int64 | 93.796 | 6.204 | 307 | false | 0 | 2023-05-26 | 2026-05-18 | [3120, 3660, 14400, 1200, 4860] | 60 | 1242 | 5700 | 9540 | 14790 | 24180 | 47580 |  |  |
| allDayStress_TOTAL_lowDuration | Int64 | 94.239 | 5.761 | 328 | false | 0 | 2023-05-26 | 2026-05-18 | [3660, 9660, 10740, 13800, 14640] | 60 | 2673 | 7935 | 12360 | 17040 | 24249 | 34740 |  |  |
| allDayStress_TOTAL_maxStressLevel | Int64 | 94.83 | 5.17 | 22 | false | 0 | 2023-05-26 | 2026-05-18 | [96, 97, 99, 90, 98] | 30 | 90 | 97 | 99 | 99 | 99 | 100 |  |  |
| allDayStress_TOTAL_mediumDuration | Int64 | 94.682 | 5.318 | 276 | false | 0 | 2023-05-26 | 2026-05-18 | [4740, 9480, 7020, 7740, 7860] | 60 | 2220 | 8100 | 11160 | 14520 | 19800 | 31620 |  |  |
| allDayStress_TOTAL_restDuration | Int64 | 92.762 | 7.238 | 380 | false | 0 | 2023-05-26 | 2026-05-18 | [3420, 41400, 31800, 44880, 44220] | 60 | 3564 | 24885 | 30510 | 35940 | 43377 | 59160 |  |  |
| allDayStress_TOTAL_stressDuration | Int64 | 94.83 | 5.17 | 407 | false | 0 | 2023-05-26 | 2026-05-18 | [11520, 22800, 32160, 22740, 27360] | 120 | 11712 | 28815 | 35880 | 41865 | 52557 | 72780 |  |  |
| allDayStress_TOTAL_stressIntensityCount | Int64 | 94.83 | 5.17 | 403 | false | 0 | 2023-05-26 | 2026-05-18 | [249, 1070, 1066, 1127, 1193] | 2 | 378.05 | 1024 | 1143.5 | 1223.75 | 1313.95 | 1399 |  |  |
| allDayStress_TOTAL_stressOffWristCount | Int64 | 99.852 | 0.148 | 232 | false | 0 | 2023-05-26 | 2026-05-18 | [26, 59, 189, 53, 38] | 1 | 18.75 | 42 | 66.5 | 118.25 | 782.25 | 1440 |  |  |
| allDayStress_TOTAL_stressTooActiveCount | Int64 | 94.83 | 5.17 | 284 | false | 0 | 2023-05-26 | 2026-05-18 | [93, 285, 169, 249, 202] | 1 | 30 | 103 | 161 | 213.75 | 308.95 | 1072 |  |  |
| allDayStress_TOTAL_totalDuration | Int64 | 100 | 0 | 193 | false | 0 | 2023-05-26 | 2026-05-18 | [22080, 84840, 85440, 85740, 85980] | 1080 | 32328 | 83760 | 85680 | 86160 | 86400 | 89820 |  |  |
| allDayStress_TOTAL_totalStressCount | Int64 | 100 | 0 | 193 | false | 0 | 2023-05-26 | 2026-05-18 | [368, 1414, 1424, 1429, 1433] | 18 | 538.8 | 1396 | 1428 | 1436 | 1440 | 1497 |  |  |
| allDayStress_TOTAL_totalStressIntensity | Int64 | 94.83 | 5.17 | 641 | false | 0 | 2023-05-26 | 2026-05-18 | [-6142, 29734, 1676, 31574, 26626] | -76210 | -34003.2 | -15479.25 | -3662.5 | 7661.75 | 22756.5 | 45292 |  |  |
| allDayStress_TOTAL_uncategorizedDuration | Int64 | 99.852 | 0.148 | 232 | false | 0 | 2023-05-26 | 2026-05-18 | [1560, 3540, 11340, 3180, 2280] | 60 | 1125 | 2520 | 3990 | 7095 | 46935 | 86400 |  |  |
| avgSleepStress | float64 | 82.127 | 17.873 | 480 | false | 0 | 2023-05-27 | 2026-05-18 | [5.480000019073486, 8.59000015258789, 8.020000457763672, 6.590000152587891, 1... | 3.55 | 7.603 | 11.795 | 15.735 | 19.368 | 26.3 | 70 |  |  |
| stressAsleepDurationSeconds | Int64 | 81.241 | 18.759 | 289 | false | 0 | 2023-05-27 | 2026-05-18 | [28500, 27180, 31800, 25740, 41520] | 780 | 17601 | 26355 | 30120 | 33300 | 38613 | 49260 | Seconds |  |
| stressAwakeDurationSeconds | Int64 | 100 | 0 | 389 | false | 0 | 2023-05-26 | 2026-05-18 | [22080, 56340, 58260, 53940, 60240] | 1080 | 26112 | 49920 | 54960 | 60180 | 85992 | 89820 | Seconds |  |
| stressTotalDurationSeconds | Int64 | 100 | 0 | 193 | false | 0 | 2023-05-26 | 2026-05-18 | [22080, 84840, 85440, 85740, 85980] | 1080 | 32328 | 83760 | 85680 | 86160 | 86400 | 89820 | Seconds |  |

### timestamps

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| calendarDate | datetime64[us] | 100 | 0 | 677 | false |  | 2023-05-26 | 2026-05-18 | ["2023-05-26T00:00:00", "2023-05-27T00:00:00", "2023-05-28T00:00:00", "2023-0... |  |  |  |  |  |  |  |  |  |
