# Data Dictionary

Generated at (UTC): 2026-02-16T16:13:56.848555+00:00
Dataset shape: rows=580, columns=176
Date range: 2023-05-26 to 2026-02-05

## Missingness summary (top 30)

| column | dtype | missing_pct | inferred_group | notes |
| --- | --- | --- | --- | --- |
| abnormalHeartRateAlertsCount | Int64 | 90.3448275862069 | heart_rate |  |
| allDayStress_ASLEEP_highDuration | Int64 | 81.72413793103448 | stress |  |
| bodyBatteryStat_SLEEPEND | Int64 | 71.20689655172414 | body_battery |  |
| bodyBatteryStat_SLEEPEND_statTimestamp | str | 71.20689655172414 | body_battery |  |
| bodyBatteryStat_SLEEPEND_bodyBatteryStatus | str | 71.20689655172414 | body_battery |  |
| bodyBatteryStat_SLEEPSTART | Int64 | 70.17241379310344 | body_battery |  |
| bodyBatteryStat_SLEEPSTART_bodyBatteryStatus | str | 70.17241379310344 | body_battery |  |
| bodyBatteryStat_SLEEPSTART_statTimestamp | str | 70.17241379310344 | body_battery |  |
| respiration_algorithmVersion | Int64 | 63.793103448275865 | respiration |  |
| restingCaloriesFromActivity | Int64 | 56.37931034482758 | calories |  |
| hydration_capped | boolean | 56.20689655172414 | hydration |  |
| hydration_goalInML | Float64 | 56.20689655172414 | hydration |  |
| hydration_adjustedGoalInML | Float64 | 56.20689655172414 | hydration |  |
| hydration_lastEntryTimestampLocal | str | 56.20689655172414 | hydration |  |
| hydration_activityIntakeInML | Int64 | 56.20689655172414 | hydration |  |
| hydration_sweatLossInML | Int64 | 56.20689655172414 | hydration |  |
| hydration_valueInML | Int64 | 56.20689655172414 | hydration |  |
| allDayStress_ASLEEP_stressTooActiveCount | Int64 | 52.758620689655174 | stress |  |
| allDayStress_ASLEEP_activityDuration | Int64 | 52.758620689655174 | stress |  |
| bodyBatteryStat_DURINGSLEEP_statTimestamp | str | 52.758620689655174 | body_battery |  |
| bodyBatteryStat_DURINGSLEEP_bodyBatteryStatus | str | 52.758620689655174 | body_battery |  |
| bodyBatteryStat_DURINGSLEEP | Int64 | 52.758620689655174 | body_battery |  |
| allDayStress_ASLEEP_mediumDuration | Int64 | 38.275862068965516 | stress |  |
| isVigorousDay | boolean | 34.310344827586206 | other |  |
| remainingKilocalories | Int64 | 32.758620689655174 | calories |  |
| allDayStress_ASLEEP_stressOffWristCount | Int64 | 30.17241379310345 | stress |  |
| allDayStress_ASLEEP_uncategorizedDuration | Int64 | 30.17241379310345 | stress |  |
| spo2SleepAverageHR | float64 | 22.758620689655174 | spo2 |  |
| spo2SleepLowestSPO2 | Int64 | 22.413793103448278 | spo2 |  |
| spo2SleepAverageSPO2 | float64 | 22.413793103448278 | spo2 |  |

## Columns by group

