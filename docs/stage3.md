# Stage 3 — Validation and Modeling

Stage 3 extends the EDA-driven findings from [Stage 2](stage2.md) into explicit validation and prediction tasks.
The current focus is narrow on purpose: test whether `day D` awake signals contain usable information about `next-night` sleep outcomes, and keep the modeling story interpretable.

Primary evidence notebook:
- `notebooks/05_modeling_recovery.ipynb`

## Current Scope

The initial Stage 3 pass evaluates three kinds of tasks:

1. Binary classification of **low next-night recovery**
2. Regression of **next-night numeric sleep targets**
3. Secondary binary classification of **high next-night avgSleepStress**

The modeling frame is built from the strict-quality day slice and aligned with next-night sleep targets using the same `D -> D+1` contract used in Stage 2 directional analysis.

## Data and Split

Current notebook run snapshot:
- modeling rows: `525`
- rows with next-night recovery target: `464`
- rows with next-night overall/quality targets: `464`
- rows with next-night avgSleepStress target: `465`
- split strategy: contiguous time-ordered `60/20/20` train/validation/test

This is intentional. Random train/test shuffling would overstate quality on a single-subject temporal dataset.

## Main Result: Low Recovery Classification Works Moderately

The strongest current Stage 3 story is a binary task:
- target: `next-night sleepRecoveryScore < 75`

Why `75`:
- `70` makes the positive class too rare for a clean baseline story
- `79/80` drift too close to a median split and lose the “bad night” interpretation
- `75` is a practical middle ground between class balance and domain meaning

### Best interpretable result

Forward feature selection on the compact awake + stress set yields a small logistic model with:
- `awakeAverageStressLevel`
- `maxHeartRate`
- `bodyBatteryLowest`

On the current test split, the sparse logistic variants land around:
- balanced accuracy: `~0.64`
- ROC-AUC: `~0.64-0.65`
- PR-AUC: `~0.35`
- F1: `~0.46`

This is not a strong production model, but it is a real predictive signal and a defensible portfolio result on noisy single-subject wearable data.

### Best nonlinear benchmark

`HistGradientBoostingClassifier` on the forward-selected compact set performs slightly better on ranking metrics:
- balanced accuracy: `~0.64`
- ROC-AUC: `~0.68`
- PR-AUC: `~0.40`

This is useful as a benchmark, but the sparse logistic model remains easier to explain and defend.

### Practical interpretation

The current classifier behaves more like a **risk flag** than a precise detector:
- it catches a large share of low-recovery nights
- it still produces many false positives

That is acceptable for Stage 3. The honest interpretation is:
- daytime signals can moderately identify elevated next-night recovery risk
- they do not support precise decision-grade prediction yet

## Feature Selection Result

Stage 3 now includes a time-aware forward feature selection pass rather than relying only on manual feature bundles.

This matters because it shows that the signal does not depend on throwing dozens of columns at the model.
The selected features repeatedly emphasize:
- awake stress level
- heart-rate load
- low-end Body Battery state

That is directionally consistent with the Stage 2 carryover story.

## Negative Result: Numeric Regression Is Still Weak

The current regression tasks do **not** beat a simple median baseline on the test split for:
- `sleepRecoveryScore`
- `sleepOverallScore`
- `sleepQualityScore`
- `avgSleepStress`

This is an important result, not a failure to hide:
- day-level awake aggregates appear sufficient for coarse risk classification
- the same feature layer is not sufficient for reliable numeric next-night prediction

Likely reasons:
- small single-subject dataset
- noisy or composite Garmin-derived scores
- bounded / ceiling-heavy targets, especially recovery
- missing lag and recent-history context

## Secondary Result: High AvgSleepStress Classification

As a follow-up branch, Stage 3 also tested:
- target: `high next-night avgSleepStress`
- cutoff: top quartile (`>= ~19.1`)

This produced a weaker and less stable story than low-recovery classification.
Best manual runs reached roughly:
- balanced accuracy: `~0.62-0.64`
- ROC-AUC: `~0.65-0.68`
- PR-AUC: `~0.34-0.35`

But automated feature selection did not preserve that quality cleanly, so this branch is currently better treated as a **secondary exploratory result**, not the main Stage 3 headline.

## Current Takeaway

At this stage, the project can support a careful public claim:

> Daytime Garmin-derived signals contain moderate predictive information about the risk of low next-night recovery, especially via awake stress and low-end body-energy context, but they do not yet support reliable prediction of exact next-night score values.

That is already useful for a DS-generalist portfolio story because it demonstrates:
- a reproducible modeling setup
- time-aware evaluation
- honest model comparison
- feature selection beyond raw notebook intuition
- willingness to keep negative results instead of hiding them

## Logical Next Steps

If Stage 3 continues, the most promising additions are:

1. Add lag and rolling features (`D-1`, trailing 3-day means, recent stress load)
2. Keep binary targets primary; avoid expanding regression unless a better feature layer appears
3. Add brief statistical validation summaries so Stage 2 findings and Stage 3 modeling tell one coherent story
