# Data Dictionary

Generated at (UTC): 2026-02-27T13:54:45.361392+00:00
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

## Missingness summary (top 30)

| column | dtype | non_null_pct | missing_pct | is_constant | first_non_null_date | last_non_null_date | inferred_group | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abnormalHeartRateAlertsCount | Int64 | 9.655 | 90.345 | false | 2023-05-28 | 2023-11-04 | heart_rate |  |
| allDayStress_ASLEEP_highDuration | Int64 | 18.276 | 81.724 | false | 2023-05-28 | 2026-01-29 | stress |  |
| bodyBatteryStat_SLEEPEND | Int64 | 28.793 | 71.207 | false | 2024-11-17 | 2026-02-05 | body_battery |  |
| bodyBatteryStat_SLEEPEND_bodyBatteryStatus | str | 28.793 | 71.207 | true | 2024-11-17 | 2026-02-05 | body_battery |  |
| bodyBatteryStat_SLEEPEND_statTimestamp | str | 28.793 | 71.207 | false | 2024-11-17 | 2026-02-05 | body_battery | ISO datetime string |
| bodyBatteryStat_SLEEPSTART | Int64 | 29.828 | 70.172 | false | 2024-06-21 | 2026-02-05 | body_battery |  |
| bodyBatteryStat_SLEEPSTART_bodyBatteryStatus | str | 29.828 | 70.172 | true | 2024-06-21 | 2026-02-05 | body_battery |  |
| bodyBatteryStat_SLEEPSTART_statTimestamp | str | 29.828 | 70.172 | false | 2024-06-21 | 2026-02-05 | body_battery | ISO datetime string |
| respiration_algorithmVersion | Int64 | 36.207 | 63.793 | true | 2024-08-14 | 2026-02-05 | respiration |  |
| restingCaloriesFromActivity | Int64 | 43.621 | 56.379 | false | 2023-05-26 | 2026-01-31 | calories |  |
| hydration_sweatLossInML | Int64 | 43.793 | 56.207 | false | 2023-05-26 | 2026-01-31 | hydration |  |
| hydration_valueInML | Int64 | 43.793 | 56.207 | true | 2023-05-26 | 2026-01-31 | hydration |  |
| hydration_lastEntryTimestampLocal | str | 43.793 | 56.207 | false | 2023-05-26 | 2026-01-31 | hydration | ISO datetime string |
| hydration_goalInML | Float64 | 43.793 | 56.207 | false | 2023-05-26 | 2026-01-31 | hydration |  |
| hydration_capped | boolean | 43.793 | 56.207 | true | 2023-05-26 | 2026-01-31 | hydration |  |
| hydration_adjustedGoalInML | Float64 | 43.793 | 56.207 | false | 2023-05-26 | 2026-01-31 | hydration |  |
| hydration_activityIntakeInML | Int64 | 43.793 | 56.207 | true | 2023-05-26 | 2026-01-31 | hydration |  |
| allDayStress_ASLEEP_activityDuration | Int64 | 47.241 | 52.759 | false | 2023-05-28 | 2026-02-05 | stress |  |
| bodyBatteryStat_DURINGSLEEP_statTimestamp | str | 47.241 | 52.759 | false | 2023-12-18 | 2026-02-05 | body_battery | ISO datetime string |
| bodyBatteryStat_DURINGSLEEP_bodyBatteryStatus | str | 47.241 | 52.759 | true | 2023-12-18 | 2026-02-05 | body_battery |  |
| bodyBatteryStat_DURINGSLEEP | Int64 | 47.241 | 52.759 | false | 2023-12-18 | 2026-02-05 | body_battery |  |
| allDayStress_ASLEEP_stressTooActiveCount | Int64 | 47.241 | 52.759 | false | 2023-05-28 | 2026-02-05 | stress |  |
| allDayStress_ASLEEP_mediumDuration | Int64 | 61.724 | 38.276 | false | 2023-05-27 | 2026-02-05 | stress |  |
| isVigorousDay | boolean | 65.69 | 34.31 | false | 2023-12-13 | 2026-02-05 | other |  |
| remainingKilocalories | Int64 | 67.241 | 32.759 | false | 2023-05-26 | 2025-01-13 | calories |  |
| allDayStress_ASLEEP_stressOffWristCount | Int64 | 69.828 | 30.172 | false | 2023-05-27 | 2026-02-03 | stress |  |
| allDayStress_ASLEEP_uncategorizedDuration | Int64 | 69.828 | 30.172 | false | 2023-05-27 | 2026-02-03 | stress |  |
| spo2SleepAverageHR | float64 | 77.241 | 22.759 | false | 2023-05-28 | 2026-02-03 | sleep |  |
| spo2SleepMeasurementStartTimestampGMT | Int64 | 77.586 | 22.414 | false | 2023-05-28 | 2026-02-05 | sleep | epoch seconds timestamp |
| spo2SleepLowestSPO2 | Int64 | 77.586 | 22.414 | false | 2023-05-28 | 2026-02-05 | sleep |  |

## Columns by group

