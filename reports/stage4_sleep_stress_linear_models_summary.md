# Stage 4 Sleep Stress Linear Models

This report evaluates linear-family regression models for next-sleep average stress using the Stage 4 `day D -> next sleep` modeling frame. It is an exploratory single-subject modeling pass, not a production predictor or health recommendation.

## Modeling Setup

- Target: `target_avgSleepStress_next_sleep`
- Feature set: `monitoring_full_wake_pre_sleep_plus_state`
- Candidate features: `148`
- Grid source: `control_panel`
- Grid preset: not used
- Split strategy: `split_past_random_valid_future_test` with a fixed future holdout excluded from model selection
- Tuning: `10` random holdouts plus `8` expanding temporal holdouts inside the pre-test history
- Tuning metric: `mae`
- Parallel candidate jobs: `8` with `loky` backend
- Definitive rerank candidates: `150` linear-family configurations
- Representative validation shortlist: `150` candidates
- Validation-selected finalists refit on all dev rows before fixed-future-holdout evaluation: `6`
- Dummy baselines: `dummy_mean, dummy_median, dummy_last`
- Comparison baseline selected before fixed-future-holdout evaluation: `dummy_median`

Preprocessing is fit inside each training split: numeric median imputation, optional train-fitted z clipping, standardization, and categorical one-hot encoding when categorical predictors are present. Feature selection and optional linear calibration are also fit without using validation or test target values; calibration uses out-of-fold pre-test predictions.

The saved notebook first screened `52,812` configurations on `3` random plus `3` expanding-temporal holdouts, then reranked the representative `150`-candidate shortlist shown in this report on `10` random plus `8` temporal holdouts. The search intentionally favors deeper mixed validation over maximizing the number of unique configurations.

Model selection uses a combined rank led by temporal mean relative MAE, with temporal worst-fold performance and random-holdout performance/stability as secondary criteria. Relative MAE is measured against `dummy_median` fit on each holdout's training rows. The fixed future holdout is evaluated only after validation-selected finalists are frozen and refit on all development rows. Any future-holdout ordering among finalists is diagnostic only, not a tuning rule.

## Validation Leaders

| selection_rank | candidate_short_label | model_kind | model_param_1 | model_param_2 | feature_selection_mode | feature_selection_param_1 | feature_selection_param_2 | robust_clip | calibration | mean_train_mae | mean_train_rmse | mean_train_r2 | mean_valid_mae | std_valid_mae | mean_valid_rmse | mean_valid_r2 | mean_valid_spearman | mean_selected_feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Huber alpha=30 eps=1.05 \| correlation_prune_0.9 \| clip=z=4 | huber | alpha=30 | epsilon=1.05 | correlation_prune | corr=0.9 | min_features=8 | z=4 | none | 3.157 | 5.134 | 0.464 | 3.587 | 0.505 | 4.995 | 0.336 | 0.587 | 98.222 |
| 2 | Huber alpha=30 eps=1.1 \| correlation_prune_0.9 \| clip=z=4 | huber | alpha=30 | epsilon=1.1 | correlation_prune | corr=0.9 | min_features=8 | z=4 | none | 3.175 | 5.112 | 0.468 | 3.583 | 0.508 | 4.998 | 0.336 | 0.587 | 98.222 |
| 3 | Huber alpha=30 eps=1.1 \| correlation_prune_0.95 \| clip=z=4 | huber | alpha=30 | epsilon=1.1 | correlation_prune | corr=0.95 | min_features=8 | z=4 | none | 3.108 | 5.041 | 0.483 | 3.573 | 0.460 | 4.990 | 0.336 | 0.593 | 120.278 |
| 4 | Huber alpha=30 eps=1.1 \| correlation_prune_0.9 \| clip=z=5 | huber | alpha=30 | epsilon=1.1 | correlation_prune | corr=0.9 | min_features=8 | z=5 | none | 3.172 | 5.102 | 0.470 | 3.584 | 0.501 | 4.994 | 0.337 | 0.587 | 98.222 |
| 5 | Huber alpha=30 eps=1.15 \| correlation_prune_0.9 \| clip=z=5 | huber | alpha=30 | epsilon=1.15 | correlation_prune | corr=0.9 | min_features=8 | z=5 | none | 3.189 | 5.085 | 0.474 | 3.581 | 0.504 | 4.992 | 0.337 | 0.589 | 98.222 |
| 6 | Huber alpha=30 eps=1.15 \| correlation_prune_0.9 \| clip=z=4 | huber | alpha=30 | epsilon=1.15 | correlation_prune | corr=0.9 | min_features=8 | z=4 | none | 3.192 | 5.092 | 0.473 | 3.580 | 0.506 | 4.999 | 0.336 | 0.587 | 98.222 |
| 7 | Huber alpha=30 eps=1.2 \| correlation_prune_0.9 \| clip=z=5 | huber | alpha=30 | epsilon=1.2 | correlation_prune | corr=0.9 | min_features=8 | z=5 | none | 3.203 | 5.066 | 0.478 | 3.577 | 0.501 | 4.988 | 0.338 | 0.590 | 98.222 |
| 8 | Huber alpha=30 eps=1.05 \| correlation_prune_0.95 \| clip=z=4 | huber | alpha=30 | epsilon=1.05 | correlation_prune | corr=0.95 | min_features=8 | z=4 | none | 3.092 | 5.070 | 0.477 | 3.580 | 0.454 | 4.990 | 0.335 | 0.596 | 120.278 |
| 9 | Huber alpha=30 eps=1.2 \| correlation_prune_0.9 \| clip=z=4 | huber | alpha=30 | epsilon=1.2 | correlation_prune | corr=0.9 | min_features=8 | z=4 | none | 3.206 | 5.073 | 0.476 | 3.577 | 0.504 | 4.996 | 0.336 | 0.588 | 98.222 |
| 10 | Huber alpha=30 eps=1.05 \| correlation_prune_0.9 \| clip=z=5 | huber | alpha=30 | epsilon=1.05 | correlation_prune | corr=0.9 | min_features=8 | z=5 | none | 3.154 | 5.124 | 0.466 | 3.594 | 0.498 | 4.999 | 0.334 | 0.585 | 98.222 |

