# Monitoring Feature Catalog

This catalog summarizes the columns in `data/processed/monitoring_feature_library.parquet`. The full row-level feature dictionary is in the CSV output.

## Outputs

- Full CSV catalog: `reports/monitoring_feature_catalog.csv`
- Markdown summary: `reports/monitoring_feature_catalog.md`

## Feature Family Counts

- identity/window metadata: `11`
- foundation coverage: `24`
- distribution/shape: `76`
- stress state fractions: `10`
- HR MHR zones: `20`
- variability/gaps: `32`
- missingness/coverage: `16`
- episodes/state structure: `78`
- recovery/deactivation: `24`
- relative windows: `96`
- anchored windows: `72`
- trends: `18`
- sleep-wake contrast: `11`
- HR/stress coupling: `20`
- raw stress status: `18`

## Family Guide

- identity/window metadata: Semantic-day identifiers, UTC/local sleep and wake boundaries, durations, and local offset metadata.
- foundation coverage: Packet 02 baseline counts, coverage fractions, and status diagnostics carried forward for filtering and audit.
- distribution/shape: Robust and standard summaries of valid HR or numeric stress values; entropy uses fixed bins.
- stress state fractions: Shares of valid stress minutes in fixed Garmin-like 0..100 stress states.
- HR MHR zones: Shares of valid HR minutes in fixed zones derived from the configured maximum heart rate.
- variability/gaps: Gap-aware first-difference roughness and jump diagnostics without interpolation.
- missingness/coverage: Missing-gap and paired-coverage diagnostics for data quality filtering.
- episodes/state structure: Contiguous runs of stress or HR states with gap breaks.
- recovery/deactivation: Sleep decline and pre-sleep deactivation summaries.
- relative windows: Compact summaries for sleep/wake quarters.
- anchored windows: Compact summaries for fixed windows around wake and sleep boundaries.
- trends: Simple linear slopes, trend fit quality, and smoothed endpoint contrasts.
- sleep-wake contrast: Direct wake-minus-sleep physiology and state-fraction differences.
- HR/stress coupling: Same-minute paired HR and valid numeric stress relationships.
- raw stress status: Raw stress status/proxy diagnostics; negative raw values are not stress scores.

## Constant Non-Null Columns

Constant columns are diagnostics. Some are constant only because they have very few non-null values; modeling and first-pass EDA should filter/select features intentionally.

| column | family | missing_pct | n_unique | caution |
| --- | --- | --- | --- | --- |
| sleep_hr_zone2_plus_fragmentation_index | episodes/state structure | 99.78858350951374 | 1 | constant among non-null values; mostly missing; inspect before EDA/modeling |
| sleep_hr_zone2_plus_max_duration_minutes | episodes/state structure | 99.78858350951374 | 1 | constant among non-null values; mostly missing; inspect before EDA/modeling |
| sleep_hr_zone2_plus_mean_duration_minutes | episodes/state structure | 99.78858350951374 | 1 | constant among non-null values; mostly missing; inspect before EDA/modeling |
| sleep_hr_zone2_plus_median_duration_minutes | episodes/state structure | 99.78858350951374 | 1 | constant among non-null values; mostly missing; inspect before EDA/modeling |
| sleep_hr_zone2_plus_time_since_last_minutes | episodes/state structure | 99.78858350951374 | 1 | constant among non-null values; mostly missing; inspect before EDA/modeling |
| sleep_hr_zone2_plus_time_to_first_minutes | episodes/state structure | 99.78858350951374 | 1 | constant among non-null values; mostly missing; inspect before EDA/modeling |
| sleep_frac_hr_zone1_plus_stress_low_or_resting | HR/stress coupling | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature; requires paired valid HR and stress minutes |
| sleep_frac_hr_zone2_plus_stress_elevated | HR/stress coupling | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature; requires paired valid HR and stress minutes |
| sleep_hr_frac_above_mhr | HR MHR zones | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature |
| sleep_hr_frac_zone3_70_80 | HR MHR zones | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature |
| sleep_hr_frac_zone3_plus | HR MHR zones | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature |
| sleep_hr_frac_zone4_80_90 | HR MHR zones | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature |
| sleep_hr_frac_zone5_90_100 | HR MHR zones | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature |
| sleep_stress_status_value_count | foundation coverage | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature |
| sleep_stress_status_value_fraction | foundation coverage | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature |
| wake_hr_frac_above_mhr | HR MHR zones | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature |
| wake_stress_status_value_count | foundation coverage | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature |
| wake_stress_status_value_fraction | foundation coverage | 0.0 | 1 | constant among non-null values; sparse or rare-event style feature |

## Mostly Missing Columns

Columns below use `missing_pct >= 90` as the mostly-missing threshold.

| column | family | missing_pct | non_null_count | n_unique |
| --- | --- | --- | --- | --- |
| sleep_hr_zone2_plus_fragmentation_index | episodes/state structure | 99.78858350951374 | 1 | 1 |
| sleep_hr_zone2_plus_max_duration_minutes | episodes/state structure | 99.78858350951374 | 1 | 1 |
| sleep_hr_zone2_plus_mean_duration_minutes | episodes/state structure | 99.78858350951374 | 1 | 1 |
| sleep_hr_zone2_plus_median_duration_minutes | episodes/state structure | 99.78858350951374 | 1 | 1 |
| sleep_hr_zone2_plus_time_since_last_minutes | episodes/state structure | 99.78858350951374 | 1 | 1 |
| sleep_hr_zone2_plus_time_to_first_minutes | episodes/state structure | 99.78858350951374 | 1 | 1 |
| sleep_hr_zone1_plus_fragmentation_index | episodes/state structure | 95.77167019027483 | 20 | 6 |
| sleep_hr_zone1_plus_max_duration_minutes | episodes/state structure | 95.77167019027483 | 20 | 6 |
| sleep_hr_zone1_plus_mean_duration_minutes | episodes/state structure | 95.77167019027483 | 20 | 6 |
| sleep_hr_zone1_plus_median_duration_minutes | episodes/state structure | 95.77167019027483 | 20 | 5 |
| sleep_hr_zone1_plus_time_since_last_minutes | episodes/state structure | 95.77167019027483 | 20 | 20 |
| sleep_hr_zone1_plus_time_to_first_minutes | episodes/state structure | 95.77167019027483 | 20 | 20 |

