# Case Study: Privacy-First Garmin Wearable Analytics

## Executive Summary

This project turns local Garmin wearable exports into a privacy-safe analytics workflow that is strong enough to use as a DS/DA portfolio case study. The raw source data is messy: nested JSON, FIT monitoring files, changing coverage over time, and model-derived device metrics that can be informative but are not always trustworthy at face value. To make the data usable, the project builds an end-to-end workflow: discover raw files, ingest them into parquet checkpoints, sanitize sensitive fields, generate a data dictionary, label day-level quality, and only then move into exploratory analysis and modeling. The public story now spans aggregate EDA, Stage 3 day-level validation/modeling, and a Stage 4 minute-level HR/stress monitoring layer that feeds a leakage-aware next-sleep modeling frame. The Stage 4 linear-family regression pass predicts next-sleep `avgSleepStress` with a temporal-validation-selected Huber model, improving fixed-future-holdout MAE by **15.8%** versus a baseline selected before future evaluation. The result is a repo that demonstrates not only plotting ability, but also data hygiene, quality-aware analysis, careful interpretation of observational signals, multi-resolution feature engineering, and honest time-aware modeling.

## Problem Framing

Personal wearable exports are not analysis-ready. They are nested, schema-heavy, and contain a mixture of direct measurements, inferred scores, partial-day records, and genuine no-wear gaps. On top of that, the data is privacy-sensitive, which means a shareable project cannot simply expose raw exports and hope the analysis looks polished afterward.

This project addresses that workflow end-to-end. Instead of treating notebooks as the only product, it treats analytics as a layered system: ingestion, privacy boundary, quality checks, and then interpretation. That framing is what makes the repo useful as a portfolio artifact for balanced DS/DA roles.

In practical terms, the project had to solve four non-trivial problems before any findings were worth looking at:
- flatten two different Garmin export families into one day-level analysis table
- keep the shareable boundary privacy-safe
- distinguish real behavior from no-wear / charging / partial-day artifacts
- avoid telling causal stories from noisy observational device summaries

## Data and Privacy Constraints

The source data comes from two Garmin export families stored locally under `data/raw/DI_CONNECT`:
- UDS aggregator exports with day-level nested wellness/activity summaries
- sleep export files with nightly sleep and respiration information
- FIT monitoring files with minute-level heart-rate and stress observations

Those raw files are never part of the public-facing project story. The pipeline converts them into day-level parquet outputs and then applies a sanitize step to remove or suppress fields that are sensitive or analytically irrelevant. The sanitized outputs become the default boundary for analysis, sharing, and documentation. This is a deliberate design choice: the project demonstrates not just analysis skill, but disciplined handling of personal data.

## Pipeline Overview

```mermaid
flowchart LR
    A["Raw Garmin exports"] --> B["Discover + inventory"]
    B --> C["Ingest UDS + sleep JSON"]
    C --> D["Build day-level parquet tables"]
    D --> E["Sanitize sensitive fields"]
    E --> F["Data dictionary + quality labels"]
    F --> G["EDA notebooks"]
    G --> H["Stage 3 validation + modeling"]
    D --> I["Stage 4 FIT monitoring extension"]
    I --> J["Monitoring quality + feature tables"]
    J --> L["Stage 4 modeling frame"]
    L --> M["Linear-family regression"]
    H --> K["Curated findings + case study"]
    M --> K
```

Core project stages:
- **Stage 0**: discover raw files, ingest nested JSON, build canonical parquet datasets
- **Stage 1**: sanitize outputs, generate a data dictionary, and label day-level quality
- **Stage 2**: run notebook-based EDA with explicit quality-aware analysis slices
- **Stage 3**: validate and model `day D -> next-night` sleep outcomes with compact scikit-learn baselines
- **Stage 4**: decode minute-level FIT monitoring records into sleep-aware HR/stress quality and feature tables, then evaluate a first linear-family next-sleep stress regression pass

