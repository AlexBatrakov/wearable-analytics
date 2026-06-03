# Stage 4 Sleep Modeling Feature Sets

This catalog defines the reusable feature spaces for the Stage 4 sleep-outcome modeling frame. It defines inputs only; no models are fit here.

## Feature Set Sizes

| feature_set | features | numeric_features | categorical_features | complete_modeling_rows | median_missing_pct_modeling_rows | max_missing_pct_modeling_rows | source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| aggregate_stage3_baseline | 33 | 32 | 1 | 469 | 0.000 | 0.636 | aggregate Stage 3 |
| monitoring_core_wake_pre_sleep | 56 | 56 | 0 | 464 | 0.000 | 1.271 | monitoring core v0 |
| monitoring_full_wake_pre_sleep | 123 | 123 | 0 | 393 | 0.000 | 15.254 | monitoring full v0 catalog |
| aggregate_plus_monitoring_full | 138 | 137 | 1 | 393 | 0.000 | 15.254 | monitoring full v0 plus aggregate context |

## Aggregate Candidate Review

Aggregate columns are prefixed with `agg__` in the modeling frame. Sleep-start local time is included as schedule context. Direct wake HR/stress overlaps remain available in the aggregate-only baseline, while the combined feature set adds only non-overlapping aggregate day context.

| review_group | include_in_aggregate_plus_monitoring_full | features |
| --- | --- | --- |
| direct_monitoring_overlap | False | 17 |
| non_overlapping_day_context | True | 15 |

## Feature Family Counts

| feature_set | family | features |
| --- | --- | --- |
| aggregate_plus_monitoring_full | distribution/shape | 30 |
| aggregate_plus_monitoring_full | relative windows | 28 |
| aggregate_plus_monitoring_full | episodes/state structure | 20 |
| aggregate_plus_monitoring_full | non_overlapping_day_context | 15 |
| aggregate_plus_monitoring_full | variability/gaps | 10 |
| aggregate_plus_monitoring_full | recovery/deactivation | 9 |
| aggregate_plus_monitoring_full | trends | 8 |
| aggregate_plus_monitoring_full | HR MHR zones | 6 |
| aggregate_plus_monitoring_full | HR/stress coupling | 6 |
| aggregate_plus_monitoring_full | stress state fractions | 5 |
| aggregate_plus_monitoring_full | schedule/context | 1 |
| aggregate_stage3_baseline | direct_monitoring_overlap | 17 |
| aggregate_stage3_baseline | non_overlapping_day_context | 15 |
| aggregate_stage3_baseline | schedule/context | 1 |
| monitoring_core_wake_pre_sleep | relative windows | 12 |
| monitoring_core_wake_pre_sleep | distribution/shape | 10 |
| monitoring_core_wake_pre_sleep | recovery/deactivation | 9 |
| monitoring_core_wake_pre_sleep | trends | 8 |
| monitoring_core_wake_pre_sleep | HR MHR zones | 7 |
| monitoring_core_wake_pre_sleep | stress state fractions | 5 |
| monitoring_core_wake_pre_sleep | variability/gaps | 4 |
| monitoring_core_wake_pre_sleep | schedule/context | 1 |
| monitoring_full_wake_pre_sleep | distribution/shape | 30 |
| monitoring_full_wake_pre_sleep | relative windows | 28 |
| monitoring_full_wake_pre_sleep | episodes/state structure | 20 |
| monitoring_full_wake_pre_sleep | variability/gaps | 10 |
| monitoring_full_wake_pre_sleep | recovery/deactivation | 9 |
| monitoring_full_wake_pre_sleep | trends | 8 |
| monitoring_full_wake_pre_sleep | HR MHR zones | 6 |
| monitoring_full_wake_pre_sleep | HR/stress coupling | 6 |
| monitoring_full_wake_pre_sleep | stress state fractions | 5 |
| monitoring_full_wake_pre_sleep | schedule/context | 1 |