## Best Validation Candidate By Model

| selection_rank | candidate_short_label | model_kind | model_param_1 | model_param_2 | feature_selection_mode | feature_selection_param_1 | feature_selection_param_2 | robust_clip | calibration | mean_train_mae | mean_train_rmse | mean_train_r2 | mean_valid_mae | std_valid_mae | mean_valid_rmse | mean_valid_r2 | mean_valid_spearman | mean_selected_feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Huber alpha=30 eps=1.05 \| correlation_prune_0.9 \| clip=z=4 | huber | alpha=30 | epsilon=1.05 | correlation_prune | corr=0.9 | min_features=8 | z=4 | none | 3.157 | 5.134 | 0.464 | 3.587 | 0.505 | 4.995 | 0.336 | 0.587 | 98.222 |
| 30 | ElasticNet alpha=0.1 l1=0.1 \| top_mutual_info_60 \| clip=z=4 \| target=log1p | elastic_net | alpha=0.1 | l1_ratio=0.1 | top_mutual_info | top_k=60 | min_features=8 | z=4 | none | 3.504 | 5.002 | 0.489 | 3.651 | 0.496 | 4.976 | 0.335 | 0.584 | 60.000 |
| 49 | Lasso alpha=0.01 \| correlation_prune_0.9 \| clip=none \| target=log1p | lasso | alpha=0.01 |  | correlation_prune | corr=0.9 | min_features=8 | none | none | 3.260 | 4.667 | 0.554 | 3.590 | 0.478 | 4.931 | 0.346 | 0.606 | 98.222 |
| 96 | Linear \| spearman_then_correlation_80_corr0.95 \| clip=z=4 \| cal=linear | linear |  |  | spearman_then_correlation | top_k=80 | corr=0.95 | z=4 | linear | 3.401 | 4.860 | 0.519 | 3.791 | 0.490 | 5.179 | 0.281 | 0.563 | 60.556 |
| 97 | Ridge alpha=1000 \| lasso_nonzero_0.1 \| clip=none \| target=log1p | ridge | alpha=1000 |  | lasso_nonzero | alpha=0.1 | min_features=8 | none | none | 3.765 | 5.576 | 0.368 | 3.819 | 0.541 | 5.275 | 0.267 | 0.597 | 55.000 |
| 98 | PLS k=6 \| top_mutual_info_60 \| clip=z=4 \| cal=linear \| target=log1p | pls | n_components=6 |  | top_mutual_info | top_k=60 | min_features=8 | z=4 | linear | 3.408 | 4.814 | 0.526 | 3.672 | 0.524 | 5.009 | 0.325 | 0.574 | 60.000 |

## Best Validation Candidate By Model And Feature Selection