This matters because the repo is not just about “making charts”; it shows a complete local analytics workflow that can absorb imperfect personal data without pretending the imperfections do not exist.

## Quality and Trustworthiness

The analysis-ready dataset contains **677 daily rows** spanning **2023-05-26 to 2026-05-18**. Quality is not treated as an afterthought. Instead, each day is labeled under strict and loose readiness rules based on the availability of core signals such as steps, heart rate, stress duration, sleep coverage, and Body Battery end-of-day values.

Headline quality numbers:
- **Strict good**: `617 / 677` days (`91.14%`)
- **Strict partial**: `25 / 677` days (`3.69%`)
- **Strict bad**: `35 / 677` days (`5.17%`)
- **Corrupted stress-only days**: `21` dates (`3.10%`)

These labels are important because they separate genuine behavioral patterns from device artifacts. For example, some suspicious dates are truly corrupted stress-only runs, while others are partial but still plausible days where the watch likely ran out of battery before end-of-day.

![Coverage calendar](img/stage2_quality_calendar_github_style.png)

*Coverage calendar: long dark spans reflect no-wear or no corroborating-signal periods, while orange/red clusters mark partial or bad-quality days that should not be interpreted like ordinary behavior.*

## Key Analytical Findings

### Behavioral Rhythms

The day-of-week segmentation shows that the dataset contains stable routines rather than pure noise. Saturday is the most active day in the strict-quality slice, with a median of about **7,555 steps**, while Sunday drops to roughly **2,085 steps**. This pattern is mirrored by `active_hours`, which peaks on Saturday and is lowest on Sunday. That consistency matters because it shows the signal is not just a quirk of one metric.

![Median steps by weekday](img/steps_by_weekday.png)

*Behavioral rhythm: median steps are highest on Saturday and lowest on Sunday, showing a stable weekly routine rather than random activity variation.*

Stress also has a weekly rhythm. Tuesday has the highest median awake stress in the strict-quality slice, at roughly **58.5**, which is above the calmer weekdays. This is a useful validation that the project can recover interpretable weekly structure from noisy wearable summaries rather than only producing generic distributions.

![Awake stress by weekday](img/seg_dow_awake_stress_box.png)

*Weekday stress segmentation: Tuesday stands out as the highest-stress weekday, while the overall weekly profile remains stable enough to interpret.*

### Sleep Quality Structure

Sleep quality is structured by both **duration** and **timing**. Duration does not improve score monotonically: the strongest nights cluster in a broad middle band rather than at the longest durations. Timing matters too: later sleep onset is associated with weaker scores even after handling the midnight wrap correctly. Taken together, these two plots are more informative than either one alone, because they show that Garmin sleep score is not just a proxy for “more hours is better”.

<table>
  <tr>
    <td><img src="img/rel_sleep_hours_vs_sleep_score_same_row.png" alt="Sleep hours versus sleep score" width="100%"></td>
    <td><img src="img/rel_sleep_start_hour_local_wrapped_vs_sleep_score.png" alt="Sleep start hour versus sleep score" width="100%"></td>
  </tr>
  <tr>
    <td><em>Sleep duration effect: the best nights cluster around a middle duration band, and the score drops away from that range rather than increasing indefinitely.</em></td>
    <td><em>Sleep timing effect: later sleep onset is associated with weaker Garmin sleep scores after midnight wrap is handled correctly.</em></td>
  </tr>
</table>

The segmented sleep buckets tell the same story from a different angle. Median sleep duration rises from roughly **6.3 hours** in poor-quality nights to about **8.9 hours** in excellent nights, which shows that duration matters, but only within a plausible range rather than at the extreme long end.

![Sleep duration by quality bucket](img/seg_sleep_bucket_sleep_hours_box.png)

*Sleep quality buckets: better-scoring nights are clearly longer on average, but the relationship is structured rather than linear.*

