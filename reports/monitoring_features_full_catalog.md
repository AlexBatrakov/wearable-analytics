# Monitoring Feature Catalog

This catalog summarizes the columns in `data/processed/monitoring_features_full_v0.parquet`. The full row-level feature dictionary is in the CSV output.

## Outputs

- Full CSV catalog: `reports/monitoring_features_full_catalog.csv`
- Markdown summary: `reports/monitoring_features_full_catalog.md`

## Feature Family Counts

- identity/window metadata: `2`
- distribution/shape: `60`
- stress state fractions: `10`
- HR MHR zones: `14`
- variability/gaps: `20`
- episodes/state structure: `35`
- recovery/deactivation: `14`
- relative windows: `56`
- trends: `12`
- sleep-wake contrast: `8`
- HR/stress coupling: `12`

## Family Guide

- identity/window metadata: Semantic-day identifiers, UTC/local sleep and wake boundaries, durations, and local offset metadata.
- distribution/shape: Robust and standard summaries of valid HR or numeric stress values; entropy uses fixed bins.
- stress state fractions: Shares of eligible raw stress minutes in fixed Garmin-like states, including active proxy from raw `-2` only when same-minute valid HR confirms activity.
- HR MHR zones: Shares of valid HR minutes in fixed zones derived from the configured maximum heart rate.
- variability/gaps: Gap-aware first-difference roughness and jump diagnostics without interpolation.
- episodes/state structure: Contiguous runs of stress or HR states with gap breaks; no-event cases have `has_event = 0` and zero duration summaries.
- recovery/deactivation: Sleep decline and pre-sleep deactivation summaries.
- relative windows: Compact summaries for sleep/wake quarters.
- trends: Simple linear slopes and trend fit quality computed over available valid points.
- sleep-wake contrast: Direct wake-minus-sleep physiology and state-fraction differences.
- HR/stress coupling: Same-minute paired HR and valid numeric stress relationships.

## Constant Non-Null Columns

Constant columns are diagnostics. Some are constant only because they have very few non-null values; modeling and first-pass EDA should filter/select features intentionally.

| column | family | missing_pct | n_unique | caution |
| --- | --- | --- | --- | --- |
| wake_hr_frac_above_mhr | HR MHR zones | 5.622489959839357 | 1 | constant among non-null values; sparse or rare-event style feature |
| wake_stress_active_has_event | episodes/state structure | 5.622489959839357 | 1 | constant among non-null values |
| sleep_frac_hr_zone2_plus_stress_high | HR/stress coupling | 4.819277108433735 | 1 | constant among non-null values; sparse or rare-event style feature; requires paired valid HR and stress minutes |
| sleep_hr_frac_above_mhr | HR MHR zones | 4.819277108433735 | 1 | constant among non-null values; sparse or rare-event style feature |
| sleep_hr_frac_zone3 | HR MHR zones | 4.819277108433735 | 1 | constant among non-null values; sparse or rare-event style feature |
| sleep_hr_frac_zone4 | HR MHR zones | 4.819277108433735 | 1 | constant among non-null values; sparse or rare-event style feature |
| sleep_hr_frac_zone5 | HR MHR zones | 4.819277108433735 | 1 | constant among non-null values; sparse or rare-event style feature |

## Mostly Missing Columns

Columns below use `missing_pct >= 90` as the mostly-missing threshold.

| column | family | missing_pct | non_null_count | n_unique |
| --- | --- | --- | --- | --- |
| sleep_hr_zone1_plus_time_to_first_minutes | episodes/state structure | 95.98393574297188 | 20 | 20 |

## Useful Starting Columns By Family

These are non-constant, not-mostly-missing catalog candidates, intended as a starting point rather than a final model feature set.

| column | family | signal | phase | window | missing_pct |
| --- | --- | --- | --- | --- | --- |
| sleep_hr_frac_below_zone1 | HR MHR zones | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_frac_zone1 | HR MHR zones | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_frac_zone2 | HR MHR zones | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_frac_hr_below_zone1_stress_high | HR/stress coupling | hr+stress | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_diff_stress_diff_corr | HR/stress coupling | hr+stress | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_stress_corr | HR/stress coupling | hr+stress | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_histogram_entropy | distribution/shape | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_iqr | distribution/shape | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_kurtosis | distribution/shape | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_zone1_plus_episode_count | episodes/state structure | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_zone1_plus_fragmentation_index | episodes/state structure | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_zone1_plus_has_event | episodes/state structure | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_time_to_min_minutes | recovery/deactivation | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_stress_time_to_min_minutes | recovery/deactivation | stress | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_q1_minus_q4 | recovery/deactivation | hr | sleep | sleep_phase | 5.020080321285141 |
| sleep_q1_hr_mean | relative windows | hr | sleep | sleep_q1 | 4.819277108433735 |
| sleep_q1_hr_p90 | relative windows | hr | sleep | sleep_q1 | 4.819277108433735 |
| sleep_q1_hr_std | relative windows | hr | sleep | sleep_q1 | 4.819277108433735 |
| hr_wake_mean_minus_sleep_mean | sleep-wake contrast | hr | sleep-wake | not_windowed | 10.441767068273093 |
| hr_wake_median_minus_sleep_median | sleep-wake contrast | hr | sleep-wake | not_windowed | 10.441767068273093 |
| hr_wake_p90_minus_sleep_p90 | sleep-wake contrast | hr | sleep-wake | not_windowed | 10.441767068273093 |
| sleep_stress_frac_active | stress state fractions | stress | sleep | sleep_phase | 4.819277108433735 |
| sleep_stress_frac_high | stress state fractions | stress | sleep | sleep_phase | 4.819277108433735 |
| sleep_stress_frac_low | stress state fractions | stress | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_slope_per_hour | trends | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_trend_r2 | trends | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_stress_slope_per_hour | trends | stress | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_max_abs_jump | variability/gaps | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_mean_abs_diff | variability/gaps | hr | sleep | sleep_phase | 4.819277108433735 |
| sleep_hr_median_abs_diff | variability/gaps | hr | sleep | sleep_phase | 4.819277108433735 |

## Entropy Policy

- Stress histogram entropy uses fixed Garmin-like stress-state bins across valid `0..100` stress values: `0..25`, `26..50`, `51..75`, and `76..100`.
- HR histogram entropy uses fixed maximum-heart-rate zone bins derived from the configured `max_hr_bpm`: below 50%, 50..60%, 60..70%, 70..80%, 80..90%, 90..100%, and above 100% MHR.
- Entropy is therefore comparable across days for a fixed `max_hr_bpm`; it is not computed from per-day dynamic min/max bin edges.

## Notes

- Numeric stress features use only valid `0..100` stress values.
- Raw stress `-1` is excluded from feature-state denominators and remains a quality diagnostic.
- Raw stress `-2` appears in feature-state fractions only through `stress_frac_active` when same-minute valid HR confirms activity.
- Raw stress `-2` without same-minute valid HR remains an unmeasurable/status diagnostic, not activity.
- Episode no-event cases are represented with `has_event = 0`, zero duration summaries, and undefined time-to-event fields.
- Candidate model feature flags are first-pass guidance only; Modeling v2 should still apply leakage-safe feature selection.
