# Stage 4 Sleep Stress Linear Models

This report evaluates linear-family regression models for next-sleep average stress using the Stage 4 `day D -> next sleep` modeling frame. It is an exploratory single-subject modeling pass, not a production predictor or health recommendation.

## Modeling Setup

- Target: `target_avgSleepStress_next_sleep`
- Feature set: `monitoring_full_wake_pre_sleep`
- Candidate features: `123`
- Split strategy: `split_past_random_valid_future_test`; the final future block stayed untouched during tuning
- Tuning: `3` repeated train/validation holdouts inside the pre-test history
- Tuning metric: `mae`
- Expanded grid: `70,056` linear-family configurations from the notebook control panel
- Finalists: `50` validation-selected candidates refit on all pre-test rows before future-test evaluation
- Dummy baselines: `dummy_mean`, `dummy_median`, `dummy_last`

The notebook preserves outputs from the expanded run. Its visible rerun defaults are set to the `smoke` preset with a safety gate, so a fresh end-to-end run is intentionally much smaller unless the expanded control-panel grid is explicitly enabled.

Preprocessing is fit inside each training split: numeric median imputation, optional train-fitted z clipping, standardization, and categorical one-hot encoding when categorical predictors are present. Feature selection and optional linear calibration are also fit without using validation or test target values; calibration uses out-of-fold pre-test predictions.

Model selection is based on repeated-holdout validation only. The future test block is used once for evaluation of validation-selected finalists after refitting on all pre-test rows. Any future-test ordering among finalists is diagnostic only, not a tuning rule.

## Headline Result

The validation rank-1 model was `Huber alpha=30 eps=1.15 \| top_spearman_90 \| clip=z=4 \| cal=linear`. It reached mean validation MAE `3.610` and future-test MAE `5.336`.

The best future-test dummy baseline was `dummy_mean` with MAE `6.198`. The validation-selected rank-1 model improved future-test MAE by `0.863` points (`13.9%`) versus that dummy.

## Validation Leaders

| selection_rank | candidate_short_label | model_kind | feature_selection_mode | robust_clip | calibration | mean_valid_mae | std_valid_mae | mean_valid_r2 | mean_valid_spearman | future_test_mae | future_test_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.000 | Huber alpha=30 eps=1.15 \| top_spearman_90 \| clip=z=4 \| cal=linear | huber | top_spearman | z=4 | linear | 3.610 | 0.395 | 0.350 | 0.581 | 5.336 | 0.279 |
| 2.000 | Huber alpha=30 eps=1.15 \| top_spearman_90 \| clip=z=5 \| cal=linear | huber | top_spearman | z=5 | linear | 3.611 | 0.402 | 0.348 | 0.581 | 5.342 | 0.292 |
| 3.000 | Huber alpha=30 eps=1.1 \| top_spearman_90 \| clip=z=4 \| cal=linear | huber | top_spearman | z=4 | linear | 3.612 | 0.399 | 0.349 | 0.578 | 5.320 | 0.283 |
| 4.000 | Huber alpha=30 eps=1.15 \| spearman_then_correlation_90_corr0.99 \| clip=z=4 \| cal=linear | huber | spearman_then_correlation | z=4 | linear | 3.613 | 0.385 | 0.351 | 0.579 | 5.318 | 0.283 |
| 5.000 | Huber alpha=10 eps=1.15 \| spearman_then_correlation_90_corr0.99 \| clip=z=4 | huber | spearman_then_correlation | z=4 | none | 3.616 | 0.424 | 0.341 | 0.577 | 5.276 | 0.244 |
| 6.000 | Huber alpha=30 eps=1.15 \| spearman_then_correlation_90_corr0.99 \| clip=z=5 \| cal=linear | huber | spearman_then_correlation | z=5 | linear | 3.616 | 0.394 | 0.349 | 0.580 | 5.322 | 0.294 |
| 7.000 | Huber alpha=30 eps=1.1 \| top_spearman_90 \| clip=z=5 \| cal=linear | huber | top_spearman | z=5 | linear | 3.616 | 0.402 | 0.347 | 0.578 | 5.323 | 0.295 |
| 8.000 | Huber alpha=30 eps=1.1 \| spearman_then_correlation_90_corr0.99 \| clip=z=4 \| cal=linear | huber | spearman_then_correlation | z=4 | linear | 3.616 | 0.390 | 0.350 | 0.578 | 5.301 | 0.287 |
| 9.000 | Huber alpha=10 eps=1.2 \| spearman_then_correlation_90_corr0.95 \| clip=z=4 | huber | spearman_then_correlation | z=4 | none | 3.617 | 0.405 | 0.344 | 0.581 | 5.297 | 0.242 |
| 10.000 | Huber alpha=10 eps=1.1 \| spearman_then_correlation_90_corr0.99 \| clip=none | huber | spearman_then_correlation | none | none | 3.618 | 0.438 | 0.338 | 0.577 | 5.287 | 0.281 |

## Best Validation Candidate By Model Family

This compact view keeps one validation-ranked candidate per model family plus dummy baselines. Future-test metrics are shown only where they already exist for validation-selected finalists or dummies; missing future-test values were not backfilled.