Sleep stress is another strong driver. `sleepAverageStressLevel` is negatively associated with `sleepOverallScore` with a Pearson correlation of about **-0.64**, making it one of the clearest degraders of sleep quality in the whole project. This relationship is stronger and cleaner than many of the daytime activity effects.

![Sleep stress vs sleep score](img/rel_sleep_avg_stress_level_vs_sleep_score.png)

*Sleep stress is one of the clearest score degraders: higher average asleep stress is associated with substantially worse sleep scores.*

### Day-to-Night Carryover

The most important directional relationship in the project is a carryover effect from daytime stress into the following night. `awakeAverageStressLevel (D)` is negatively associated with `next-night sleepRecoveryScore (D+1)` (Pearson about **-0.34**, Spearman about **-0.32**, `n=543`). The broader pattern is not just about the average stress level either: days with a larger high-stress share tend to precede worse next-night recovery, while days with a larger rest share tend to precede better recovery.

![Daytime stress vs next-night recovery](img/awake_stress_to_nextsleep_recovery.png)

*Day-to-night carryover: higher daytime stress is associated with weaker next-night recovery, making this one of the clearest directional findings in the repository.*

The same carryover appears in the next-night asleep stress signal. `awakeAverageStressLevel (D)` is positively associated with `sleepAverageStressLevel (D+1)` with a Pearson correlation of about **+0.31** (`n=529`). This is weaker than the recovery effect, but it supports the same interpretation: stress does not stay confined to the calendar day where it was recorded.

![Daytime stress vs next-night asleep stress](img/rel_awake_stress_to_nextsleep_asleep_stress.png)

*Stress carryover: days with higher awake stress tend to be followed by nights with higher asleep stress as well.*

The composition of the day matters too. A larger `awakeRestShare` tends to precede better recovery, which is useful because it moves the analysis beyond one average stress metric and toward a more interpretable “stress vs recovery balance” framing.

![Rest share vs next-night recovery](img/rel_awake_rest_share_to_nextsleep_recovery.png)

*Stress composition matters: days with a larger rest share tend to be followed by stronger next-night recovery.*

There are also smaller but still interesting secondary effects. Very high-intensity activity is associated with shorter next-night REM duration, while total daily steps have much weaker and less intuitive next-night effects. That distinction is useful because it suggests ordinary movement and high-intensity load should not be treated as interchangeable. Another small but interpretable same-day pattern is that longer sleep is followed by fewer active hours, which is a reminder that some relationships in wearable data reflect time-budget tradeoffs rather than “better” or “worse” behavior in the abstract.

## Stage 3 Modeling Result

The strongest Stage 2 directional finding was that higher daytime stress tends to precede weaker next-night recovery. Stage 3 turns that into a compact predictive task rather than leaving it as a visual observation only.

The current headline modeling task is:
- predict whether `next-night sleepRecoveryScore < 75`

This threshold is intentionally a compromise. A stricter cutoff like `< 70` makes the positive class too rare for a clean baseline story, while a median-style split near `79/80` loses too much of the “bad night” interpretation. With the current time-ordered `60/20/20` split, `< 75` produces a usable but still meaningfully adverse class.

The best interpretable models are sparse logistic variants built on a very small set of daytime features. In the refreshed run, the selected sparse L1 model uses:
- `awakeAverageStressLevel`
- `restingHeartRate`

On the current test split, this classifier lands around:
- balanced accuracy: **~0.68**
- ROC-AUC: **~0.71**
- PR-AUC: **~0.60**
- F1: **~0.62**

This is not a strong production predictor, but it is a real predictive signal on noisy single-subject wearable data. The practical interpretation is that daytime signals can act as a moderate **risk flag** for poor next-night recovery, even if they are not precise enough to support exact score prediction.

The refreshed nonlinear benchmarks are useful checks, but they no longer beat the selected sparse classifier on the headline test metrics. That keeps the modeling story simpler: the most defensible public result is also the most interpretable one.

