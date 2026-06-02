# Monitoring EDA Summary

Stage 4 adds minute-level heart-rate and stress monitoring to the aggregate JSON case study. This report summarizes the current public EDA layer: inventory, quality, semantic-day inspection, status-aware stress states, HR zones, within-window shape, representative day traces, and pre-sleep features.

## What Minute-Level FIT Adds

- Intra-day HR/stress dynamics instead of daily summaries only.
- Sleep-aware windows rather than midnight-to-midnight grouping.
- Direct coverage, boundary, and gap diagnostics before modeling.
- Stress status semantics that separate numeric stress, unmeasurable values, and HR-confirmed active proxy minutes.
- Wake-quarter, sleep-quarter, and pre-sleep windows that define candidate predictors for the next modeling pass.

## Current Monitoring Inventory

| table | rows | columns | date_range |
| --- | --- | --- | --- |
| monitoring_heart_rate | 675325 | 3 | 2023-05-26 to 2026-05-18 |
| monitoring_stress | 889323 | 4 | 2023-05-26 to 2026-05-18 |
| semantic_sleep_windows | 556 | 15 | 2023-05-27 to 2026-05-18 |
| monitoring_quality_index | 589 | 88 | 2023-05-27 to 2026-05-18 |
| monitoring_features_core_v0 | 589 | 93 | 2023-05-27 to 2026-05-18 |
| monitoring_features_full_v0 | 589 | 243 | 2023-05-27 to 2026-05-18 |

## Quality Funnel

| step | rows | share_of_analysis_rows |
| --- | --- | --- |
| Observed semantic sleep windows | 556 |  |
| Analysis windows after boundary policy | 589 | 1.000 |
| Rows with observed next sleep boundary | 524 | 0.890 |
| Rows plausible under sleep/wake duration bounds | 524 | 0.890 |
| Rows usable for sleep and wake HR/stress | 481 | 0.817 |
| Rows eligible for recovery modeling v0 | 472 | 0.801 |

## Quality Over Time

Quality is uneven over calendar time, which is why downstream modeling keeps a future holdout while using past-random train/validation splits for the earlier history. Recent months include usable observed windows as well as a small number of synthetic or unsupported boundary cases.

| month | analysis_rows | eligible_rows | synthetic_split | unsupported_multi_day_gap | eligible_rate |
| --- | --- | --- | --- | --- | --- |
| 2025-10-01 00:00:00 | 23 | 20 | 2 | 1 | 0.870 |
| 2025-11-01 00:00:00 | 21 | 14 | 5 | 1 | 0.667 |
| 2025-12-01 00:00:00 | 6 | 3 | 1 | 2 | 0.500 |
| 2026-01-01 00:00:00 | 31 | 26 | 4 | 0 | 0.839 |
| 2026-02-01 00:00:00 | 28 | 23 | 4 | 0 | 0.821 |
| 2026-03-01 00:00:00 | 31 | 21 | 8 | 0 | 0.677 |
| 2026-04-01 00:00:00 | 25 | 18 | 4 | 2 | 0.720 |
| 2026-05-01 00:00:00 | 12 | 6 | 2 | 2 | 0.500 |

## Coverage Diagnostics

| phase | signal | metric | count | median | p10 | p90 |
| --- | --- | --- | --- | --- | --- | --- |
| sleep | HR | Sleep HR | 556 | 0.695 | 0.618 | 0.752 |
| sleep | stress | Sleep stress | 556 | 0.975 | 0.906 | 0.998 |
| wake | HR | Wake HR | 557 | 0.875 | 0.611 | 0.903 |
| wake | stress | Wake stress | 557 | 0.916 | 0.655 | 0.962 |

## Monitoring Day Browser

The selected browser window is `2026-02-10_0479_observed` on `2026-02-10`. It exposes the sleep start, wake start, and wake end boundaries, the HR trace, valid numeric stress points, and status-value intervals that daily aggregate JSON cannot show.

A compact representative-day gallery also keeps several regimes visible without editing notebook constants:

| gallery_label | calendarDate | analysis_window_id | boundary_confidence | modeling_recovery_v0_eligible | coverage_score | largest_gap_minutes |
| --- | --- | --- | --- | --- | --- | --- |
| high_quality_reference | 2026-02-15 00:00:00 | 2026-02-15_0483_observed | observed | 1 | 0.915 | 8.000 |
| high_wake_load | 2023-11-04 00:00:00 | 2023-11-04_0148_observed | observed | 1 | 0.840 | 18.000 |
| imperfect_gap_or_boundary | 2023-09-06 00:00:00 | 2023-09-06_0095_split_a | synthetic_split | 0 | 0.897 | 13.000 |

## Stress States And HR Zones

Wake stress-state composition among recovery-eligible windows:

| state | mean_fraction | median_fraction | p25 | p75 |
| --- | --- | --- | --- | --- |
| resting | 0.119 | 0.087 | 0.034 | 0.176 |
| low | 0.222 | 0.219 | 0.142 | 0.302 |
| medium | 0.235 | 0.229 | 0.176 | 0.284 |
| high | 0.227 | 0.208 | 0.118 | 0.311 |
| active | 0.196 | 0.188 | 0.136 | 0.240 |

Wake HR-zone composition among recovery-eligible windows:

