# Stage 4 Sleep Outcome Modeling Frame

This report documents the reusable Stage 4 `day D -> next sleep` modeling frame. It covers row construction, target alignment, feature-set definitions, and the default split contract. It does not fit models or make final predictive claims.

## Outputs

- `data/processed/stage4_sleep_modeling_frame.parquet`
- `reports/stage4_sleep_modeling_feature_sets.csv`
- `reports/stage4_sleep_modeling_feature_sets.md`

## Frame Shape

- Rows: `589`
- Columns: `295`
- Date range: `2023-05-27 to 2026-05-18`

## Row And Target Availability

| metric | rows |
| --- | --- |
| analysis_rows | 589 |
| modeling_recovery_v0_eligible | 472 |
| primary_target_available | 524 |
| eligible_with_primary_target | 472 |

## Target Columns

| target | available_rows |
| --- | --- |
| target_avgSleepStress_next_sleep | 524 |
| target_sleepRecoveryScore_next_sleep | 523 |
| target_sleepOverallScore_next_sleep | 523 |
| target_sleepQualityScore_next_sleep | 523 |
| target_sleep_opportunity_hours_next_sleep | 524 |
| target_sleep_start_hour_local_wrapped_next_sleep | 524 |

Targets are aligned by exact next-sleep start timestamp from the monitoring quality index to the sleep table. The primary target is next-sleep `avgSleepStress`; opportunity and local start-hour targets are retained for audit and future sensitivity work.

## Default Split

- Strategy: `past_random_valid_future_test`
- Fractions: `0.70/0.15/0.15`
- Random seed for past train/validation split: `42`

| split | rows | eligible_rows | primary_target_rows | start_date | end_date |
| --- | --- | --- | --- | --- | --- |
| train | 330 | 330 | 330 | 2023-05-27 | 2026-01-28 |
| valid | 71 | 71 | 71 | 2023-06-12 | 2026-01-20 |
| test | 71 | 71 | 71 | 2026-01-29 | 2026-05-13 |
| not_eligible_or_missing_target | 117 | 0 | 52 | 2023-07-10 | 2026-05-18 |

The test split is the final time block among eligible rows with the primary target. Train and validation rows are assigned randomly inside the earlier history with the fixed seed.

## Feature Sets

| feature_set | features | numeric_features | categorical_features | complete_modeling_rows | median_missing_pct_modeling_rows | max_missing_pct_modeling_rows | source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| aggregate_stage3_baseline | 33 | 32 | 1 | 469 | 0.000 | 0.636 | aggregate Stage 3 |
| monitoring_core_wake_pre_sleep | 56 | 56 | 0 | 464 | 0.000 | 1.271 | monitoring core v0 |
| monitoring_full_wake_pre_sleep | 123 | 123 | 0 | 393 | 0.000 | 15.254 | monitoring full v0 catalog |
| aggregate_plus_monitoring_full | 138 | 137 | 1 | 393 | 0.000 | 15.254 | monitoring full v0 plus aggregate context |

## Leakage Controls

- Monitoring predictors are limited to wake and pre-sleep columns.
- Sleep-phase monitoring columns remain out of the predictor feature sets in this frame.
- Quality and boundary diagnostics are retained for audit, not as ordinary predictors.
- Sleep-start local time is included as schedule context because the wake/pre-sleep feature window is defined at sleep onset.
- Next-sleep duration/opportunity remains target/audit context, not an ordinary predictor.
- The combined monitoring-plus-aggregate set excludes aggregate wake HR/stress features that duplicate monitoring signals too directly.

## Limitations

This is a single-subject observational wearable dataset. The frame is a reproducible modeling input contract, not evidence of final model performance.
