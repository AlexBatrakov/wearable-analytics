# Monitoring Feature Library Summary

This report summarizes the local Packet 03 monitoring feature library built from Packet 02 canonical HR/stress rows and semantic sleep/wake windows. It contains aggregate diagnostics only.

## Outputs

- `data/processed/monitoring_feature_library.parquet`
- `reports/monitoring_feature_catalog.csv`
- `reports/monitoring_feature_catalog.md`

## Build Parameters

- Maximum heart rate parameter: `192` bpm
- Gap break threshold: `2` minutes
- Minimum valid minutes for window/trend summaries: `5`
- Minimum paired HR/stress minutes for correlation/regression: `10`

## Table Shape

- Rows: `473`
- Columns: `526`
- Calendar date range: `2023-05-27 to 2026-02-04`

## Catalog Diagnostics

- Feature families: `15`
- Numeric columns: `518`
- Duplicate columns: `0`
- Duplicate dates: `0`
- Infinite numeric values: `0`
- Constant non-null columns: `18`
- Mostly missing columns (`missing_pct >= 90`): `12`
- All-null columns: `0`
- Fraction/coverage columns outside `0..1`: `0`

Constant columns are diagnostics and will be filtered or selected intentionally in later EDA/modeling steps.

## Entropy Policy

- Stress histogram entropy uses fixed Garmin-like stress-state bins over valid `0..100` values: `0..25`, `26..50`, `51..75`, and `76..100`.
- HR histogram entropy uses fixed maximum-heart-rate zone bins derived from `max_hr_bpm`: below 50%, 50..60%, 60..70%, 70..80%, 80..90%, 90..100%, and above 100% MHR.
- Entropy is comparable across days for a fixed `max_hr_bpm`; it does not use per-day dynamic min/max bin edges.

## Feature Families

- Distribution and shape: `sleep_hr_p05`, `wake_stress_iqr`, `sleep_hr_histogram_entropy`, `wake_stress_mad`
- Stress states and HR zones: `wake_stress_frac_high_76_100`, `sleep_stress_frac_resting_0_25`, `wake_hr_frac_zone2_60_70`, `wake_hr_frac_above_mhr`
- Gap-aware variability: `wake_hr_mean_abs_diff`, `wake_stress_roughness`, `sleep_hr_diff_gap_break_count`, `wake_stress_longest_missing_gap_minutes`
- Episodes and state structure: `wake_stress_high_episode_count`, `wake_stress_elevated_total_minutes`, `wake_hr_zone1_plus_episode_count`, `sleep_stress_state_transition_count`
- Recovery and windows: `sleep_hr_first_60m_minus_last_60m`, `pre_sleep_4h_stress_mean`, `evening_deactivation_hr`, `wake_q4_stress_high_fraction`
- Trends and contrasts: `wake_stress_slope_per_hour`, `sleep_hr_end_minus_start`, `hr_wake_mean_minus_sleep_mean`, `stress_wake_high_fraction_minus_sleep`
- HR/stress coupling: `wake_paired_hr_stress_valid_minutes`, `wake_hr_stress_corr`, `wake_frac_hr_zone1_plus_stress_elevated`, `sleep_stress_hr_slope`
- Raw stress status: `wake_stress_raw_minus_1_fraction`, `wake_stress_raw_minus_2_fraction`, `wake_stress_large_motion_proxy_fraction`, `sleep_stress_raw_valid_fraction`

## Coverage Diagnostics

- `sleep_hr_coverage_fraction` median: `0.688`
- `wake_hr_coverage_fraction` median: `0.873`
- `sleep_stress_coverage_fraction` median: `0.971`
- `wake_stress_coverage_fraction` median: `0.727`
- `sleep_paired_hr_stress_coverage_fraction` median: `0.669`
- `wake_paired_hr_stress_coverage_fraction` median: `0.629`

## Selected Summary Diagnostics

- `wake_stress_frac_high_76_100` median: `0.241`
- `wake_hr_frac_zone2_plus` median: `0.017`
- `wake_stress_raw_minus_1_fraction` median: `0.051`
- `wake_stress_raw_minus_2_fraction` median: `0.171`
- `wake_stress_large_motion_proxy_fraction` median: `0.171`
- `wake_stress_high_episode_count` median: `46.000`
- `wake_hr_mean_abs_diff` median: `4.385`
- `stress_wake_mean_minus_sleep_mean` median: `41.013`

## Scope Notes

- Numeric stress features use only valid `0..100` stress values.
- Raw stress `-1` and `-2` values are represented only as status/proxy features.
- The `-2` large-motion proxy is not treated as activity ground truth or high stress.
- This packet does not add composite scores, bands, spectral features, SQL mart changes, or supervised modeling lag features.
