# Monitoring Foundation Summary

This report summarizes the local minute-level monitoring foundation built from Garmin FIT monitoring files. It contains only aggregate counts and feature-level diagnostics.

## Outputs

- `data/processed/monitoring_heart_rate.parquet`
- `data/processed/monitoring_stress.parquet`
- `data/processed/semantic_sleep_windows.parquet`
- `data/processed/monitoring_daily_features.parquet`

## Canonical Tables

- Heart-rate rows: `675,325`
- Heart-rate date range: `2023-05-26 to 2026-05-18`
- Stress rows: `889,323`
- Stress date range: `2023-05-26 to 2026-05-18`
- Stress status counts: `{'valid': 674752, 'unmeasurable': 214571}`

## Semantic Windows

- Observed sleep-anchored rows: `556`
- Next sleep status counts: `{'observed_within_cutoff': 490, 'missing_after_cutoff': 65, 'no_following_observed_sleep': 1}`
- Raw observed wake gaps >24h: `65`
- Raw observed wake gaps >48h: `31`
- Raw observed wake gaps >7d: `11`
- Max raw observed wake duration hours: `3830.30`
- Median accepted wake duration hours: `15.35`
- Max accepted wake duration hours: `23.50`
- Median sleep duration hours: `8.59`

## Local-Time Offset Metadata

- Windows with local UTC offset: `556`
- Local UTC offset source counts: `{'start_end_agree': 554, 'start_end_disagree_using_start': 2}`

## Baseline Features

- Feature rows: `556`

## Coverage Diagnostics

- `sleep_hr_coverage_fraction` median: `0.695`
- `wake_hr_coverage_fraction` median: `0.878`
- `sleep_stress_coverage_fraction` median: `0.973`
- `wake_stress_coverage_fraction` median: `0.736`

## Stress Status Diagnostics

- `sleep_stress_unmeasurable_fraction` median: `0.021`
- `sleep_stress_status_value_fraction` median: `0.000`
- `sleep_stress_nonvalid_fraction` median: `0.021`
- `wake_stress_unmeasurable_fraction` median: `0.250`
- `wake_stress_status_value_fraction` median: `0.000`
- `wake_stress_nonvalid_fraction` median: `0.250`

## Scope Notes

- `next_observed_sleep_start_utc` preserves the raw next Garmin sleep observation.
- `next_sleep_start_utc` is populated only when that observation is within the local-noon cutoff.
- Unknown next sleep boundaries are represented explicitly instead of being dropped.
- Stress values outside `0..100` are preserved as raw status values and excluded from numeric stress metrics.
- This packet intentionally stops at HR/stress monitoring, semantic windows, coverage diagnostics, and a minimal baseline feature table.
- Activity FIT files, movement monitoring, unknown FIT message families, cluster labels, and sleep-rhythm claims remain out of scope.
