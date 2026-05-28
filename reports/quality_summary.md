# Quality Summary

Generated at (UTC): 2026-05-28T08:38:59.895277+00:00
Input file: /Users/abatrakov/Documents/FUN/wearable-analytics/data/processed/daily_sanitized.parquet
Dataset shape: rows=677, columns=194
Date range: 2023-05-26 to 2026-05-18

## Strict labels

| label | count | pct |
| --- | --- | --- |
| good | 617 | 91.14 |
| partial | 25 | 3.69 |
| bad | 35 | 5.17 |

## Loose labels

| label | count | pct |
| --- | --- | --- |
| good | 637 | 94.09 |
| partial | 5 | 0.74 |
| bad | 35 | 5.17 |

## Thresholds (current config)

- steps_min: 50
- stress_any_min_seconds: 21600 (6.0h)
- stress_full_min_seconds: 72000 (20.0h)
- strict_min_score: 4
- loose_min_score: 3

## Coverage metrics

| flag | fraction_true | pct_true |
| --- | --- | --- |
| has_steps | 0.9335 | 93.35 |
| has_hr | 0.9498 | 94.98 |
| has_stress_duration | 0.9778 | 97.78 |
| has_bodybattery_end | 0.8626 | 86.26 |
| has_sleep | 0.8213 | 82.13 |

## Body Battery coverage diagnostics

| has_bodybattery_start | has_bodybattery_end | count | pct |
| --- | --- | --- | --- |
| 1 | 1 | 584 | 86.26 |
| 1 | 0 | 59 | 8.71 |
| 0 | 0 | 34 | 5.02 |

- start present, end missing (`bodybattery_start_without_end`): 59 days (8.71%)
- Interpretation: start-only Body Battery usually means the watch was worn earlier in the day but powered off before end-of-day, so coverage is partial rather than a parser failure.

## Stress duration summary

- min/median/max hours: 0.30, 23.80, 24.95
- days with stressTotalDurationSeconds < 1h: 2
- days with stressTotalDurationSeconds < 6h: 15
- days with stressTotalDurationSeconds < 12h: 51
- days with stressTotalDurationSeconds < 20h: 96

## Duplicate sanity checks

- stress_duration_matches_allDayStress_TOTAL: true=100.00%, false=0.00%, compared_rows=677
- stress_awake_matches_allDayStress_AWAKE: true=100.00%, false=0.00%, compared_rows=677

## Corrupted stress-only days

- count: 21
- percent: 3.10%
- date range: 2024-02-25 to 2025-12-10

## Suspicion reason frequencies (all rows)

| reason | count | pct_of_rows |
| --- | --- | --- |
| has_sleep | 121 | 17.87 |
| full_day_stress | 96 | 14.18 |
| has_bodybattery_end | 93 | 13.74 |
| has_steps | 45 | 6.65 |
| has_hr | 34 | 5.02 |
| corrupted_stress_only_day | 21 | 3.1 |
| has_stress_duration | 15 | 2.22 |

## Suspicion reason frequencies (strict bad rows)

| reason | count | pct_of_rows |
| --- | --- | --- |
| has_bodybattery_end | 35 | 100 |
| has_sleep | 35 | 100 |
| has_hr | 34 | 97.14 |
| has_steps | 34 | 97.14 |
| corrupted_stress_only_day | 21 | 60 |
| full_day_stress | 14 | 40 |
| has_stress_duration | 10 | 28.57 |

## Notes

- Strict validity uses quality_score >= 4.
- Loose validity uses quality_score >= 3.
- Quality labels describe day-level analysis readiness / signal coverage, not medical-grade measurement quality.
- `has_bodybattery_end` is intentionally used (instead of any Body Battery presence) because end-of-day value is more useful for day-outcome analyses.
- Missing sleep often indicates no night coverage for that date.