### body_battery

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bodyBatteryEndOfDay | Int64 | 85.69 | 14.31 | 48 | false | 0 | 2023-05-26 | 2026-02-04 | [36, 22, 19, 35, 24] | 5 | 5 | 7 | 15 | 23 | 37 | 72 |  |  |
| bodyBatteryHighest | Int64 | 94.483 | 5.517 | 83 | false | 0 | 2023-05-26 | 2026-02-05 | [70, 100, 93, 80, 82] | 5 | 34 | 68 | 83 | 96 | 100 | 100 |  |  |
| bodyBatteryLowest | Int64 | 94.483 | 5.517 | 37 | false | 0 | 2023-05-26 | 2026-02-05 | [36, 22, 8, 18, 24] | 5 | 5 | 5 | 8 | 16 | 25 | 80 |  |  |
| bodyBatteryStartOfDay | Int64 | 94.483 | 5.517 | 64 | false | 0 | 2023-05-26 | 2026-02-05 | [66, 36, 22, 19, 35] | 5 | 5 | 8 | 17 | 26 | 52 | 87 |  |  |
| bodyBatteryStat_DURINGSLEEP | Int64 | 47.241 | 52.759 | 66 | false | 0 | 2023-12-18 | 2026-02-05 | [60, 70, 37, 59, 71] | 2 | 36.65 | 62 | 71 | 80 | 90.35 | 95 |  |  |
| bodyBatteryStat_DURINGSLEEP_bodyBatteryStatus | str | 47.241 | 52.759 | 1 | true |  | 2023-12-18 | 2026-02-05 | ["MEASURED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_DURINGSLEEP_statTimestamp | str | 47.241 | 52.759 | 274 | false |  | 2023-12-18 | 2026-02-05 | ["2023-12-18T09:12:00.0", "2023-12-19T07:44:00.0", "2023-12-20T07:20:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_ENDOFDAY | Int64 | 85.69 | 14.31 | 48 | false | 0 | 2023-05-26 | 2026-02-04 | [36, 22, 19, 35, 24] | 5 | 5 | 7 | 15 | 23 | 37 | 72 |  |  |
| bodyBatteryStat_ENDOFDAY_bodyBatteryStatus | str | 85.69 | 14.31 | 2 | false |  | 2023-05-26 | 2026-02-04 | ["MEASURED", "MODELED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_ENDOFDAY_statTimestamp | str | 85.69 | 14.31 | 497 | false |  | 2023-05-26 | 2026-02-04 | ["2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "2023-05-28T22:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_HIGHEST | Int64 | 94.483 | 5.517 | 83 | false | 0 | 2023-05-26 | 2026-02-05 | [70, 100, 93, 80, 82] | 5 | 34 | 68 | 83 | 96 | 100 | 100 |  |  |
| bodyBatteryStat_HIGHEST_bodyBatteryStatus | str | 94.483 | 5.517 | 3 | false |  | 2023-05-26 | 2026-02-05 | ["MEASURED", "RESET", "MODELED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_HIGHEST_statTimestamp | str | 94.483 | 5.517 | 548 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-26T16:20:00.0", "2023-05-27T06:38:00.0", "2023-05-28T08:55:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_LOWEST | Int64 | 94.483 | 5.517 | 37 | false | 0 | 2023-05-26 | 2026-02-05 | [36, 22, 8, 18, 24] | 5 | 5 | 5 | 8 | 16 | 25 | 80 |  |  |
| bodyBatteryStat_LOWEST_bodyBatteryStatus | str | 94.483 | 5.517 | 3 | false |  | 2023-05-26 | 2026-02-05 | ["MEASURED", "MODELED", "RESET"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_LOWEST_statTimestamp | str | 94.483 | 5.517 | 548 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-26T21:55:00.0", "2023-05-27T21:57:00.0", "2023-05-28T00:50:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_MOSTRECENT | Int64 | 94.483 | 5.517 | 59 | false | 0 | 2023-05-26 | 2026-02-05 | [36, 22, 19, 35, 24] | 5 | 5 | 7.75 | 16 | 25 | 45 | 100 |  |  |
| bodyBatteryStat_MOSTRECENT_bodyBatteryStatus | str | 94.483 | 5.517 | 3 | false |  | 2023-05-26 | 2026-02-05 | ["MEASURED", "MODELED", "RESET"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_MOSTRECENT_statTimestamp | str | 94.483 | 5.517 | 548 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "2023-05-28T22:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_SLEEPEND | Int64 | 28.793 | 71.207 | 52 | false | 0 | 2024-11-17 | 2026-02-05 | [77, 83, 89, 56, 75] | 16 | 46.3 | 75 | 89 | 100 | 100 | 100 |  |  |
| bodyBatteryStat_SLEEPEND_bodyBatteryStatus | str | 28.793 | 71.207 | 1 | true |  | 2024-11-17 | 2026-02-05 | ["MEASURED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_SLEEPEND_statTimestamp | str | 28.793 | 71.207 | 167 | false |  | 2024-11-17 | 2026-02-05 | ["2024-11-17T11:34:00.0", "2024-11-18T07:51:00.0", "2024-11-19T07:46:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_SLEEPSTART | Int64 | 29.828 | 70.172 | 28 | false | 0 | 2024-06-21 | 2026-02-05 | [20, 5, 25, 22, 10] | 5 | 5 | 5 | 9 | 18 | 27.4 | 44 |  |  |
| bodyBatteryStat_SLEEPSTART_bodyBatteryStatus | str | 29.828 | 70.172 | 1 | true |  | 2024-06-21 | 2026-02-05 | ["MEASURED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_SLEEPSTART_statTimestamp | str | 29.828 | 70.172 | 173 | false |  | 2024-06-21 | 2026-02-05 | ["2024-06-20T23:16:00.0", "2024-08-08T21:12:00.0", "2024-08-09T23:39:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBatteryStat_STARTOFDAY | Int64 | 94.483 | 5.517 | 64 | false | 0 | 2023-05-26 | 2026-02-05 | [66, 36, 22, 19, 35] | 5 | 5 | 8 | 17 | 26 | 52 | 87 |  |  |
| bodyBatteryStat_STARTOFDAY_bodyBatteryStatus | str | 94.483 | 5.517 | 3 | false |  | 2023-05-26 | 2026-02-05 | ["RESET", "MEASURED", "MODELED"] |  |  |  |  |  |  |  |  |  |
| bodyBatteryStat_STARTOFDAY_statTimestamp | str | 94.483 | 5.517 | 548 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-26T15:43:00.0", "2023-05-26T22:01:00.0", "2023-05-27T22:01:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| bodyBattery_bodyBatteryVersion | Int64 | 94.655 | 5.345 | 1 | true | 0 | 2023-05-26 | 2026-02-05 | [2] | 2 | 2 | 2 | 2 | 2 | 2 | 2 |  |  |
| bodyBattery_chargedValue | Int64 | 94.31 | 5.69 | 84 | false | 7.313 | 2023-05-26 | 2026-02-05 | [4, 65, 85, 84, 66] | 0 | 0 | 53 | 70 | 79 | 90.7 | 99 | percent |  |
| bodyBattery_drainedValue | Int64 | 94.31 | 5.69 | 90 | false | 1.097 | 2023-05-26 | 2026-02-05 | [34, 79, 88, 68, 77] | 0 | 14.3 | 51 | 68 | 79 | 89 | 98 | percent |  |

### calories

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activeKilocalories | Int64 | 100 | 0 | 396 | false | 7.759 | 2023-05-26 | 2026-02-05 | [199, 792, 698, 593, 351] | 0 | 0 | 112.5 | 282 | 522 | 850.8 | 2544 | Kilocalories |  |
| bmrKilocalories | Int64 | 100 | 0 | 97 | false | 0 | 2023-05-26 | 2026-02-05 | [1959, 1964, 1962, 1966, 1955] | 401 | 1702.85 | 1940.5 | 1964 | 2023 | 2023 | 2045 | Kilocalories |  |
| remainingKilocalories | Int64 | 67.241 | 32.759 | 316 | false | 0 | 2023-05-26 | 2025-01-13 | [2158, 2756, 2660, 2559, 2306] | 408 | 1901 | 2064.5 | 2241 | 2487.5 | 2889.5 | 4461 | Kilocalories |  |
| restingCaloriesFromActivity | Int64 | 43.621 | 56.379 | 101 | false | 0.395 | 2023-05-26 | 2026-01-31 | [0, 164, 50, 207, 157] | 0 | 16.6 | 24 | 38 | 64 | 145 | 653 | Kilocalories |  |
| totalKilocalories | Int64 | 100 | 0 | 430 | false | 0 | 2023-05-26 | 2026-02-05 | [2158, 2756, 2660, 2559, 2306] | 408 | 1901 | 2068.5 | 2250 | 2495.25 | 2863.45 | 4461 | Kilocalories |  |
| wellnessActiveKilocalories | Int64 | 100 | 0 | 396 | false | 7.759 | 2023-05-26 | 2026-02-05 | [199, 792, 698, 593, 351] | 0 | 0 | 112.5 | 282 | 522 | 850.8 | 2544 | Kilocalories |  |
| wellnessKilocalories | Int64 | 100 | 0 | 430 | false | 0 | 2023-05-26 | 2026-02-05 | [2158, 2756, 2660, 2559, 2306] | 408 | 1901 | 2068.5 | 2250 | 2495.25 | 2863.45 | 4461 | Kilocalories |  |
| wellnessTotalKilocalories | Int64 | 100 | 0 | 430 | false | 0 | 2023-05-26 | 2026-02-05 | [2158, 2756, 2660, 2559, 2306] | 408 | 1901 | 2068.5 | 2250 | 2495.25 | 2863.45 | 4461 | Kilocalories |  |

### flags_includes

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| includesActivityData | boolean | 100 | 0 | 2 | false |  | 2023-05-26 | 2026-02-05 | [true, false] |  |  |  |  |  |  |  |  |  |
| includesAllDayPulseOx | boolean | 100 | 0 | 2 | false |  | 2023-05-26 | 2026-02-05 | [false, true] |  |  |  |  |  |  |  |  |  |
| includesCalorieConsumedData | boolean | 100 | 0 | 1 | true |  | 2023-05-26 | 2026-02-05 | [false] |  |  |  |  |  |  |  |  |  |
| includesContinuousMeasurement | boolean | 100 | 0 | 1 | true |  | 2023-05-26 | 2026-02-05 | [false] |  |  |  |  |  |  |  |  |  |
| includesSingleMeasurement | boolean | 100 | 0 | 2 | false |  | 2023-05-26 | 2026-02-05 | [true, false] |  |  |  |  |  |  |  |  |  |
| includesSleepPulseOx | boolean | 100 | 0 | 2 | false |  | 2023-05-26 | 2026-02-05 | [false, true] |  |  |  |  |  |  |  |  |  |
| includesWellnessData | boolean | 100 | 0 | 1 | true |  | 2023-05-26 | 2026-02-05 | [true] |  |  |  |  |  |  |  |  |  |

### heart_rate

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abnormalHeartRateAlertsCount | Int64 | 9.655 | 90.345 | 10 | false | 0 | 2023-05-28 | 2023-11-04 | [3, 8, 1, 4, 6] | 1 | 1 | 1 | 2 | 3.25 | 7.25 | 18 | bpm |  |
| currentDayRestingHeartRate | Int64 | 93.621 | 6.379 | 23 | false | 0 | 2023-05-26 | 2026-02-05 | [63, 44, 43, 40, 42] | 36 | 39 | 43 | 45 | 47 | 51 | 86 | bpm |  |
| maxAvgHeartRate | Int64 | 94.483 | 5.517 | 95 | false | 0 | 2023-05-26 | 2026-02-05 | [126, 160, 175, 119, 120] | 69 | 96 | 116 | 128 | 144.25 | 162 | 183 | bpm |  |
| maxHeartRate | Int64 | 94.483 | 5.517 | 90 | false | 0 | 2023-05-26 | 2026-02-05 | [126, 160, 175, 119, 120] | 74 | 99 | 120 | 133 | 148 | 165 | 183 | bpm |  |
| minAvgHeartRate | Int64 | 94.483 | 5.517 | 39 | false | 0 | 2023-05-26 | 2026-02-05 | [55, 41, 40, 42, 39] | 31 | 38 | 41 | 43 | 45 | 54.65 | 77 | bpm |  |
| minHeartRate | Int64 | 94.483 | 5.517 | 37 | false | 0 | 2023-05-26 | 2026-02-05 | [55, 41, 40, 39, 38] | 31 | 38 | 40 | 42 | 45 | 53 | 76 | bpm |  |
| restingHeartRate | Int64 | 93.621 | 6.379 | 24 | false | 0 | 2023-05-26 | 2026-02-05 | [63, 54, 50, 48, 47] | 39 | 41 | 43 | 45 | 47 | 49 | 86 | bpm |  |
| restingHeartRateTimestamp | Int64 | 93.621 | 6.379 | 543 | false | 0 | 2023-05-26 | 2026-02-05 | [1685138400000, 1685224800000, 1685311200000, 1685397600000, 1685484000000] | 1685138400000 | 1687479840000 | 1697018400000 | 1713132000000 | 1755079200000 | 1767990960000 | 1770283500000 | ms | epoch millis |

### hydration

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hydration_activityIntakeInML | Int64 | 43.793 | 56.207 | 1 | true | 100 | 2023-05-26 | 2026-01-31 | [0] | 0 | 0 | 0 | 0 | 0 | 0 | 0 | mL |  |
| hydration_adjustedGoalInML | Float64 | 43.793 | 56.207 | 183 | false | 0 | 2023-05-26 | 2026-01-31 | [2847.056, 3691.0, 3101.0, 3863.0, 3674.0] | 2840 | 2901 | 2949.25 | 3003 | 3115.25 | 3543.75 | 5808 | mL |  |
| hydration_capped | boolean | 43.793 | 56.207 | 1 | true |  | 2023-05-26 | 2026-01-31 | [false] |  |  |  |  |  |  |  |  |  |
| hydration_goalInML | Float64 | 43.793 | 56.207 | 2 | false | 0 | 2023-05-26 | 2026-01-31 | [2839.056, 2840.0] | 2839.06 | 2840 | 2840 | 2840 | 2840 | 2840 | 2840 | mL |  |
| hydration_lastEntryTimestampLocal | str | 43.793 | 56.207 | 254 | false |  | 2023-05-26 | 2026-01-31 | ["2023-05-26T17:50:43.0", "2023-05-27T17:07:24.0", "2023-05-28T18:34:30.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| hydration_sweatLossInML | Int64 | 43.793 | 56.207 | 183 | false | 0.787 | 2023-05-26 | 2026-01-31 | [8, 851, 261, 1023, 834] | 0 | 61 | 109.25 | 163 | 275.25 | 703.75 | 2968 | mL |  |
| hydration_valueInML | Int64 | 43.793 | 56.207 | 1 | true | 100 | 2023-05-26 | 2026-01-31 | [0] | 0 | 0 | 0 | 0 | 0 | 0 | 0 | mL |  |

### other

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activeSeconds | Int64 | 100 | 0 | 529 | false | 6.379 | 2023-05-26 | 2026-02-05 | [1285, 6453, 1321, 5498, 3372] | 0 | 0 | 1083.25 | 2676 | 4866 | 9953.45 | 30402 | Seconds |  |
| awakeCount | Int64 | 81.724 | 18.276 | 7 | false | 44.726 | 2023-05-27 | 2026-02-05 | [0, 2, 1, 4, 3] | 0 | 0 | 0 | 1 | 1.75 | 3 | 7 |  |  |
| dailyStepGoal | Int64 | 100 | 0 | 324 | false | 0 | 2023-05-26 | 2026-02-05 | [7500, 8000, 8540, 7810, 7190] | 3120 | 4919.5 | 6200 | 7690 | 8717.5 | 10973.5 | 13470 |  |  |
| durationInMilliseconds | Int64 | 100 | 0 | 43 | false | 0 | 2023-05-26 | 2026-02-05 | [86400000, 80580000, 73860000, 63420000, 35520000] | 18240000 | 73806000 | 86400000 | 86400000 | 86400000 | 86400000 | 90000000 | Milliseconds |  |
| highlyActiveSeconds | Int64 | 100 | 0 | 422 | false | 6.897 | 2023-05-26 | 2026-02-05 | [797, 5638, 2700, 3993, 1751] | 0 | 0 | 89.75 | 350.5 | 1264.5 | 3311.7 | 6664 | Seconds |  |
| isVigorousDay | boolean | 65.69 | 34.31 | 2 | false |  | 2023-12-13 | 2026-02-05 | [false, true] |  |  |  |  |  |  |  |  |  |
| moderateIntensityMinutes | Int64 | 100 | 0 | 93 | false | 23.621 | 2023-05-26 | 2026-02-05 | [0, 113, 38, 135, 29] | 0 | 0 | 1 | 19 | 39 | 75.1 | 220 |  |  |
| restlessMomentCount | Int64 | 81.724 | 18.276 | 74 | false | 0 | 2023-05-27 | 2026-02-05 | [40, 36, 65, 67, 45] | 11 | 22 | 34 | 43 | 55 | 72.35 | 109 |  |  |
| retro | boolean | 81.724 | 18.276 | 1 | true |  | 2023-05-27 | 2026-02-05 | [false] |  |  |  |  |  |  |  |  |  |
| unmeasurableSeconds | Int64 | 81.724 | 18.276 | 25 | false | 87.975 | 2023-05-27 | 2026-02-05 | [0, 480, 900, 780, 540] | 0 | 0 | 0 | 0 | 0 | 981 | 4200 | Seconds |  |
| userFloorsAscendedGoal | Int64 | 100 | 0 | 1 | true | 0 | 2023-05-26 | 2026-02-05 | [10] | 10 | 10 | 10 | 10 | 10 | 10 | 10 |  |  |
| userIntensityMinutesGoal | Int64 | 100 | 0 | 3 | false | 0 | 2023-05-26 | 2026-02-05 | [150, 300, 400] | 150 | 300 | 400 | 400 | 400 | 400 | 400 |  |  |
| vigorousIntensityMinutes | Int64 | 100 | 0 | 33 | false | 51.034 | 2023-05-26 | 2026-02-05 | [5, 8, 27, 0, 21] | 0 | 0 | 0 | 0 | 5 | 19.05 | 89 |  |  |
| wellnessEndTimeGmt | str | 100 | 0 | 580 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "2023-05-28T22:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| wellnessEndTimeLocal | str | 100 | 0 | 580 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-27T00:00:00.0", "2023-05-28T00:00:00.0", "2023-05-29T00:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| wellnessStartTimeGmt | str | 100 | 0 | 580 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-25T22:00:00.0", "2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| wellnessStartTimeLocal | str | 100 | 0 | 580 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-26T00:00:00.0", "2023-05-27T00:00:00.0", "2023-05-28T00:00:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |

### respiration

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| averageRespiration | float64 | 79.483 | 20.517 | 101 | false | 0 | 2023-05-27 | 2026-02-05 | [16.0, 15.0, 17.0, 18.0, 14.0] | 13 | 15 | 15 | 16 | 16.57 | 17.52 | 19 | brpm |  |
| highestRespiration | float64 | 79.483 | 20.517 | 11 | false | 0 | 2023-05-27 | 2026-02-05 | [22.0, 20.0, 24.0, 23.0, 21.0] | 17 | 20 | 21 | 22 | 23 | 25 | 27 | brpm |  |
| lowestRespiration | float64 | 79.483 | 20.517 | 8 | false | 0 | 2023-05-27 | 2026-02-05 | [12.0, 9.0, 11.0, 10.0, 13.0] | 7 | 8 | 9 | 10 | 11 | 12 | 14 | brpm |  |
| respiration_algorithmVersion | Int64 | 36.207 | 63.793 | 1 | true | 0 | 2024-08-14 | 2026-02-05 | [100] | 100 | 100 | 100 | 100 | 100 | 100 | 100 |  |  |
| respiration_avgWakingRespirationValue | Int64 | 94.31 | 5.69 | 8 | false | 0 | 2023-05-26 | 2026-02-05 | [13, 14, 15, 17, 16] | 11 | 13 | 13 | 14 | 14 | 15 | 18 | brpm |  |
| respiration_highestRespirationValue | Int64 | 94.31 | 5.69 | 14 | false | 0 | 2023-05-26 | 2026-02-05 | [15, 22, 20, 24, 23] | 12 | 20 | 21 | 22 | 23 | 25 | 27 | brpm |  |
| respiration_latestRespirationTimeGMT | str | 94.31 | 5.69 | 547 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-26T21:59:00.0", "2023-05-27T22:00:00.0", "2023-05-28T20:14:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| respiration_latestRespirationValue | Int64 | 94.31 | 5.69 | 14 | false | 0 | 2023-05-26 | 2026-02-05 | [14, 13, 15, 12, 16] | 9 | 12 | 13 | 14 | 14 | 19 | 22 | brpm |  |
| respiration_lowestRespirationValue | Int64 | 94.31 | 5.69 | 8 | false | 0 | 2023-05-26 | 2026-02-05 | [8, 11, 10, 9, 12] | 7 | 8 | 9 | 9 | 10 | 11 | 16 | brpm |  |

### sleep

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| awakeSleepSeconds | Int64 | 81.724 | 18.276 | 83 | false | 10.97 | 2023-05-27 | 2026-02-05 | [240, 1200, 720, 3960, 1680] | 0 | 0 | 120 | 660 | 1560 | 4020 | 9660 | Seconds |  |
| deepSleepSeconds | Int64 | 81.724 | 18.276 | 109 | false | 0 | 2023-05-27 | 2026-02-05 | [5220, 6120, 6420, 4320, 7200] | 840 | 3420 | 4920 | 5940 | 6885 | 8160 | 10140 | Seconds |  |
| lightSleepSeconds | Int64 | 81.724 | 18.276 | 242 | false | 0 | 2023-05-27 | 2026-02-05 | [16260, 14700, 19860, 14460, 21000] | 3660 | 8778 | 13350 | 16350 | 19305 | 24081 | 29400 | Seconds |  |
| remSleepSeconds | Int64 | 80.517 | 19.483 | 179 | false | 0 | 2023-05-27 | 2026-02-05 | [6720, 4620, 4740, 6180, 9300] | 120 | 2454 | 5010 | 6960 | 8790 | 11682 | 17400 | Seconds |  |
| sleepAwakeTimeScore | Int64 | 81.552 | 18.448 | 71 | false | 1.903 | 2023-05-27 | 2026-02-05 | [100, 80, 91, 34, 70] | 0 | 32.6 | 74 | 92 | 100 | 100 | 100 |  |  |
| sleepAwakeningsCountScore | Int64 | 81.552 | 18.448 | 6 | false | 0.634 | 2023-05-27 | 2026-02-05 | [100, 74, 87, 32, 61] | 0 | 61 | 74 | 87 | 100 | 100 | 100 |  |  |
| sleepCombinedAwakeScore | Int64 | 81.552 | 18.448 | 70 | false | 0.211 | 2023-05-27 | 2026-02-05 | [100, 77, 89, 33, 78] | 0 | 38.6 | 76 | 91 | 100 | 100 | 100 |  |  |
| sleepDeepScore | Int64 | 81.207 | 18.793 | 40 | false | 0 | 2023-05-27 | 2026-02-05 | [93, 100, 87, 96, 79] | 30 | 71.5 | 82 | 100 | 100 | 100 | 100 |  |  |
| sleepDurationScore | Int64 | 81.552 | 18.448 | 68 | false | 0.211 | 2023-05-27 | 2026-02-05 | [100, 79, 77, 53, 61] | 0 | 48.6 | 79 | 100 | 100 | 100 | 100 |  |  |
| sleepEndTimestampGMT | Int64 | 81.724 | 18.276 | 474 | false | 0 | 2023-05-27 | 2026-02-05 | [1685176920, 1685264159, 1685352240, 1685433900, 1685530018] | 1685176920 | 1687213311 | 1696456680 | 1710972810 | 1754704200 | 1768067535 | 1770275340 | s | epoch seconds timestamp |
| sleepFeedback | str | 81.724 | 18.276 | 31 | false |  | 2023-05-27 | 2026-02-05 | ["POSITIVE_HIGHLY_RECOVERING", "POSITIVE_RECOVERING", "NEGATIVE_LONG_BUT_DISC... |  |  |  |  |  |  |  |  |  |
| sleepInsight | str | 81.724 | 18.276 | 10 | false |  | 2023-05-27 | 2026-02-05 | ["NONE", "POSITIVE_LATE_BED_TIME", "POSITIVE_RESTFUL_DAY", "NEGATIVE_LATE_BED... |  |  |  |  |  |  |  |  |  |
| sleepInterruptionsScore | Int64 | 81.552 | 18.448 | 68 | false | 0 | 2023-05-27 | 2026-02-05 | [95, 78, 83, 86, 40] | 12 | 46.6 | 75 | 89 | 96 | 100 | 100 |  |  |
| sleepLightScore | Int64 | 81.207 | 18.793 | 41 | false | 0 | 2023-05-27 | 2026-02-05 | [92, 91, 80, 94, 77] | 35 | 71 | 84 | 94 | 100 | 100 | 100 |  |  |
| sleepOverallScore | Int64 | 81.552 | 18.448 | 63 | false | 0 | 2023-05-27 | 2026-02-05 | [98, 82, 90, 85, 69] | 26 | 49.6 | 76 | 84 | 90 | 97 | 100 |  |  |
| sleepQualityScore | Int64 | 81.552 | 18.448 | 54 | false | 0 | 2023-05-27 | 2026-02-05 | [97, 88, 89, 93, 75] | 29 | 61 | 78 | 85 | 91 | 97 | 100 |  |  |
| sleepRecoveryScore | Int64 | 81.552 | 18.448 | 48 | false | 3.171 | 2023-05-27 | 2026-02-05 | [100, 87, 99, 79, 84] | 0 | 61 | 72 | 79 | 94 | 100 | 100 |  |  |
| sleepRemScore | Int64 | 81.207 | 18.793 | 62 | false | 0.849 | 2023-05-27 | 2026-02-05 | [99, 74, 69, 100, 73] | 0 | 56 | 73 | 82 | 98 | 100 | 100 |  |  |
| sleepRestfulnessScore | Int64 | 81.552 | 18.448 | 61 | false | 0.211 | 2023-05-27 | 2026-02-05 | [79, 84, 64, 78, 73] | 0 | 55.6 | 71 | 82 | 91 | 100 | 100 |  |  |
| sleepStartTimestampGMT | Int64 | 81.724 | 18.276 | 474 | false | 0 | 2023-05-27 | 2026-02-05 | [1685148480, 1685236980, 1685320500, 1685408220, 1685488500] | 1685148480 | 1687186314 | 1696422780 | 1710940050 | 1754669625 | 1768031562 | 1770244440 | s | epoch seconds timestamp |
| sleepWindowConfirmationType | str | 81.724 | 18.276 | 1 | true |  | 2023-05-27 | 2026-02-05 | ["ENHANCED_CONFIRMED_FINAL"] |  |  |  |  |  |  |  |  |  |
| spo2SleepAverageHR | float64 | 77.241 | 22.759 | 28 | false | 0 | 2023-05-28 | 2026-02-03 | [50.0, 48.0, 45.0, 46.0, 47.0] | 40 | 45 | 48 | 51 | 53.25 | 59 | 78 | bpm |  |
| spo2SleepAverageSPO2 | float64 | 77.586 | 22.414 | 112 | false | 0 | 2023-05-28 | 2026-02-05 | [94.0, 92.0, 91.0, 93.0, 96.0] | 89 | 92 | 93.417 | 94.19 | 95 | 96.991 | 99 | percent |  |
| spo2SleepLowestSPO2 | Int64 | 77.586 | 22.414 | 21 | false | 0 | 2023-05-28 | 2026-02-05 | [83, 82, 84, 87, 86] | 74 | 78 | 82 | 84 | 86 | 89 | 94 | percent |  |
| spo2SleepMeasurementEndTimestampGMT | Int64 | 77.586 | 22.414 | 450 | false | 0 | 2023-05-28 | 2026-02-05 | [1685253540, 1685339940, 1685426400, 1685512800, 1685599140] | 1685253540 | 1687198290 | 1697457555 | 1713117570 | 1755280755 | 1768162320 | 1770274740 | s | epoch seconds timestamp |
| spo2SleepMeasurementStartTimestampGMT | Int64 | 77.586 | 22.414 | 450 | false | 0 | 2023-05-28 | 2026-02-05 | [1685237040, 1685320560, 1685408280, 1685488560, 1685577240] | 1685237040 | 1687168542 | 1697435160 | 1713091140 | 1755254790 | 1768136880 | 1770246060 | s | epoch seconds timestamp |

### spo2

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| averageSpo2Value | Int64 | 83.966 | 16.034 | 9 | false | 0 | 2023-05-28 | 2026-02-05 | [93, 92, 96, 95, 94] | 89 | 92 | 93 | 94 | 95 | 96 | 98 | percent |  |
| latestSpo2Value | Int64 | 84.31 | 15.69 | 20 | false | 0 | 2023-05-26 | 2026-02-05 | [97, 99, 95, 89, 84] | 78 | 88 | 92 | 95 | 98 | 100 | 100 | percent |  |
| latestSpo2ValueReadingTimeGmt | str | 84.31 | 15.69 | 489 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-26T17:33:00.0", "2023-05-27T17:50:00.0", "2023-05-28T05:59:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| latestSpo2ValueReadingTimeLocal | str | 84.31 | 15.69 | 489 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-26T19:33:00.0", "2023-05-27T19:50:00.0", "2023-05-28T07:59:00.0", "... |  |  |  |  |  |  |  | datetime | ISO datetime string |
| lowestSpo2Value | Int64 | 84.31 | 15.69 | 23 | false | 0 | 2023-05-26 | 2026-02-05 | [95, 93, 83, 82, 84] | 71 | 78 | 82 | 84 | 86 | 88 | 95 | percent |  |

### steps_distance

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| floorsAscendedInMeters | Float64 | 100 | 0 | 393 | false | 22.069 | 2023-05-26 | 2026-02-05 | [0.0, 72.336, 10.617, 73.152, 25.298] | 0 | 0 | 3.077 | 25.137 | 44.661 | 90.837 | 1099.29 | Meters |  |
| floorsDescendedInMeters | Float64 | 100 | 0 | 451 | false | 22.414 | 2023-05-26 | 2026-02-05 | [0.0, 63.324, 11.024, 89.929, 17.887] | 0 | 0 | 2.554 | 23.237 | 42.786 | 83.749 | 1117.69 | Meters |  |
| totalDistanceMeters | Int64 | 94.138 | 5.862 | 535 | false | 0 | 2023-05-26 | 2026-02-05 | [863, 17337, 5044, 14366, 7196] | 7 | 269.75 | 2155 | 4709.5 | 8235 | 13418.75 | 35155 | Meters |  |
| totalSteps | Int64 | 94.138 | 5.862 | 534 | false | 0 | 2023-05-26 | 2026-02-05 | [1096, 20915, 5935, 17593, 9212] | 9 | 342.75 | 2886 | 6062 | 10369.75 | 17245.25 | 46718 |  |  |
| wellnessDistanceMeters | Int64 | 94.138 | 5.862 | 535 | false | 0 | 2023-05-26 | 2026-02-05 | [863, 17337, 5044, 14366, 7196] | 7 | 269.75 | 2155 | 4709.5 | 8235 | 13418.75 | 35155 | Meters |  |

### stress

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| allDayStress_ASLEEP_activityDuration | Int64 | 47.241 | 52.759 | 13 | false | 0 | 2023-05-28 | 2026-02-05 | [300, 180, 60, 240, 360] | 60 | 60 | 60 | 120 | 180 | 420 | 3960 |  |  |
| allDayStress_ASLEEP_averageStressLevel | Int64 | 79.828 | 20.172 | 37 | false | 0 | 2023-05-27 | 2026-02-05 | [6, 9, 8, 5, 11] | 3 | 6 | 10 | 13 | 17 | 24 | 57 |  |  |
| allDayStress_ASLEEP_averageStressLevelIntensity | Int64 | 79.828 | 20.172 | 28 | false | 0 | 2023-05-27 | 2026-02-05 | [6, 9, 8, 11, 10] | 4 | 7 | 10 | 13 | 17 | 22 | 57 |  |  |
| allDayStress_ASLEEP_highDuration | Int64 | 18.276 | 81.724 | 17 | false | 0 | 2023-05-28 | 2026-01-29 | [60, 120, 240, 180, 600] | 60 | 60 | 60 | 120 | 345 | 705 | 4560 |  |  |
| allDayStress_ASLEEP_lowDuration | Int64 | 78.621 | 21.379 | 134 | false | 0 | 2023-05-27 | 2026-02-05 | [240, 1080, 1380, 300, 1800] | 60 | 180 | 780 | 1800 | 3855 | 8295 | 14580 |  |  |
| allDayStress_ASLEEP_maxStressLevel | Int64 | 79.828 | 20.172 | 73 | false | 0 | 2023-05-27 | 2026-02-05 | [51, 89, 54, 30, 45] | 16 | 35.1 | 53 | 66 | 75 | 88 | 97 |  |  |
| allDayStress_ASLEEP_mediumDuration | Int64 | 61.724 | 38.276 | 50 | false | 0 | 2023-05-27 | 2026-02-05 | [60, 240, 660, 540, 360] | 60 | 60 | 120 | 300 | 720 | 2169 | 15360 |  |  |
| allDayStress_ASLEEP_restDuration | Int64 | 79.828 | 20.172 | 285 | false | 0 | 2023-05-27 | 2026-02-05 | [27960, 24600, 29880, 25320, 38640] | 480 | 12402 | 21750 | 25920 | 30330 | 34968 | 40140 |  |  |
| allDayStress_ASLEEP_stressDuration | Int64 | 78.793 | 21.207 | 150 | false | 0 | 2023-05-27 | 2026-02-05 | [300, 1380, 1440, 1800, 360] | 60 | 240 | 900 | 2040 | 4440 | 10020 | 28140 |  |  |
| allDayStress_ASLEEP_stressIntensityCount | Int64 | 79.828 | 20.172 | 275 | false | 0 | 2023-05-27 | 2026-02-05 | [471, 433, 522, 427, 674] | 19 | 288.4 | 419 | 486 | 548 | 630.9 | 767 |  |  |
| allDayStress_ASLEEP_stressOffWristCount | Int64 | 69.828 | 30.172 | 69 | false | 0 | 2023-05-27 | 2026-02-03 | [4, 15, 5, 2, 17] | 1 | 1 | 4 | 11 | 25 | 57.8 | 98 |  |  |
| allDayStress_ASLEEP_stressTooActiveCount | Int64 | 47.241 | 52.759 | 13 | false | 0 | 2023-05-28 | 2026-02-05 | [5, 3, 1, 4, 6] | 1 | 1 | 1 | 2 | 3 | 7 | 66 |  |  |
| allDayStress_ASLEEP_totalDuration | Int64 | 79.828 | 20.172 | 273 | false | 0 | 2023-05-27 | 2026-02-05 | [28500, 27180, 31800, 25740, 41520] | 1140 | 18018 | 26250 | 30180 | 34020 | 38868 | 49260 |  |  |
| allDayStress_ASLEEP_totalStressCount | Int64 | 79.828 | 20.172 | 273 | false | 0 | 2023-05-27 | 2026-02-05 | [475, 453, 530, 429, 692] | 19 | 300.3 | 437.5 | 503 | 567 | 647.8 | 821 |  |  |
| allDayStress_ASLEEP_totalStressIntensity | Int64 | 79.828 | 20.172 | 463 | false | 0 | 2023-05-27 | 2026-02-05 | [36558, 27751, 36026, 33586, 38653] | -17133 | 4939.7 | 15982 | 22400 | 30278 | 40038.8 | 52940 |  |  |
| allDayStress_ASLEEP_uncategorizedDuration | Int64 | 69.828 | 30.172 | 69 | false | 0 | 2023-05-27 | 2026-02-03 | [240, 900, 300, 120, 1020] | 60 | 60 | 240 | 660 | 1500 | 3468 | 5880 |  |  |
| allDayStress_AWAKE_activityDuration | Int64 | 94.31 | 5.69 | 263 | false | 0 | 2023-05-26 | 2026-02-05 | [5580, 17100, 9840, 14760, 12120] | 60 | 1656 | 5940 | 9000 | 12420 | 18522 | 64320 |  |  |
| allDayStress_AWAKE_averageStressLevel | Int64 | 94.31 | 5.69 | 70 | false | 0 | 2023-05-26 | 2026-02-05 | [50, 41, 58, 36, 38] | 8 | 34 | 46 | 54 | 63 | 76 | 91 |  |  |
| allDayStress_AWAKE_averageStressLevelIntensity | Int64 | 94.31 | 5.69 | 70 | false | 0 | 2023-05-26 | 2026-02-05 | [43, 33, 55, 30, 31] | 9 | 25 | 43 | 52 | 62 | 76 | 91 |  |  |
| allDayStress_AWAKE_highDuration | Int64 | 93.276 | 6.724 | 277 | false | 0 | 2023-05-26 | 2026-02-05 | [3120, 3660, 14340, 1200, 4860] | 60 | 1380 | 5340 | 9000 | 13980 | 23400 | 47580 |  |  |
| allDayStress_AWAKE_lowDuration | Int64 | 93.621 | 6.379 | 281 | false | 0 | 2023-05-26 | 2026-02-05 | [3660, 9420, 9660, 12420, 14340] | 60 | 1746 | 6780 | 10860 | 14370 | 20394 | 28980 |  |  |
| allDayStress_AWAKE_maxStressLevel | Int64 | 94.31 | 5.69 | 22 | false | 0 | 2023-05-26 | 2026-02-05 | [96, 97, 99, 90, 98] | 30 | 90 | 96.5 | 99 | 99 | 99 | 100 |  |  |
| allDayStress_AWAKE_mediumDuration | Int64 | 94.138 | 5.862 | 259 | false | 0 | 2023-05-26 | 2026-02-05 | [4740, 9420, 6780, 7680, 7860] | 60 | 2160 | 7740 | 10740 | 13980 | 19245 | 31500 |  |  |
| allDayStress_AWAKE_restDuration | Int64 | 91.724 | 8.276 | 258 | false | 0 | 2023-05-26 | 2026-02-04 | [3420, 13440, 7200, 15000, 18900] | 60 | 420 | 2145 | 5370 | 10770 | 25983 | 46980 |  |  |
| allDayStress_AWAKE_stressDuration | Int64 | 94.31 | 5.69 | 361 | false | 0 | 2023-05-26 | 2026-02-05 | [11520, 22500, 30780, 21300, 27060] | 120 | 10974 | 26700 | 32700 | 38070 | 47442 | 72780 |  |  |
| allDayStress_AWAKE_stressIntensityCount | Int64 | 94.31 | 5.69 | 378 | false | 0 | 2023-05-26 | 2026-02-05 | [249, 599, 633, 605, 766] | 2 | 282.6 | 570.5 | 673 | 762 | 947.1 | 1399 |  |  |
| allDayStress_AWAKE_stressOffWristCount | Int64 | 99.828 | 0.172 | 208 | false | 0 | 2023-05-26 | 2026-02-05 | [26, 55, 174, 48, 36] | 1 | 12 | 30 | 49 | 99.5 | 858.1 | 1440 |  |  |
| allDayStress_AWAKE_stressTooActiveCount | Int64 | 94.31 | 5.69 | 263 | false | 0 | 2023-05-26 | 2026-02-05 | [93, 285, 164, 246, 202] | 1 | 27.6 | 99 | 150 | 207 | 308.7 | 1072 |  |  |
| allDayStress_AWAKE_totalDuration | Int64 | 100 | 0 | 362 | false | 0 | 2023-05-26 | 2026-02-05 | [22080, 56340, 58260, 53940, 60240] | 1080 | 30069 | 49680 | 54900 | 60915 | 86163 | 89820 |  |  |
| allDayStress_AWAKE_totalStressCount | Int64 | 100 | 0 | 362 | false | 0 | 2023-05-26 | 2026-02-05 | [368, 939, 971, 899, 1004] | 18 | 501.15 | 828 | 915 | 1015.25 | 1436.05 | 1497 |  |  |
| allDayStress_AWAKE_totalStressIntensity | Int64 | 94.31 | 5.69 | 547 | false | 0 | 2023-05-26 | 2026-02-05 | [-6142, -6824, -26075, -4452, -6960] | -76210 | -44095.8 | -31874 | -22751 | -14017.5 | 15 | 45292 |  |  |
| allDayStress_AWAKE_uncategorizedDuration | Int64 | 99.828 | 0.172 | 208 | false | 0 | 2023-05-26 | 2026-02-05 | [1560, 3300, 10440, 2880, 2160] | 60 | 720 | 1800 | 2940 | 5970 | 51486 | 86400 |  |  |
| allDayStress_TOTAL_activityDuration | Int64 | 94.31 | 5.69 | 268 | false | 0 | 2023-05-26 | 2026-02-05 | [5580, 17100, 10140, 14940, 12120] | 60 | 1860 | 5940 | 9120 | 12480 | 18708 | 64320 |  |  |
| allDayStress_TOTAL_averageStressLevel | Int64 | 94.31 | 5.69 | 66 | false | 0 | 2023-05-26 | 2026-02-05 | [50, 25, 38, 23, 26] | 8 | 25 | 33 | 38 | 44 | 60 | 91 |  |  |
| allDayStress_TOTAL_averageStressLevelIntensity | Int64 | 94.31 | 5.69 | 62 | false | 0 | 2023-05-26 | 2026-02-05 | [43, 18, 25, 20, 22] | 9 | 20 | 23 | 27 | 35.5 | 59 | 91 |  |  |
| allDayStress_TOTAL_highDuration | Int64 | 93.276 | 6.724 | 274 | false | 0 | 2023-05-26 | 2026-02-05 | [3120, 3660, 14400, 1200, 4860] | 60 | 1380 | 5520 | 9060 | 13980 | 23520 | 47580 |  |  |
| allDayStress_TOTAL_lowDuration | Int64 | 93.621 | 6.379 | 296 | false | 0 | 2023-05-26 | 2026-02-05 | [3660, 9660, 10740, 13800, 14640] | 60 | 2538 | 8700 | 13200 | 17370 | 24234 | 34740 |  |  |
| allDayStress_TOTAL_maxStressLevel | Int64 | 94.31 | 5.69 | 22 | false | 0 | 2023-05-26 | 2026-02-05 | [96, 97, 99, 90, 98] | 30 | 90 | 96.5 | 99 | 99 | 99 | 100 |  |  |
| allDayStress_TOTAL_mediumDuration | Int64 | 94.138 | 5.862 | 256 | false | 0 | 2023-05-26 | 2026-02-05 | [4740, 9480, 7020, 7740, 7860] | 60 | 2250 | 7935 | 11100 | 14505 | 20295 | 31620 |  |  |
| allDayStress_TOTAL_restDuration | Int64 | 92.069 | 7.931 | 349 | false | 0 | 2023-05-26 | 2026-02-05 | [3420, 41400, 31800, 44880, 44220] | 60 | 4755 | 25500 | 31260 | 36600 | 44142 | 59160 |  |  |
| allDayStress_TOTAL_stressDuration | Int64 | 94.31 | 5.69 | 369 | false | 0 | 2023-05-26 | 2026-02-05 | [11520, 22800, 32160, 22740, 27360] | 120 | 12012 | 28470 | 35760 | 41220 | 52602 | 72780 |  |  |
| allDayStress_TOTAL_stressIntensityCount | Int64 | 94.31 | 5.69 | 359 | false | 0 | 2023-05-26 | 2026-02-05 | [249, 1070, 1066, 1127, 1193] | 2 | 405.3 | 1026.5 | 1149 | 1227 | 1325.7 | 1399 |  |  |
| allDayStress_TOTAL_stressOffWristCount | Int64 | 99.828 | 0.172 | 212 | false | 0 | 2023-05-26 | 2026-02-05 | [26, 59, 189, 53, 38] | 1 | 19 | 44 | 67 | 118 | 858.1 | 1440 |  |  |
| allDayStress_TOTAL_stressTooActiveCount | Int64 | 94.31 | 5.69 | 268 | false | 0 | 2023-05-26 | 2026-02-05 | [93, 285, 169, 249, 202] | 1 | 31 | 99 | 152 | 208 | 311.8 | 1072 |  |  |
| allDayStress_TOTAL_totalDuration | Int64 | 100 | 0 | 166 | false | 0 | 2023-05-26 | 2026-02-05 | [22080, 84840, 85440, 85740, 85980] | 1080 | 32472 | 84000 | 85680 | 86160 | 86400 | 89820 |  |  |
| allDayStress_TOTAL_totalStressCount | Int64 | 100 | 0 | 166 | false | 0 | 2023-05-26 | 2026-02-05 | [368, 1414, 1424, 1429, 1433] | 18 | 541.2 | 1400 | 1428 | 1436 | 1440 | 1497 |  |  |
| allDayStress_TOTAL_totalStressIntensity | Int64 | 94.31 | 5.69 | 546 | false | 0 | 2023-05-26 | 2026-02-05 | [-6142, 29734, 1676, 31574, 26626] | -76210 | -33192.7 | -13922 | -2686 | 8617 | 23332.3 | 45292 |  |  |
| allDayStress_TOTAL_uncategorizedDuration | Int64 | 99.828 | 0.172 | 212 | false | 0 | 2023-05-26 | 2026-02-05 | [1560, 3540, 11340, 3180, 2280] | 60 | 1140 | 2640 | 4020 | 7080 | 51486 | 86400 |  |  |
| avgSleepStress | float64 | 81.724 | 18.276 | 415 | false | 0 | 2023-05-27 | 2026-02-05 | [5.480000019073486, 8.59000015258789, 8.020000457763672, 6.590000152587891, 1... | 3.55 | 7.573 | 11.625 | 15.45 | 19.098 | 24.549 | 63.06 |  |  |
| stressAsleepDurationSeconds | Int64 | 79.828 | 20.172 | 273 | false | 0 | 2023-05-27 | 2026-02-05 | [28500, 27180, 31800, 25740, 41520] | 1140 | 18018 | 26250 | 30180 | 34020 | 38868 | 49260 | Seconds |  |
| stressAwakeDurationSeconds | Int64 | 100 | 0 | 362 | false | 0 | 2023-05-26 | 2026-02-05 | [22080, 56340, 58260, 53940, 60240] | 1080 | 30069 | 49680 | 54900 | 60915 | 86163 | 89820 | Seconds |  |
| stressTotalDurationSeconds | Int64 | 100 | 0 | 166 | false | 0 | 2023-05-26 | 2026-02-05 | [22080, 84840, 85440, 85740, 85980] | 1080 | 32472 | 84000 | 85680 | 86160 | 86400 | 89820 | Seconds |  |

### timestamps

| column | dtype | non_null_pct | missing_pct | n_unique | is_constant | zero_pct | first_non_null_date | last_non_null_date | example_values | min | p05 | p25 | median | p75 | p95 | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| calendarDate | datetime64[us] | 100 | 0 | 580 | false |  | 2023-05-26 | 2026-02-05 | ["2023-05-26T00:00:00", "2023-05-27T00:00:00", "2023-05-28T00:00:00", "2023-0... |  |  |  |  |  |  |  |  |  |