Just as importantly, Stage 3 keeps a limited result instead of overstating it: current day-level awake aggregates show only weak numeric regression value. Tree models produce small positive `R^2` for `avgSleepStress` and `sleepRecoveryScore`, while other score targets remain near or below a simple median baseline. That is analytically useful because it draws a clear boundary between coarse risk classification and exact score prediction.

Stage 3 also adds a lightweight validation layer for the claims that matter most to the public narrative. Three of the strongest observational findings hold up under simple statistical checks: Saturday activity is significantly higher than Sunday activity, higher daytime awake stress is associated with lower next-night recovery, and higher daytime awake stress is also associated with higher next-night sleep stress. A fourth descriptive observation, that Tuesday is the highest-stress weekday, remains weaker and is better treated as an exploratory weekly-rhythm note than as a validated headline result.

## Stage 4 Monitoring and Modeling

The Stage 4 extension changes the project from a purely day-level JSON case study into a multi-resolution wearable analytics pipeline.

The monitoring extension decodes Garmin FIT monitoring files into minute-level heart-rate and stress tables, then aligns those records to semantic sleep/wake windows instead of midnight-to-midnight calendar days. The current refreshed run decoded **3,562** monitoring FIT files, producing **675,325** heart-rate rows and **889,323** stress rows.

The important design choice is separation of concerns:
- `monitoring_quality_index.parquet` holds row-level plausibility, coverage, gap, boundary, and recovery-eligibility flags
- `monitoring_features_core_v0.parquet` is a compact `589 x 93` starter feature table
- `monitoring_features_full_v0.parquet` is a cleaned `589 x 243` feature table with a catalog for leakage-aware feature selection
- `stage4_sleep_modeling_frame.parquet` aligns day-D monitoring and aggregate context with next-sleep targets
- `stage4_sleep_stress_linear_models_summary.md` reports the first validation-selected linear-family next-sleep stress result

Stress status values are handled explicitly. Raw `0..100` values are numeric Garmin stress readings, raw `-1` is an unmeasurable/status value, and raw `-2` is only treated as an active/large-motion proxy when the same minute also has valid heart rate.

The public analytical layer now adds three Stage 4 notebooks. Notebook 07 shows what the minute-level layer contributes beyond daily aggregates: coverage diagnostics, stress-state composition, HR zones, within-day shape, and pre-sleep context. Notebook 08 checks target alignment, eligibility, split policy, and feature-set definitions. Notebook 09 runs a configurable linear-family regression pass for next-sleep average stress with a two-stage mixed-validation protocol inside the development history.

The Stage 4 linear pass uses `target_avgSleepStress_next_sleep` and the `monitoring_full_wake_pre_sleep_plus_state` feature set, which has **148** candidate features. Beyond current wake and pre-sleep physiology, it adds previous-sleep context, prior-observation history, and current-day deviations from recent personal baselines.

A compact feature-set screen also checks aggregate-only, monitoring-core, monitoring-full, previous-sleep, history, state, and wider combined alternatives. The state-context set is retained because it improves validation behavior without requiring the widest **180-feature** state-plus-aggregate candidate pool.

The first stage screens **52,812** configurations on `3` random plus `3` expanding-temporal holdouts. A representative **150-candidate** shortlist is then reranked on `10` random plus `8` temporal holdouts before any finalist is evaluated on the fixed future block. The definitive validation-selected rank-1 model is:

`Huber alpha=30 eps=1.05 | correlation_prune_0.9 | clip=z=4`

On the fixed future block, that model reaches MAE **5.327** and R2 **0.264**. The comparison baseline is fixed as `dummy_median` before future evaluation; it reaches MAE **6.326**. The selected Huber model therefore improves MAE by **0.999** points, or **15.8%**. The absolute predictive gain over the earlier Stage 4 run is small, but the selection protocol is substantially more defensible.

![Stage 4 linear prediction diagnostics](img/stage4_linear_prediction_diagnostics.png)