| zone | mean_fraction | median_fraction |
| --- | --- | --- |
| below zone1 | 0.860 | 0.882 |
| zone1 | 0.110 | 0.091 |
| zone2 | 0.023 | 0.014 |
| zone3 | 0.005 | 0.001 |
| zone4 | 0.001 | 0.000 |
| zone5 | 0.000 | 0.000 |
| above mhr | 0.000 | 0.000 |

## Within-Window Shape

Wake quarters summarize daytime shape among recovery-eligible rows. Sleep quarters use plausible rows with usable sleep HR and stress, and remain descriptive EDA features rather than sleep-stage detection.

Wake quarters:

| quarter | signal | rows | mean_value | median_value | p25 | p75 |
| --- | --- | --- | --- | --- | --- | --- |
| Q1 | Heart rate | 472 | 79.528 | 78.245 | 72.165 | 86.261 |
| Q1 | Stress | 472 | 56.885 | 56.755 | 45.709 | 68.285 |
| Q2 | Heart rate | 472 | 79.192 | 78.492 | 71.102 | 87.125 |
| Q2 | Stress | 470 | 58.454 | 59.055 | 45.593 | 72.766 |
| Q3 | Heart rate | 472 | 79.120 | 78.954 | 70.597 | 86.642 |
| Q3 | Stress | 472 | 61.379 | 63.145 | 48.254 | 75.025 |
| Q4 | Heart rate | 472 | 73.260 | 72.522 | 66.782 | 78.963 |
| Q4 | Stress | 472 | 52.210 | 51.843 | 39.925 | 64.428 |

Sleep quarters:

| quarter | signal | rows | mean_value | median_value | p25 | p75 |
| --- | --- | --- | --- | --- | --- | --- |
| Q1 | Heart rate | 520 | 54.652 | 53.822 | 50.593 | 58.014 |
| Q1 | Stress | 520 | 20.049 | 17.960 | 13.362 | 25.086 |
| Q2 | Heart rate | 520 | 51.683 | 51.208 | 48.321 | 54.093 |
| Q2 | Stress | 520 | 14.671 | 13.563 | 8.604 | 18.679 |
| Q3 | Heart rate | 520 | 50.403 | 49.800 | 47.581 | 52.358 |
| Q3 | Stress | 520 | 12.133 | 10.660 | 7.510 | 15.207 |
| Q4 | Heart rate | 520 | 50.530 | 49.912 | 48.087 | 52.517 |
| Q4 | Stress | 520 | 11.872 | 10.903 | 7.862 | 14.776 |

Wake local-time point distribution:

The local-time profile uses all recovery-eligible wake minute points and anchors after-midnight values as 24+ so the late-wake period remains visually continuous.

| signal | points | windows | median_value |
| --- | --- | --- | --- |
| Heart rate | 378828 | 472 | 76.000 |
| Stress | 319529 | 472 | 58.000 |

Wake phase-fraction point distribution:

The normalized wake-phase profile uses the same recovery-eligible minute points, but maps each wake window to `0..1`. This separates a relative late-wake effect from a strict local-clock-time effect.

Wake stress distribution by normalized quarter:

Density-normalized stress histograms split the same wake points into four normalized wake quarters, which makes changes in distribution shape visible beyond the median line.

## Pre-Sleep Window

| metric | value |
| --- | --- |
| eligible rows | 472.000 |
| pre_sleep_4h_usable rows | 464.000 |
| pre_sleep_4h_hr_mean | 72.907 |
| pre_sleep_4h_stress_mean | 52.077 |
| pre_sleep_4h_hr_early_minus_late | 9.051 |
| pre_sleep_4h_stress_early_minus_late | 17.754 |

## Feature Readiness For Modeling

| feature_table | rows | columns |
| --- | --- | --- |
| core v0 | 589 | 93 |
| full v0 | 589 | 243 |

Full feature catalog family counts:

| family | columns |
| --- | --- |
| distribution/shape | 60 |
| relative windows | 56 |
| episodes/state structure | 35 |
| variability/gaps | 20 |
| HR MHR zones | 14 |
| recovery/deactivation | 14 |
| HR/stress coupling | 12 |
| trends | 12 |
| stress state fractions | 10 |
| sleep-wake contrast | 8 |
| identity/window metadata | 2 |

## Interpretation

- The monitoring layer is useful because it makes within-day physiology and missingness visible, not because it proves a prediction claim.
- Quality filtering removes a meaningful number of windows before modeling, especially when wake boundaries or whole-wake coverage are weak.
- Active/status proxy stress minutes are analytically different from numeric high-stress minutes and are kept separate.
- Wake-quarter, sleep-quarter, gallery day-browser, and pre-sleep features provide the most direct EDA bridge into future sleep-outcome modeling.
- The layer remains single-subject observational wearable data and should be interpreted as a quality-aware baseline.

## Figure References

- `docs/img/monitoring_example_day.png`
- `docs/img/monitoring_day_gallery.png`
- `docs/img/monitoring_within_day_shape.png`
- `docs/img/monitoring_wake_local_time_distribution.png`
- `docs/img/monitoring_wake_phase_fraction_distribution.png`
- `docs/img/monitoring_wake_stress_quarter_distribution.png`

## Links

- [Notebook 07: monitoring FIT EDA](../notebooks/07_monitoring_fit_eda.ipynb)
- [Stage 4 monitoring docs](../docs/stage4_monitoring.md)