| selection_rank | candidate_short_label | model_kind | model_param_1 | model_param_2 | feature_selection_mode | feature_selection_param_1 | feature_selection_param_2 | robust_clip | calibration | mean_train_mae | mean_train_rmse | mean_train_r2 | mean_valid_mae | std_valid_mae | mean_valid_rmse | mean_valid_r2 | mean_valid_spearman | mean_selected_feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Huber alpha=30 eps=1.05 \| correlation_prune_0.9 \| clip=z=4 | huber | alpha=30 | epsilon=1.05 | correlation_prune | corr=0.9 | min_features=8 | z=4 | none | 3.157 | 5.134 | 0.464 | 3.587 | 0.505 | 4.995 | 0.336 | 0.587 | 98.222 |
| 12 | Huber alpha=100 eps=1.15 \| top_mutual_info_60 \| clip=z=4 \| target=log1p | huber | alpha=100 | epsilon=1.15 | top_mutual_info | top_k=60 | min_features=8 | z=4 | none | 3.232 | 4.845 | 0.520 | 3.610 | 0.479 | 4.944 | 0.345 | 0.573 | 60.000 |
| 25 | Huber alpha=10 eps=1.2 \| spearman_then_correlation_80_corr0.95 \| clip=z=4 | huber | alpha=10 | epsilon=1.2 | spearman_then_correlation | top_k=80 | corr=0.95 | z=4 | none | 3.233 | 4.971 | 0.497 | 3.605 | 0.454 | 4.990 | 0.332 | 0.594 | 60.556 |
| 30 | ElasticNet alpha=0.1 l1=0.1 \| top_mutual_info_60 \| clip=z=4 \| target=log1p | elastic_net | alpha=0.1 | l1_ratio=0.1 | top_mutual_info | top_k=60 | min_features=8 | z=4 | none | 3.504 | 5.002 | 0.489 | 3.651 | 0.496 | 4.976 | 0.335 | 0.584 | 60.000 |
| 44 | Huber alpha=30 eps=1.15 \| lasso_nonzero_0.03 \| clip=z=4 | huber | alpha=30 | epsilon=1.15 | lasso_nonzero | alpha=0.03 | min_features=8 | z=4 | none | 3.178 | 5.004 | 0.491 | 3.623 | 0.493 | 5.045 | 0.319 | 0.583 | 84.556 |
| 46 | ElasticNet alpha=0.03 l1=0.3 \| correlation_prune_0.9 \| clip=none \| target=log1p | elastic_net | alpha=0.03 | l1_ratio=0.3 | correlation_prune | corr=0.9 | min_features=8 | none | none | 3.243 | 4.647 | 0.558 | 3.583 | 0.475 | 4.924 | 0.347 | 0.605 | 98.222 |
| 49 | Lasso alpha=0.01 \| correlation_prune_0.9 \| clip=none \| target=log1p | lasso | alpha=0.01 |  | correlation_prune | corr=0.9 | min_features=8 | none | none | 3.260 | 4.667 | 0.554 | 3.590 | 0.478 | 4.931 | 0.346 | 0.606 | 98.222 |
| 91 | ElasticNet alpha=0.1 l1=0.5 \| none \| clip=z=4 \| target=log1p | elastic_net | alpha=0.1 | l1_ratio=0.5 | none |  |  | z=4 | none | 3.828 | 5.586 | 0.365 | 3.802 | 0.520 | 5.244 | 0.275 | 0.575 | 148.000 |
| 96 | Linear \| spearman_then_correlation_80_corr0.95 \| clip=z=4 \| cal=linear | linear |  |  | spearman_then_correlation | top_k=80 | corr=0.95 | z=4 | linear | 3.401 | 4.860 | 0.519 | 3.791 | 0.490 | 5.179 | 0.281 | 0.563 | 60.556 |
| 97 | Ridge alpha=1000 \| lasso_nonzero_0.1 \| clip=none \| target=log1p | ridge | alpha=1000 |  | lasso_nonzero | alpha=0.1 | min_features=8 | none | none | 3.765 | 5.576 | 0.368 | 3.819 | 0.541 | 5.275 | 0.267 | 0.597 | 55.000 |
| 98 | PLS k=6 \| top_mutual_info_60 \| clip=z=4 \| cal=linear \| target=log1p | pls | n_components=6 |  | top_mutual_info | top_k=60 | min_features=8 | z=4 | linear | 3.408 | 4.814 | 0.526 | 3.672 | 0.524 | 5.009 | 0.325 | 0.574 | 60.000 |
| 115 | Huber alpha=3 eps=1.05 \| top_spearman_80 \| clip=z=4 | huber | alpha=3 | epsilon=1.05 | top_spearman | top_k=80 | min_features=8 | z=4 | none | 3.051 | 4.834 | 0.524 | 3.718 | 0.460 | 5.113 | 0.293 | 0.573 | 80.000 |
| 124 | Ridge alpha=0.01 \| spearman_then_correlation_100_corr0.95 \| clip=z=5 \| cal=linear | ridge | alpha=0.01 |  | spearman_then_correlation | top_k=100 | corr=0.95 | z=5 | linear | 3.493 | 5.011 | 0.489 | 3.837 | 0.535 | 5.248 | 0.261 | 0.559 | 77.444 |
| 138 | Lasso alpha=0.003 \| spearman_then_correlation_100_corr0.95 \| clip=z=4 \| cal=linear | lasso | alpha=0.003 |  | spearman_then_correlation | top_k=100 | corr=0.95 | z=4 | linear | 3.433 | 4.914 | 0.509 | 3.824 | 0.508 | 5.224 | 0.264 | 0.555 | 77.444 |
| 142 | Linear \| lasso_nonzero_0.1 \| clip=z=5 \| cal=linear | linear |  |  | lasso_nonzero | alpha=0.1 | min_features=8 | z=5 | linear | 3.324 | 4.762 | 0.538 | 3.769 | 0.462 | 5.188 | 0.275 | 0.557 | 55.000 |
| 150 | Huber alpha=0.1 eps=1.3 \| none \| clip=none \| cal=linear \| target=log1p | huber | alpha=0.1 | epsilon=1.3 | none |  |  | none | linear | 4.188 | 6.192 | 0.220 | 4.322 | 0.641 | 6.014 | 0.052 | 0.386 | 148.000 |

