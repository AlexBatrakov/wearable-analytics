# Quality Summary

Generated at (UTC): 2026-02-23T15:02:41.818583+00:00
Input file: /Users/abatrakov/Documents/FUN/wearable-analytics/data/processed/daily_sanitized.parquet
Dataset shape: rows=580, columns=194
Date range: 2023-05-26 to 2026-02-05

## Strict labels

| label | count | pct |
| --- | --- | --- |
| good | 525 | 90.52 |
| partial | 22 | 3.79 |
| bad | 33 | 5.69 |

## Loose labels

| label | count | pct |
| --- | --- | --- |
| good | 542 | 93.45 |
| partial | 5 | 0.86 |
| bad | 33 | 5.69 |

## Thresholds (current config)

- steps_min: 50
- stress_any_min_seconds: 21600 (6.0h)
- stress_full_min_seconds: 72000 (20.0h)
- strict_min_score: 4
- loose_min_score: 3

## Coverage metrics

| flag | fraction_true | pct_true |
| --- | --- | --- |
| has_steps | 0.9293 | 92.93 |
| has_hr | 0.9448 | 94.48 |
| has_stress_duration | 0.9776 | 97.76 |
| has_bodybattery_end | 0.8569 | 85.69 |
| has_sleep | 0.8172 | 81.72 |

## Body Battery coverage diagnostics

| has_bodybattery_start | has_bodybattery_end | count | pct |
| --- | --- | --- | --- |
| 1 | 1 | 497 | 85.69 |
| 1 | 0 | 51 | 8.79 |
| 0 | 0 | 32 | 5.52 |

- start present, end missing (`bodybattery_start_without_end`): 51 days (8.79%)
- Interpretation: start-only Body Battery usually means the watch was worn earlier in the day but powered off before end-of-day, so coverage is partial rather than a parser failure.

## Stress duration summary

- min/median/max hours: 0.30, 23.80, 24.95
- days with stressTotalDurationSeconds < 1h: 2
- days with stressTotalDurationSeconds < 6h: 13
- days with stressTotalDurationSeconds < 12h: 44
- days with stressTotalDurationSeconds < 20h: 77

## Duplicate sanity checks

- stress_duration_matches_allDayStress_TOTAL: true=100.00%, false=0.00%, compared_rows=580
- stress_awake_matches_allDayStress_AWAKE: true=100.00%, false=0.00%, compared_rows=580

## Corrupted stress-only days

- count: 21
- percent: 3.62%
- date range: 2024-02-25 to 2025-12-10

## Suspicion reason frequencies (all rows)

| reason | count | pct_of_rows |
| --- | --- | --- |
| has_sleep | 106 | 18.28 |
| has_bodybattery_end | 83 | 14.31 |
| full_day_stress | 77 | 13.28 |
| has_steps | 41 | 7.07 |
| has_hr | 32 | 5.52 |
| corrupted_stress_only_day | 21 | 3.62 |
| has_stress_duration | 13 | 2.24 |

## Suspicion reason frequencies (strict bad rows)

| reason | count | pct_of_rows |
| --- | --- | --- |
| has_bodybattery_end | 33 | 100 |
| has_sleep | 33 | 100 |
| has_hr | 32 | 96.97 |
| has_steps | 32 | 96.97 |
| corrupted_stress_only_day | 21 | 63.64 |
| full_day_stress | 12 | 36.36 |
| has_stress_duration | 9 | 27.27 |

## Notes

- Strict validity uses quality_score >= 4.
- Loose validity uses quality_score >= 3.
- Quality labels describe day-level analysis readiness / signal coverage, not medical-grade measurement quality.
- `has_bodybattery_end` is intentionally used (instead of any Body Battery presence) because end-of-day value is more useful for day-outcome analyses.
- Missing sleep often indicates no night coverage for that date.