| candidate_type | model_kind | candidate_short_label | feature_selection_mode | robust_clip | calibration | mean_valid_mae | std_valid_mae | mean_valid_r2 | mean_valid_spearman | future_test_mae | future_test_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| linear_family | huber | Huber alpha=30 eps=1.15 \| top_spearman_90 \| clip=z=4 \| cal=linear | top_spearman | z=4 | linear | 3.610 | 0.395 | 0.350 | 0.581 | 5.336 | 0.279 |
| linear_family | ridge | Ridge alpha=300 \| top_spearman_90 \| clip=z=4 | top_spearman | z=4 | none | 3.725 | 0.344 | 0.339 | 0.572 |  |  |
| linear_family | elastic_net | ElasticNet alpha=1 l1=0.01 \| top_spearman_90 \| clip=z=4 \| cal=linear | top_spearman | z=4 | linear | 3.728 | 0.339 | 0.337 | 0.574 |  |  |
| linear_family | pls | PLS k=2 \| lasso_nonzero_0.1 \| clip=z=4 \| cal=linear | lasso_nonzero | z=4 | linear | 3.733 | 0.310 | 0.333 | 0.564 |  |  |
| linear_family | lasso | Lasso alpha=1 \| spearman_then_correlation_60_corr0.9 \| clip=z=4 \| cal=linear | spearman_then_correlation | z=4 | linear | 3.764 | 0.281 | 0.306 | 0.555 |  |  |
| linear_family | linear | Linear \| spearman_then_correlation_60_corr0.9 \| clip=none \| cal=linear | spearman_then_correlation | none | linear | 3.872 | 0.364 | 0.274 | 0.527 |  |  |
| dummy | dummy_last | dummy_last | none | none | none | 4.644 | 0.519 | -0.042 |  | 6.689 | -0.182 |
| dummy | dummy_median | dummy_median | none | none | none | 4.665 | 0.520 | -0.009 |  | 6.326 | -0.096 |
| dummy | dummy_mean | dummy_mean | none | none | none | 4.734 | 0.492 | -0.021 |  | 6.198 | -0.064 |

## Rank-1 Feature Diagnostics

The rank-1 feature-importance artifact combines final-refit standardized coefficients with validation permutation importance. Coefficients are fit on pre-test history; permutation importance is fit on train rows and evaluated on validation rows, not the future test block.

| rank | feature | standardized_coefficient | abs_standardized_coefficient | permutation_mae_increase_mean | permutation_mae_increase_std |
| --- | --- | --- | --- | --- | --- |
| 1 | wake_frac_hr_zone2_plus_stress_high | 0.704 | 0.704 | 0.219 | 0.083 |
| 2 | pre_sleep_4h_stress_mean | 0.485 | 0.485 | 0.142 | 0.078 |
| 3 | wake_stress_slope_per_hour | 0.469 | 0.469 | 0.128 | 0.058 |
| 4 | pre_sleep_4h_hr_std | -0.314 | 0.314 | 0.106 | 0.055 |
| 5 | wake_q4_stress_mean | 0.454 | 0.454 | 0.092 | 0.064 |
| 6 | wake_hr_std_diff | -0.299 | 0.299 | 0.059 | 0.030 |
| 7 | wake_hr_mad | -0.302 | 0.302 | 0.052 | 0.021 |
| 8 | pre_sleep_4h_stress_p90 | 0.370 | 0.370 | 0.051 | 0.038 |
| 9 | pre_sleep_4h_stress_slope_per_hour | 0.349 | 0.349 | 0.051 | 0.046 |
| 10 | wake_q1_stress_std | -0.468 | 0.468 | 0.044 | 0.049 |
| 11 | wake_q4_stress_p90 | 0.283 | 0.283 | 0.044 | 0.047 |
| 12 | wake_hr_roughness | -0.308 | 0.308 | 0.041 | 0.024 |

See `docs/img/stage4_linear_feature_importance.png` and `reports/stage4_sleep_stress_linear_rank1_feature_importance.csv` for the full top-N diagnostic.

## Conservative Read

The expanded grid suggests a modest but real linear signal for next-sleep stress. Huber-style robust regression was the strongest validation baseline, and feature-selection, clipping, and calibration choices changed results enough to justify explicit tuning.

The future block still shows drift and extreme-night underprediction, so this should not be read as reliable night-level prediction. The feature-importance view is dominated by recent wake and pre-sleep stress plus heart-rate variability features, which is plausible but not causal evidence.

The next modeling family should be tree ensembles because the linear models may be compressing nonlinear or threshold-like physiology patterns that appear in the residual diagnostics.

## Public Artifacts

- `notebooks/09_sleep_stress_linear_models.ipynb`
- `reports/stage4_sleep_stress_linear_model_grid.csv`
- `reports/stage4_sleep_stress_linear_model_leaderboard.csv`
- `reports/stage4_sleep_stress_linear_best_by_model_family.csv`
- `reports/stage4_sleep_stress_linear_rank1_feature_importance.csv`
- `docs/img/stage4_linear_prediction_diagnostics.png`
- `docs/img/stage4_linear_feature_importance.png`
