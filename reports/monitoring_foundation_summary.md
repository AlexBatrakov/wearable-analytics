# Monitoring Foundation Summary

This report summarizes the local minute-level monitoring foundation built from Garmin FIT monitoring files. It contains only aggregate counts and feature-level diagnostics.

## Outputs

- `data/processed/monitoring_heart_rate.parquet`
- `data/processed/monitoring_stress.parquet`
- `data/processed/semantic_sleep_windows.parquet`
- `data/processed/monitoring_daily_features.parquet`

## Canonical Tables

- Heart-rate rows: `577,615`
- Heart-rate date range: `2023-05-26 to 2026-02-05`
- Stress rows: `764,639`
- Stress date range: `2023-05-26 to 2026-02-05`
- Stress status counts: `{'valid': 579707, 'unmeasurable': 184932}`

## Semantic Windows

- Complete semantic sleep/wake windows: `473`
- Median sleep duration hours: `8.55`
- Median wake duration hours: `15.68`

## Local-Time Offset Metadata

- Windows with local UTC offset: `473`
- Local UTC offset source counts: `{'start_end_agree': 471, 'start_end_disagree_using_start': 2}`

## Baseline Features

- Feature rows: `473`

## Coverage Diagnostics

- `sleep_hr_coverage_fraction` median: `0.688`
- `wake_hr_coverage_fraction` median: `0.873`
- `sleep_stress_coverage_fraction` median: `0.971`
- `wake_stress_coverage_fraction` median: `0.727`

## Stress Status Diagnostics

- `sleep_stress_unmeasurable_fraction` median: `0.023`
- `sleep_stress_status_value_fraction` median: `0.000`
- `sleep_stress_nonvalid_fraction` median: `0.023`
- `wake_stress_unmeasurable_fraction` median: `0.252`
- `wake_stress_status_value_fraction` median: `0.000`
- `wake_stress_nonvalid_fraction` median: `0.252`

## Scope Notes

- Stress values outside `0..100` are preserved as raw status values and excluded from numeric stress metrics.
- This packet intentionally stops at HR/stress monitoring, semantic windows, coverage diagnostics, and a minimal baseline feature table.
- Activity FIT files, movement monitoring, unknown FIT message families, cluster labels, and sleep-rhythm claims remain out of scope.