## Fixed Future Holdout For Validation-Selected Finalists

| validation_selection_rank | model_kind | feature_selection_mode | robust_clip | calibration | mae | rmse | r2 | pearson | spearman | bias_pred_minus_target | selected_feature_count_final_refit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | huber | correlation_prune | z=4 | none | 5.327 | 8.825 | 0.264 | 0.603 | 0.600 | -2.778 | 100 |
| 30 | elastic_net | top_mutual_info | z=4 | none | 5.075 | 8.184 | 0.367 | 0.652 | 0.634 | -1.997 | 60 |
| 49 | lasso | correlation_prune | none | none | 5.260 | 8.604 | 0.301 | 0.604 | 0.601 | -2.498 | 100 |
| 96 | linear | spearman_then_correlation | z=4 | linear | 5.093 | 8.201 | 0.365 | 0.635 | 0.627 | -1.943 | 61 |
| 97 | ridge | lasso_nonzero | none | none | 5.421 | 8.989 | 0.237 | 0.617 | 0.590 | -2.754 | 53 |
| 98 | pls | top_mutual_info | z=4 | linear | 5.047 | 7.877 | 0.414 | 0.683 | 0.642 | -1.642 | 60 |

## Dummy Baselines

| model_kind | baseline_value | valid_mae | valid_mae_std | test_mae | test_rmse | test_r2 | test_bias_pred_minus_target |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dummy_median | 15.580 | 4.576 | 0.744 | 6.326 | 10.773 | -0.096 | -3.187 |
| dummy_mean | 16.161 | 4.602 | 0.771 | 6.198 | 10.615 | -0.064 | -2.606 |
| dummy_last | 14.380 | 5.742 | 3.538 | 6.689 | 11.187 | -0.182 | -4.387 |

## Dummy Baselines On Fixed Future Holdout

| model_kind | preselected_for_comparison | baseline_value | mae | rmse | r2 | bias_pred_minus_target |
| --- | --- | --- | --- | --- | --- | --- |
| dummy_median | true | 15.580 | 6.326 | 10.773 | -0.096 | -3.187 |
| dummy_last | false | 14.380 | 6.689 | 11.187 | -0.182 | -4.387 |
| dummy_mean | false | 16.161 | 6.198 | 10.615 | -0.064 | -2.606 |

## Conservative Read

The validation-selected rank `1` finalist improved fixed-future-holdout MAE by `0.999` points versus the preselected `dummy_median` baseline (`15.8%`).
The result should be read as evidence of modest wearable-signal association, not reliable night-level prediction. The fixed future holdout is one contiguous period, so performance can still be sensitive to nonstationarity and the single-person data context.