## Useful Starting Columns By Family

These are non-constant, not-mostly-missing catalog candidates, intended as a starting point rather than a final model feature set.

| column | family | signal | phase | window | missing_pct |
| --- | --- | --- | --- | --- | --- |
| sleep_hr_frac_below_zone1 | HR MHR zones | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_frac_zone1_50_60 | HR MHR zones | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_frac_zone1_plus | HR MHR zones | hr | sleep | sleep_phase | 0.0 |
| sleep_frac_hr_below_zone1_stress_high | HR/stress coupling | hr+stress | sleep | sleep_phase | 0.0 |
| sleep_frac_hr_zone1_plus_stress_elevated | HR/stress coupling | hr+stress | sleep | sleep_phase | 0.0 |
| sleep_hr_diff_stress_diff_corr | HR/stress coupling | hr+stress | sleep | sleep_phase | 0.0 |
| first_2h_after_wake_hr_coverage_fraction | anchored windows | hr | wake | first_2h_after_wake | 0.0 |
| first_2h_after_wake_hr_valid_count | anchored windows | hr | wake | first_2h_after_wake | 0.0 |
| first_2h_after_wake_stress_coverage_fraction | anchored windows | stress | wake | first_2h_after_wake | 0.0 |
| sleep_hr_coefficient_of_variation | distribution/shape | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_histogram_entropy | distribution/shape | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_iqr | distribution/shape | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_longest_below_zone1_episode_minutes | episodes/state structure | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_state_transition_count | episodes/state structure | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_transitions_per_valid_hour | episodes/state structure | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_coverage_fraction | foundation coverage | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_total_count | foundation coverage | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_valid_count | foundation coverage | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_large_gap_count | missingness/coverage | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_longest_missing_gap_minutes | missingness/coverage | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_missing_gap_count | missingness/coverage | hr | sleep | sleep_phase | 0.0 |
| sleep_stress_large_motion_proxy_fraction | raw stress status | stress | sleep | sleep_phase | 0.0 |
| sleep_stress_large_motion_proxy_minutes | raw stress status | stress | sleep | sleep_phase | 0.0 |
| sleep_stress_raw_minus_1_count | raw stress status | stress | sleep | sleep_phase | 0.0 |
| pre_sleep_2h_hr_mean | recovery/deactivation | hr | wake/pre-sleep | pre_sleep_2h | 0.0 |
| pre_sleep_2h_stress_high_fraction | recovery/deactivation | stress | wake/pre-sleep | pre_sleep_2h | 0.0 |
| pre_sleep_2h_stress_mean | recovery/deactivation | stress | wake/pre-sleep | pre_sleep_2h | 0.0 |
| sleep_q1_hr_coverage_fraction | relative windows | hr | sleep | sleep_q1 | 0.0 |
| sleep_q1_hr_mean | relative windows | hr | sleep | sleep_q1 | 0.0 |
| sleep_q1_hr_p90 | relative windows | hr | sleep | sleep_q1 | 0.0 |
| hr_sleep_reduction_from_wake | sleep-wake contrast | hr | sleep-wake | not_windowed | 0.0 |
| hr_wake_mean_minus_sleep_mean | sleep-wake contrast | hr | sleep-wake | not_windowed | 0.0 |
| hr_wake_median_minus_sleep_median | sleep-wake contrast | hr | sleep-wake | not_windowed | 0.0 |
| sleep_stress_frac_high_76_100 | stress state fractions | stress | sleep | sleep_phase | 0.0 |
| sleep_stress_frac_low_26_50 | stress state fractions | stress | sleep | sleep_phase | 0.0 |
| sleep_stress_frac_medium_51_75 | stress state fractions | stress | sleep | sleep_phase | 0.0 |
| pre_sleep_4h_hr_slope_per_hour | trends | hr | wake/pre-sleep | pre_sleep_4h | 0.0 |
| pre_sleep_4h_hr_trend_r2 | trends | hr | wake/pre-sleep | pre_sleep_4h | 0.0 |
| pre_sleep_4h_stress_slope_per_hour | trends | stress | wake/pre-sleep | pre_sleep_4h | 0.0 |
| sleep_hr_diff_gap_break_count | variability/gaps | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_diff_valid_pair_count | variability/gaps | hr | sleep | sleep_phase | 0.0 |
| sleep_hr_longest_observed_gap_minutes | variability/gaps | hr | sleep | sleep_phase | 0.0 |

## Entropy Policy

- Stress histogram entropy uses fixed Garmin-like stress-state bins across valid `0..100` stress values: `0..25`, `26..50`, `51..75`, and `76..100`.
- HR histogram entropy uses fixed maximum-heart-rate zone bins derived from the configured `max_hr_bpm`: below 50%, 50..60%, 60..70%, 70..80%, 80..90%, 90..100%, and above 100% MHR.
- Entropy is therefore comparable across days for a fixed `max_hr_bpm`; it is not computed from per-day dynamic min/max bin edges.

## Notes

- Numeric stress features use only valid `0..100` stress values.
- Raw stress `-1` and `-2` values remain status/proxy diagnostics.
- Candidate model feature flags are first-pass guidance only; Modeling v2 should still apply leakage-safe feature selection.