### body_battery

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bodyBatteryEndOfDay | Int64 | 14.310344827586208 | 48 | [36, 22, 19, 35, 24] | 5.0 | 15.0 | 72.0 |  |  |
| bodyBatteryHighest | Int64 | 5.517241379310345 | 83 | [70, 100, 93, 80, 82] | 5.0 | 83.0 | 100.0 |  |  |
| bodyBatteryLowest | Int64 | 5.517241379310345 | 37 | [36, 22, 8, 18, 24] | 5.0 | 8.0 | 80.0 |  |  |
| bodyBatteryStartOfDay | Int64 | 5.517241379310345 | 64 | [66, 36, 22, 19, 35] | 5.0 | 17.0 | 87.0 |  |  |
| bodyBatteryStat_DURINGSLEEP | Int64 | 52.758620689655174 | 66 | [60, 70, 37, 59, 71] | 2.0 | 71.0 | 95.0 |  |  |
| bodyBatteryStat_DURINGSLEEP_bodyBatteryStatus | str | 52.758620689655174 | 1 | ["MEASURED"] | nan | nan | nan |  |  |
| bodyBatteryStat_DURINGSLEEP_statTimestamp | str | 52.758620689655174 | 274 | ["2023-12-18T09:12:00.0", "2023-12-19T07:44:00.0", "2023-12-20T07:20:00.0", "... | nan | nan | nan |  |  |
| bodyBatteryStat_ENDOFDAY | Int64 | 14.310344827586208 | 48 | [36, 22, 19, 35, 24] | 5.0 | 15.0 | 72.0 |  |  |
| bodyBatteryStat_ENDOFDAY_bodyBatteryStatus | str | 14.310344827586208 | 2 | ["MEASURED", "MODELED"] | nan | nan | nan |  |  |
| bodyBatteryStat_ENDOFDAY_statTimestamp | str | 14.310344827586208 | 497 | ["2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "2023-05-28T22:00:00.0", "... | nan | nan | nan |  |  |
| bodyBatteryStat_HIGHEST | Int64 | 5.517241379310345 | 83 | [70, 100, 93, 80, 82] | 5.0 | 83.0 | 100.0 |  |  |
| bodyBatteryStat_HIGHEST_bodyBatteryStatus | str | 5.517241379310345 | 3 | ["MEASURED", "RESET", "MODELED"] | nan | nan | nan |  |  |
| bodyBatteryStat_HIGHEST_statTimestamp | str | 5.517241379310345 | 548 | ["2023-05-26T16:20:00.0", "2023-05-27T06:38:00.0", "2023-05-28T08:55:00.0", "... | nan | nan | nan |  |  |
| bodyBatteryStat_LOWEST | Int64 | 5.517241379310345 | 37 | [36, 22, 8, 18, 24] | 5.0 | 8.0 | 80.0 |  |  |
| bodyBatteryStat_LOWEST_bodyBatteryStatus | str | 5.517241379310345 | 3 | ["MEASURED", "MODELED", "RESET"] | nan | nan | nan |  |  |
| bodyBatteryStat_LOWEST_statTimestamp | str | 5.517241379310345 | 548 | ["2023-05-26T21:55:00.0", "2023-05-27T21:57:00.0", "2023-05-28T00:50:00.0", "... | nan | nan | nan |  |  |
| bodyBatteryStat_MOSTRECENT | Int64 | 5.517241379310345 | 59 | [36, 22, 19, 35, 24] | 5.0 | 16.0 | 100.0 |  |  |
| bodyBatteryStat_MOSTRECENT_bodyBatteryStatus | str | 5.517241379310345 | 3 | ["MEASURED", "MODELED", "RESET"] | nan | nan | nan |  |  |
| bodyBatteryStat_MOSTRECENT_statTimestamp | str | 5.517241379310345 | 548 | ["2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "2023-05-28T22:00:00.0", "... | nan | nan | nan |  |  |
| bodyBatteryStat_SLEEPEND | Int64 | 71.20689655172414 | 52 | [77, 83, 89, 56, 75] | 16.0 | 89.0 | 100.0 |  |  |
| bodyBatteryStat_SLEEPEND_bodyBatteryStatus | str | 71.20689655172414 | 1 | ["MEASURED"] | nan | nan | nan |  |  |
| bodyBatteryStat_SLEEPEND_statTimestamp | str | 71.20689655172414 | 167 | ["2024-11-17T11:34:00.0", "2024-11-18T07:51:00.0", "2024-11-19T07:46:00.0", "... | nan | nan | nan |  |  |
| bodyBatteryStat_SLEEPSTART | Int64 | 70.17241379310344 | 28 | [20, 5, 25, 22, 10] | 5.0 | 9.0 | 44.0 |  |  |
| bodyBatteryStat_SLEEPSTART_bodyBatteryStatus | str | 70.17241379310344 | 1 | ["MEASURED"] | nan | nan | nan |  |  |
| bodyBatteryStat_SLEEPSTART_statTimestamp | str | 70.17241379310344 | 173 | ["2024-06-20T23:16:00.0", "2024-08-08T21:12:00.0", "2024-08-09T23:39:00.0", "... | nan | nan | nan |  |  |
| bodyBatteryStat_STARTOFDAY | Int64 | 5.517241379310345 | 64 | [66, 36, 22, 19, 35] | 5.0 | 17.0 | 87.0 |  |  |
| bodyBatteryStat_STARTOFDAY_bodyBatteryStatus | str | 5.517241379310345 | 3 | ["RESET", "MEASURED", "MODELED"] | nan | nan | nan |  |  |
| bodyBatteryStat_STARTOFDAY_statTimestamp | str | 5.517241379310345 | 548 | ["2023-05-26T15:43:00.0", "2023-05-26T22:01:00.0", "2023-05-27T22:01:00.0", "... | nan | nan | nan |  |  |
| bodyBattery_bodyBatteryVersion | Int64 | 5.344827586206897 | 1 | [2] | 2.0 | 2.0 | 2.0 |  |  |
| bodyBattery_chargedValue | Int64 | 5.689655172413794 | 84 | [4, 65, 85, 84, 66] | 0.0 | 70.0 | 99.0 | percent |  |
| bodyBattery_drainedValue | Int64 | 5.689655172413794 | 90 | [34, 79, 88, 68, 77] | 0.0 | 68.0 | 98.0 | percent |  |

### calories

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activeKilocalories | Int64 | 0.0 | 396 | [199, 792, 698, 593, 351] | 0.0 | 282.0 | 2544.0 | Kilocalories |  |
| bmrKilocalories | Int64 | 0.0 | 97 | [1959, 1964, 1962, 1966, 1955] | 401.0 | 1964.0 | 2045.0 | Kilocalories |  |
| remainingKilocalories | Int64 | 32.758620689655174 | 316 | [2158, 2756, 2660, 2559, 2306] | 408.0 | 2241.0 | 4461.0 | Kilocalories |  |
| restingCaloriesFromActivity | Int64 | 56.37931034482758 | 101 | [0, 164, 50, 207, 157] | 0.0 | 38.0 | 653.0 | Kilocalories |  |
| totalKilocalories | Int64 | 0.0 | 430 | [2158, 2756, 2660, 2559, 2306] | 408.0 | 2250.0 | 4461.0 | Kilocalories |  |
| wellnessActiveKilocalories | Int64 | 0.0 | 396 | [199, 792, 698, 593, 351] | 0.0 | 282.0 | 2544.0 | Kilocalories |  |
| wellnessKilocalories | Int64 | 0.0 | 430 | [2158, 2756, 2660, 2559, 2306] | 408.0 | 2250.0 | 4461.0 | Kilocalories |  |
| wellnessTotalKilocalories | Int64 | 0.0 | 430 | [2158, 2756, 2660, 2559, 2306] | 408.0 | 2250.0 | 4461.0 | Kilocalories |  |

### flags_includes

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| includesActivityData | boolean | 0.0 | 2 | [true, false] | 0.0 | 0.0 | 1.0 |  |  |
| includesAllDayPulseOx | boolean | 0.0 | 2 | [false, true] | 0.0 | 1.0 | 1.0 |  |  |
| includesCalorieConsumedData | boolean | 0.0 | 1 | [false] | 0.0 | 0.0 | 0.0 |  |  |
| includesContinuousMeasurement | boolean | 0.0 | 1 | [false] | 0.0 | 0.0 | 0.0 |  |  |
| includesSingleMeasurement | boolean | 0.0 | 2 | [true, false] | 0.0 | 0.0 | 1.0 |  |  |
| includesSleepPulseOx | boolean | 0.0 | 2 | [false, true] | 0.0 | 1.0 | 1.0 |  |  |
| includesWellnessData | boolean | 0.0 | 1 | [true] | 1.0 | 1.0 | 1.0 |  |  |

### heart_rate

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abnormalHeartRateAlertsCount | Int64 | 90.3448275862069 | 10 | [3, 8, 1, 4, 6] | 1.0 | 2.0 | 18.0 | bpm |  |
| currentDayRestingHeartRate | Int64 | 6.379310344827586 | 23 | [63, 44, 43, 40, 42] | 36.0 | 45.0 | 86.0 | bpm |  |
| maxAvgHeartRate | Int64 | 5.517241379310345 | 95 | [126, 160, 175, 119, 120] | 69.0 | 128.0 | 183.0 | bpm |  |
| maxHeartRate | Int64 | 5.517241379310345 | 90 | [126, 160, 175, 119, 120] | 74.0 | 133.0 | 183.0 | bpm |  |
| minAvgHeartRate | Int64 | 5.517241379310345 | 39 | [55, 41, 40, 42, 39] | 31.0 | 43.0 | 77.0 | bpm |  |
| minHeartRate | Int64 | 5.517241379310345 | 37 | [55, 41, 40, 39, 38] | 31.0 | 42.0 | 76.0 | bpm |  |
| restingHeartRate | Int64 | 6.379310344827586 | 24 | [63, 54, 50, 48, 47] | 39.0 | 45.0 | 86.0 | bpm |  |
| restingHeartRateTimestamp | Int64 | 6.379310344827586 | 543 | [1685138400000, 1685224800000, 1685311200000, 1685397600000, 1685484000000] | 1685138400000.0 | 1713132000000.0 | 1770283500000.0 | ms | epoch millis |

### hydration

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hydration_activityIntakeInML | Int64 | 56.20689655172414 | 1 | [0] | 0.0 | 0.0 | 0.0 | mL |  |
| hydration_adjustedGoalInML | Float64 | 56.20689655172414 | 183 | [2847.056, 3691.0, 3101.0, 3863.0, 3674.0] | 2840.0 | 3003.0 | 5808.0 | mL |  |
| hydration_capped | boolean | 56.20689655172414 | 1 | [false] | 0.0 | 0.0 | 0.0 |  |  |
| hydration_goalInML | Float64 | 56.20689655172414 | 2 | [2839.056, 2840.0] | 2839.056 | 2840.0 | 2840.0 | mL |  |
| hydration_lastEntryTimestampLocal | str | 56.20689655172414 | 254 | ["2023-05-26T17:50:43.0", "2023-05-27T17:07:24.0", "2023-05-28T18:34:30.0", "... | nan | nan | nan |  |  |
| hydration_sweatLossInML | Int64 | 56.20689655172414 | 183 | [8, 851, 261, 1023, 834] | 0.0 | 163.0 | 2968.0 | mL |  |
| hydration_valueInML | Int64 | 56.20689655172414 | 1 | [0] | 0.0 | 0.0 | 0.0 | mL |  |

### other

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| activeSeconds | Int64 | 0.0 | 529 | [1285, 6453, 1321, 5498, 3372] | 0.0 | 2676.0 | 30402.0 | Seconds |  |
| averageRespiration | float64 | 20.517241379310345 | 101 | [16.0, 15.0, 17.0, 18.0, 14.0] | 13.0 | 16.0 | 19.0 | brpm |  |
| awakeCount | Int64 | 18.275862068965516 | 7 | [0, 2, 1, 4, 3] | 0.0 | 1.0 | 7.0 |  |  |
| awakeSleepSeconds | Int64 | 18.275862068965516 | 83 | [240, 1200, 720, 3960, 1680] | 0.0 | 660.0 | 9660.0 | Seconds |  |
| dailyStepGoal | Int64 | 0.0 | 324 | [7500, 8000, 8540, 7810, 7190] | 3120.0 | 7690.0 | 13470.0 |  |  |
| deepSleepSeconds | Int64 | 18.275862068965516 | 109 | [5220, 6120, 6420, 4320, 7200] | 840.0 | 5940.0 | 10140.0 | Seconds |  |
| durationInMilliseconds | Int64 | 0.0 | 43 | [86400000, 80580000, 73860000, 63420000, 35520000] | 18240000.0 | 86400000.0 | 90000000.0 | Milliseconds |  |
| highestRespiration | float64 | 20.517241379310345 | 11 | [22.0, 20.0, 24.0, 23.0, 21.0] | 17.0 | 22.0 | 27.0 | brpm |  |
| highlyActiveSeconds | Int64 | 0.0 | 422 | [797, 5638, 2700, 3993, 1751] | 0.0 | 350.5 | 6664.0 | Seconds |  |
| isVigorousDay | boolean | 34.310344827586206 | 2 | [false, true] | 0.0 | 0.0 | 1.0 |  |  |
| lightSleepSeconds | Int64 | 18.275862068965516 | 242 | [16260, 14700, 19860, 14460, 21000] | 3660.0 | 16350.0 | 29400.0 | Seconds |  |
| lowestRespiration | float64 | 20.517241379310345 | 8 | [12.0, 9.0, 11.0, 10.0, 13.0] | 7.0 | 10.0 | 14.0 | brpm |  |
| moderateIntensityMinutes | Int64 | 0.0 | 93 | [0, 113, 38, 135, 29] | 0.0 | 19.0 | 220.0 |  |  |
| remSleepSeconds | Int64 | 19.482758620689655 | 179 | [6720, 4620, 4740, 6180, 9300] | 120.0 | 6960.0 | 17400.0 | Seconds |  |
| restlessMomentCount | Int64 | 18.275862068965516 | 74 | [40, 36, 65, 67, 45] | 11.0 | 43.0 | 109.0 |  |  |
| retro | boolean | 18.275862068965516 | 1 | [false] | 0.0 | 0.0 | 0.0 |  |  |
| unmeasurableSeconds | Int64 | 18.275862068965516 | 25 | [0, 480, 900, 780, 540] | 0.0 | 0.0 | 4200.0 | Seconds |  |
| userFloorsAscendedGoal | Int64 | 0.0 | 1 | [10] | 10.0 | 10.0 | 10.0 |  |  |
| userIntensityMinutesGoal | Int64 | 0.0 | 3 | [150, 300, 400] | 150.0 | 400.0 | 400.0 |  |  |
| vigorousIntensityMinutes | Int64 | 0.0 | 33 | [5, 8, 27, 0, 21] | 0.0 | 0.0 | 89.0 |  |  |
| wellnessEndTimeGmt | str | 0.0 | 580 | ["2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "2023-05-28T22:00:00.0", "... | nan | nan | nan |  |  |
| wellnessEndTimeLocal | str | 0.0 | 580 | ["2023-05-27T00:00:00.0", "2023-05-28T00:00:00.0", "2023-05-29T00:00:00.0", "... | nan | nan | nan |  |  |
| wellnessStartTimeGmt | str | 0.0 | 580 | ["2023-05-25T22:00:00.0", "2023-05-26T22:00:00.0", "2023-05-27T22:00:00.0", "... | nan | nan | nan |  |  |
| wellnessStartTimeLocal | str | 0.0 | 580 | ["2023-05-26T00:00:00.0", "2023-05-27T00:00:00.0", "2023-05-28T00:00:00.0", "... | nan | nan | nan |  |  |

### respiration

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| respiration_algorithmVersion | Int64 | 63.793103448275865 | 1 | [100] | 100.0 | 100.0 | 100.0 | brpm |  |
| respiration_avgWakingRespirationValue | Int64 | 5.689655172413794 | 8 | [13, 14, 15, 17, 16] | 11.0 | 14.0 | 18.0 | brpm |  |
| respiration_highestRespirationValue | Int64 | 5.689655172413794 | 14 | [15, 22, 20, 24, 23] | 12.0 | 22.0 | 27.0 | brpm |  |
| respiration_latestRespirationTimeGMT | str | 5.689655172413794 | 547 | ["2023-05-26T21:59:00.0", "2023-05-27T22:00:00.0", "2023-05-28T20:14:00.0", "... | nan | nan | nan | brpm |  |
| respiration_latestRespirationValue | Int64 | 5.689655172413794 | 14 | [14, 13, 15, 12, 16] | 9.0 | 14.0 | 22.0 | brpm |  |
| respiration_lowestRespirationValue | Int64 | 5.689655172413794 | 8 | [8, 11, 10, 9, 12] | 7.0 | 9.0 | 16.0 | brpm |  |

### sleep

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sleepAwakeTimeScore | Int64 | 18.448275862068968 | 71 | [100, 80, 91, 34, 70] | 0.0 | 92.0 | 100.0 |  |  |
| sleepAwakeningsCountScore | Int64 | 18.448275862068968 | 6 | [100, 74, 87, 32, 61] | 0.0 | 87.0 | 100.0 |  |  |
| sleepCombinedAwakeScore | Int64 | 18.448275862068968 | 70 | [100, 77, 89, 33, 78] | 0.0 | 91.0 | 100.0 |  |  |
| sleepDeepScore | Int64 | 18.79310344827586 | 40 | [93, 100, 87, 96, 79] | 30.0 | 100.0 | 100.0 |  |  |
| sleepDurationScore | Int64 | 18.448275862068968 | 68 | [100, 79, 77, 53, 61] | 0.0 | 100.0 | 100.0 |  |  |
| sleepEndTimestampGMT | Int64 | 18.275862068965516 | 474 | [1685176920, 1685264159, 1685352240, 1685433900, 1685530018] | 1685176920.0 | 1710972810.0 | 1770275340.0 |  | epoch seconds timestamp |
| sleepFeedback | str | 18.275862068965516 | 31 | ["POSITIVE_HIGHLY_RECOVERING", "POSITIVE_RECOVERING", "NEGATIVE_LONG_BUT_DISC... | nan | nan | nan |  |  |
| sleepInsight | str | 18.275862068965516 | 10 | ["NONE", "POSITIVE_LATE_BED_TIME", "POSITIVE_RESTFUL_DAY", "NEGATIVE_LATE_BED... | nan | nan | nan |  |  |
| sleepInterruptionsScore | Int64 | 18.448275862068968 | 68 | [95, 78, 83, 86, 40] | 12.0 | 89.0 | 100.0 |  |  |
| sleepLightScore | Int64 | 18.79310344827586 | 41 | [92, 91, 80, 94, 77] | 35.0 | 94.0 | 100.0 |  |  |
| sleepOverallScore | Int64 | 18.448275862068968 | 63 | [98, 82, 90, 85, 69] | 26.0 | 84.0 | 100.0 |  |  |
| sleepQualityScore | Int64 | 18.448275862068968 | 54 | [97, 88, 89, 93, 75] | 29.0 | 85.0 | 100.0 |  |  |
| sleepRecoveryScore | Int64 | 18.448275862068968 | 48 | [100, 87, 99, 79, 84] | 0.0 | 79.0 | 100.0 |  |  |
| sleepRemScore | Int64 | 18.79310344827586 | 62 | [99, 74, 69, 100, 73] | 0.0 | 82.0 | 100.0 |  |  |
| sleepRestfulnessScore | Int64 | 18.448275862068968 | 61 | [79, 84, 64, 78, 73] | 0.0 | 82.0 | 100.0 |  |  |
| sleepStartTimestampGMT | Int64 | 18.275862068965516 | 474 | [1685148480, 1685236980, 1685320500, 1685408220, 1685488500] | 1685148480.0 | 1710940050.0 | 1770244440.0 |  | epoch seconds timestamp |
| sleepWindowConfirmationType | str | 18.275862068965516 | 1 | ["ENHANCED_CONFIRMED_FINAL"] | nan | nan | nan |  |  |

### spo2

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| averageSpo2Value | Int64 | 16.034482758620687 | 9 | [93, 92, 96, 95, 94] | 89.0 | 94.0 | 98.0 | percent |  |
| latestSpo2Value | Int64 | 15.689655172413794 | 20 | [97, 99, 95, 89, 84] | 78.0 | 95.0 | 100.0 | percent |  |
| latestSpo2ValueReadingTimeGmt | str | 15.689655172413794 | 489 | ["2023-05-26T17:33:00.0", "2023-05-27T17:50:00.0", "2023-05-28T05:59:00.0", "... | nan | nan | nan | percent |  |
| latestSpo2ValueReadingTimeLocal | str | 15.689655172413794 | 489 | ["2023-05-26T19:33:00.0", "2023-05-27T19:50:00.0", "2023-05-28T07:59:00.0", "... | nan | nan | nan | percent |  |
| lowestSpo2Value | Int64 | 15.689655172413794 | 23 | [95, 93, 83, 82, 84] | 71.0 | 84.0 | 95.0 | percent |  |
| spo2SleepAverageHR | float64 | 22.758620689655174 | 28 | [50.0, 48.0, 45.0, 46.0, 47.0] | 40.0 | 51.0 | 78.0 | percent |  |
| spo2SleepAverageSPO2 | float64 | 22.413793103448278 | 112 | [94.0, 92.0, 91.0, 93.0, 96.0] | 89.0 | 94.19 | 99.0 | percent |  |
| spo2SleepLowestSPO2 | Int64 | 22.413793103448278 | 21 | [83, 82, 84, 87, 86] | 74.0 | 84.0 | 94.0 | percent |  |
| spo2SleepMeasurementEndTimestampGMT | Int64 | 22.413793103448278 | 450 | [1685253540, 1685339940, 1685426400, 1685512800, 1685599140] | 1685253540.0 | 1713117570.0 | 1770274740.0 | percent | epoch seconds timestamp |
| spo2SleepMeasurementStartTimestampGMT | Int64 | 22.413793103448278 | 450 | [1685237040, 1685320560, 1685408280, 1685488560, 1685577240] | 1685237040.0 | 1713091140.0 | 1770246060.0 | percent | epoch seconds timestamp |

### steps_distance

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| floorsAscendedInMeters | Float64 | 0.0 | 393 | [0.0, 72.336, 10.617, 73.152, 25.298] | 0.0 | 25.137 | 1099.285 | Meters |  |
| floorsDescendedInMeters | Float64 | 0.0 | 451 | [0.0, 63.324, 11.024, 89.929, 17.887] | 0.0 | 23.237499999999997 | 1117.692 | Meters |  |
| totalDistanceMeters | Int64 | 5.862068965517241 | 535 | [863, 17337, 5044, 14366, 7196] | 7.0 | 4709.5 | 35155.0 | Meters |  |
| totalSteps | Int64 | 5.862068965517241 | 534 | [1096, 20915, 5935, 17593, 9212] | 9.0 | 6062.0 | 46718.0 |  |  |
| wellnessDistanceMeters | Int64 | 5.862068965517241 | 535 | [863, 17337, 5044, 14366, 7196] | 7.0 | 4709.5 | 35155.0 | Meters |  |

### stress

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| allDayStress_ASLEEP_activityDuration | Int64 | 52.758620689655174 | 13 | [300, 180, 60, 240, 360] | 60.0 | 120.0 | 3960.0 |  |  |
| allDayStress_ASLEEP_averageStressLevel | Int64 | 0.0 | 38 | [-2, 6, 9, 8, 5] | -2.0 | 12.0 | 57.0 |  |  |
| allDayStress_ASLEEP_averageStressLevelIntensity | Int64 | 0.0 | 29 | [-2, 6, 9, 8, 11] | -2.0 | 12.0 | 57.0 |  |  |
| allDayStress_ASLEEP_highDuration | Int64 | 81.72413793103448 | 17 | [60, 120, 240, 180, 600] | 60.0 | 120.0 | 4560.0 |  |  |
| allDayStress_ASLEEP_lowDuration | Int64 | 21.379310344827587 | 134 | [240, 1080, 1380, 300, 1800] | 60.0 | 1800.0 | 14580.0 |  |  |
| allDayStress_ASLEEP_maxStressLevel | Int64 | 20.17241379310345 | 73 | [51, 89, 54, 30, 45] | 16.0 | 66.0 | 97.0 |  |  |
| allDayStress_ASLEEP_mediumDuration | Int64 | 38.275862068965516 | 50 | [60, 240, 660, 540, 360] | 60.0 | 300.0 | 15360.0 |  |  |
| allDayStress_ASLEEP_restDuration | Int64 | 20.17241379310345 | 285 | [27960, 24600, 29880, 25320, 38640] | 480.0 | 25920.0 | 40140.0 |  |  |
| allDayStress_ASLEEP_stressDuration | Int64 | 21.20689655172414 | 150 | [300, 1380, 1440, 1800, 360] | 60.0 | 2040.0 | 28140.0 |  |  |
| allDayStress_ASLEEP_stressIntensityCount | Int64 | 20.17241379310345 | 275 | [471, 433, 522, 427, 674] | 19.0 | 486.0 | 767.0 |  |  |
| allDayStress_ASLEEP_stressOffWristCount | Int64 | 30.17241379310345 | 69 | [4, 15, 5, 2, 17] | 1.0 | 11.0 | 98.0 |  |  |
| allDayStress_ASLEEP_stressTooActiveCount | Int64 | 52.758620689655174 | 13 | [5, 3, 1, 4, 6] | 1.0 | 2.0 | 66.0 |  |  |
| allDayStress_ASLEEP_totalDuration | Int64 | 20.17241379310345 | 273 | [28500, 27180, 31800, 25740, 41520] | 1140.0 | 30180.0 | 49260.0 |  |  |
| allDayStress_ASLEEP_totalStressCount | Int64 | 20.17241379310345 | 273 | [475, 453, 530, 429, 692] | 19.0 | 503.0 | 821.0 |  |  |
| allDayStress_ASLEEP_totalStressIntensity | Int64 | 20.17241379310345 | 463 | [36558, 27751, 36026, 33586, 38653] | -17133.0 | 22400.0 | 52940.0 |  |  |
| allDayStress_ASLEEP_uncategorizedDuration | Int64 | 30.17241379310345 | 69 | [240, 900, 300, 120, 1020] | 60.0 | 660.0 | 5880.0 |  |  |
| allDayStress_AWAKE_activityDuration | Int64 | 5.689655172413794 | 263 | [5580, 17100, 9840, 14760, 12120] | 60.0 | 9000.0 | 64320.0 |  |  |
| allDayStress_AWAKE_averageStressLevel | Int64 | 0.0 | 71 | [50, 41, 58, 36, 38] | -1.0 | 53.0 | 91.0 |  |  |
| allDayStress_AWAKE_averageStressLevelIntensity | Int64 | 0.0 | 71 | [43, 33, 55, 30, 31] | -1.0 | 52.0 | 91.0 |  |  |
| allDayStress_AWAKE_highDuration | Int64 | 6.724137931034482 | 277 | [3120, 3660, 14340, 1200, 4860] | 60.0 | 9000.0 | 47580.0 |  |  |
| allDayStress_AWAKE_lowDuration | Int64 | 6.379310344827586 | 281 | [3660, 9420, 9660, 12420, 14340] | 60.0 | 10860.0 | 28980.0 |  |  |
| allDayStress_AWAKE_maxStressLevel | Int64 | 5.689655172413794 | 22 | [96, 97, 99, 90, 98] | 30.0 | 99.0 | 100.0 |  |  |
| allDayStress_AWAKE_mediumDuration | Int64 | 5.862068965517241 | 259 | [4740, 9420, 6780, 7680, 7860] | 60.0 | 10740.0 | 31500.0 |  |  |
| allDayStress_AWAKE_restDuration | Int64 | 8.275862068965518 | 258 | [3420, 13440, 7200, 15000, 18900] | 60.0 | 5370.0 | 46980.0 |  |  |
| allDayStress_AWAKE_stressDuration | Int64 | 5.689655172413794 | 361 | [11520, 22500, 30780, 21300, 27060] | 120.0 | 32700.0 | 72780.0 |  |  |
| allDayStress_AWAKE_stressIntensityCount | Int64 | 5.689655172413794 | 378 | [249, 599, 633, 605, 766] | 2.0 | 673.0 | 1399.0 |  |  |
| allDayStress_AWAKE_stressOffWristCount | Int64 | 0.1724137931034483 | 208 | [26, 55, 174, 48, 36] | 1.0 | 49.0 | 1440.0 |  |  |
| allDayStress_AWAKE_stressTooActiveCount | Int64 | 5.689655172413794 | 263 | [93, 285, 164, 246, 202] | 1.0 | 150.0 | 1072.0 |  |  |
| allDayStress_AWAKE_totalDuration | Int64 | 0.0 | 362 | [22080, 56340, 58260, 53940, 60240] | 1080.0 | 54900.0 | 89820.0 |  |  |
| allDayStress_AWAKE_totalStressCount | Int64 | 0.0 | 362 | [368, 939, 971, 899, 1004] | 18.0 | 915.0 | 1497.0 |  |  |
| allDayStress_AWAKE_totalStressIntensity | Int64 | 5.689655172413794 | 547 | [-6142, -6824, -26075, -4452, -6960] | -76210.0 | -22751.0 | 45292.0 |  |  |
| allDayStress_AWAKE_uncategorizedDuration | Int64 | 0.1724137931034483 | 208 | [1560, 3300, 10440, 2880, 2160] | 60.0 | 2940.0 | 86400.0 |  |  |
| allDayStress_TOTAL_activityDuration | Int64 | 5.689655172413794 | 268 | [5580, 17100, 10140, 14940, 12120] | 60.0 | 9120.0 | 64320.0 |  |  |
| allDayStress_TOTAL_averageStressLevel | Int64 | 0.0 | 67 | [50, 25, 38, 23, 26] | -1.0 | 37.0 | 91.0 |  |  |
| allDayStress_TOTAL_averageStressLevelIntensity | Int64 | 0.0 | 63 | [43, 18, 25, 20, 22] | -1.0 | 25.0 | 91.0 |  |  |
| allDayStress_TOTAL_highDuration | Int64 | 6.724137931034482 | 274 | [3120, 3660, 14400, 1200, 4860] | 60.0 | 9060.0 | 47580.0 |  |  |
| allDayStress_TOTAL_lowDuration | Int64 | 6.379310344827586 | 296 | [3660, 9660, 10740, 13800, 14640] | 60.0 | 13200.0 | 34740.0 |  |  |
| allDayStress_TOTAL_maxStressLevel | Int64 | 5.689655172413794 | 22 | [96, 97, 99, 90, 98] | 30.0 | 99.0 | 100.0 |  |  |
| allDayStress_TOTAL_mediumDuration | Int64 | 5.862068965517241 | 256 | [4740, 9480, 7020, 7740, 7860] | 60.0 | 11100.0 | 31620.0 |  |  |
| allDayStress_TOTAL_restDuration | Int64 | 7.931034482758621 | 349 | [3420, 41400, 31800, 44880, 44220] | 60.0 | 31260.0 | 59160.0 |  |  |
| allDayStress_TOTAL_stressDuration | Int64 | 5.689655172413794 | 369 | [11520, 22800, 32160, 22740, 27360] | 120.0 | 35760.0 | 72780.0 |  |  |
| allDayStress_TOTAL_stressIntensityCount | Int64 | 5.689655172413794 | 359 | [249, 1070, 1066, 1127, 1193] | 2.0 | 1149.0 | 1399.0 |  |  |
| allDayStress_TOTAL_stressOffWristCount | Int64 | 0.1724137931034483 | 212 | [26, 59, 189, 53, 38] | 1.0 | 67.0 | 1440.0 |  |  |
| allDayStress_TOTAL_stressTooActiveCount | Int64 | 5.689655172413794 | 268 | [93, 285, 169, 249, 202] | 1.0 | 152.0 | 1072.0 |  |  |
| allDayStress_TOTAL_totalDuration | Int64 | 0.0 | 166 | [22080, 84840, 85440, 85740, 85980] | 1080.0 | 85680.0 | 89820.0 |  |  |
| allDayStress_TOTAL_totalStressCount | Int64 | 0.0 | 166 | [368, 1414, 1424, 1429, 1433] | 18.0 | 1428.0 | 1497.0 |  |  |
| allDayStress_TOTAL_totalStressIntensity | Int64 | 5.689655172413794 | 546 | [-6142, 29734, 1676, 31574, 26626] | -76210.0 | -2686.0 | 45292.0 |  |  |
| allDayStress_TOTAL_uncategorizedDuration | Int64 | 0.1724137931034483 | 212 | [1560, 3540, 11340, 3180, 2280] | 60.0 | 4020.0 | 86400.0 |  |  |
| avgSleepStress | float64 | 18.275862068965516 | 415 | [5.480000019073486, 8.59000015258789, 8.020000457763672, 6.590000152587891, 1... | 3.549999952316284 | 15.449999809265137 | 63.060001373291016 |  |  |
| stressAsleepDurationSeconds | Int64 | 20.17241379310345 | 273 | [28500, 27180, 31800, 25740, 41520] | 1140.0 | 30180.0 | 49260.0 | Seconds |  |
| stressAwakeDurationSeconds | Int64 | 0.0 | 362 | [22080, 56340, 58260, 53940, 60240] | 1080.0 | 54900.0 | 89820.0 | Seconds |  |
| stressTotalDurationSeconds | Int64 | 0.0 | 166 | [22080, 84840, 85440, 85740, 85980] | 1080.0 | 85680.0 | 89820.0 | Seconds |  |

### timestamps

| column | dtype | missing_pct | n_unique | example_values | min | median | max | inferred_unit | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| calendarDate | datetime64[us] | 0.0 | 580 | ["2023-05-26T00:00:00", "2023-05-27T00:00:00", "2023-05-28T00:00:00", "2023-0... | nan | nan | nan |  |  |
