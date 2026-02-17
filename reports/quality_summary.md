# Quality Summary

Generated at (UTC): 2026-02-17T16:48:42.315232+00:00
Input file: data/processed/daily_sanitized.parquet
Dataset shape: rows=580, columns=191
Date range: 2023-05-26 to 2026-02-05

## Strict labels

| label | count | pct |
| --- | --- | --- |
| good | 525 | 90.51724137931035 |
| partial | 22 | 3.793103448275862 |
| bad | 33 | 5.689655172413794 |

## Loose labels

| label | count | pct |
| --- | --- | --- |
| good | 542 | 93.44827586206897 |
| partial | 5 | 0.8620689655172413 |
| bad | 33 | 5.689655172413794 |

## Coverage metrics

| flag | fraction_true | pct_true |
| --- | --- | --- |
| has_steps | 0.9293 | 92.93 |
| has_hr | 0.9448 | 94.48 |
| has_stress_duration | 0.9776 | 97.76 |
| has_bodybattery_end | 0.8569 | 85.69 |
| has_sleep | 0.8172 | 81.72 |

## Stress duration summary

- min/median/max hours: 0.3, 23.8, 24.95
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

## Notes

- Strict validity uses quality_score >= 4.
- Loose validity uses quality_score >= 3.
- Missing sleep often indicates no night coverage for that date.