*Stage 4 linear diagnostics: the future block shows useful signal versus a dummy baseline, but residual drift and high-stress-night underprediction are still visible.*

![Stage 4 linear feature importance](img/stage4_linear_feature_importance.png)

*Rank-1 feature diagnostics: recent wake and pre-sleep stress remain important, while deviations from recent personal stress baselines add useful state context. These are associations, not causal or clinical evidence.*

The result is best read as methodological progress, not as a production predictor. It shows that minute-level wearable signals can be transformed into a quality-aware modeling frame and evaluated honestly against simple baselines on a future holdout. It does not support medical decision-making, precise night-level prediction, or causal claims.

## What This Demonstrates as a DS/DA Project

This repo demonstrates more than one skill category:
- **Raw data wrangling**: nested JSON exports are flattened into consistent day-level tables
- **Schema handling**: sleep and UDS records are integrated without losing traceability of important fields
- **Multi-resolution data design**: aggregate JSON metrics and minute-level FIT monitoring are kept as linked but distinct analytical layers
- **Privacy-aware preprocessing**: sanitize is treated as a first-class stage, not as a cosmetic cleanup
- **Quality-rule design**: strict and loose readiness labels make downstream analysis more defensible
- **EDA structuring**: the analysis is split into coverage, time series, distributions/segmentation, and relationships rather than dumped into one notebook
- **Time-aware modeling**: a compact Stage 3 modeling layer evaluates predictive tasks with contiguous train/validation/test splits rather than random shuffling
- **Leakage-aware target alignment**: Stage 4 aligns day-D monitoring windows to exact next-sleep targets and keeps sleep-phase predictors out of the default feature sets
- **Validation-selected model tuning**: the Stage 4 linear pass combines random and expanding-temporal holdouts, reranks a representative shortlist, freezes finalists, and only then evaluates them on a fixed future block
- **Feature selection and honest benchmarking**: sparse models, linear-family grids, dummy baselines, nonlinear checks, and negative results are all kept in view
- **Future-holdout evaluation**: the public modeling results separate development-history tuning from a fixed future readout and call out drift when it appears
- **Interpretation discipline**: findings are framed as observational and cross-checked with artifact review
- **Reproducible repo organization**: CLI, tests, docs, and notebooks fit together as one workflow

That combination is exactly why the project is useful as a balanced DS/DA portfolio piece. It shows analytical judgment and data engineering maturity in the same artifact.

## Limitations

This is still a single-subject observational dataset. The metrics are wearable-derived and partly model-based, not diagnostic measurements. Coverage gaps, charging periods, and off-wrist artifacts can still shape some day-level aggregates even after quality filtering. The Stage 4 linear model is modest and still shows residual drift plus underprediction of extreme high-stress nights. The findings are therefore useful as disciplined observational insights and modeling baselines, not as causal, clinical, or treatment claims.

## Where to Go Deeper

- [Notebook 02: curated time series](../notebooks/02_eda_timeseries.ipynb)
- [Notebook 03: distributions + segmentation](../notebooks/03_eda_distributions.ipynb)
- [Notebook 04: relationships + artifact review](../notebooks/04_eda_relationships.ipynb)
- [Notebook 05: Stage 3 modeling baseline](../notebooks/05_modeling_recovery.ipynb)
- [Notebook 07: monitoring FIT EDA](../notebooks/07_monitoring_fit_eda.ipynb)
- [Notebook 08: sleep outcome modeling frame](../notebooks/08_sleep_outcome_modeling_frame.ipynb)
- [Notebook 09: sleep stress linear models](../notebooks/09_sleep_stress_linear_models.ipynb)
- [Pipeline overview](pipeline.md)
- [Stage 1: sanitize, data dictionary, quality](stage1.md)
- [Stage 2: EDA details](stage2.md)
- [Stage 3: validation and modeling](stage3.md)
- [Stage 4: FIT monitoring extension](stage4_monitoring.md)
