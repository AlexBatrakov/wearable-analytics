# Stage 3 — Validation and Modeling

Stage 3 extends the EDA-driven findings from [Stage 2](stage2.md) into explicit validation and prediction tasks.
The current focus is narrow on purpose: test whether `day D` awake signals contain usable information about `next-night` sleep outcomes, and keep the modeling story interpretable.

Primary evidence notebook:
- `notebooks/05_modeling_recovery.ipynb`
- `notebooks/06_statistical_validation.ipynb`

## Current Scope

The current Stage 3 pass evaluates three kinds of tasks:

1. Binary classification of **low next-night recovery**
2. Regression of **next-night numeric sleep targets**
3. Lightweight statistical validation of a small number of headline findings

The modeling frame is built from the strict-quality day slice and aligned with next-night sleep targets using the same `D -> D+1` contract used in Stage 2 directional analysis.

## Data and Split

Current notebook run snapshot:
- modeling rows: `617`
- rows with next-night recovery target: `543`
- rows with next-night overall/quality targets: `543`
- rows with next-night avgSleepStress target: `544`
- split strategy: contiguous time-ordered `60/20/20` train/validation/test

This is intentional. Random train/test shuffling would overstate quality on a single-subject temporal dataset.

## Statistical Validation Snapshot

Stage 3 now also includes a narrow statistical-validation pass for the claims already visible in Stage 2 and used by the Stage 3 modeling story.

Current validated results:
- **Saturday vs Sunday steps**: supported
  - Saturday median steps: `~7555`
  - Sunday median steps: `~2085`
  - Mann-Whitney `p ≈ 5.4e-06`
  - bootstrap median-difference CI: roughly `[2785, 7471]`
  - effect size: Cliff's delta `~0.387`
- **Awake stress (D) -> next-night recovery (D+1)**: supported
  - `n=543`
  - Spearman rho `~ -0.323`
  - 95% bootstrap CI roughly `[-0.394, -0.246]`
  - `p ≈ 6.3e-15`
- **Awake stress (D) -> next-night sleep stress (D+1)**: supported
  - `n=529`
  - Spearman rho `~ +0.296`
  - 95% bootstrap CI roughly `[0.216, 0.372]`
  - `p ≈ 2.0e-12`
- **Tuesday higher stress than other weekdays**: weak / inconclusive
  - Tuesday median awake stress is higher descriptively (`~58.5` vs `~56`)
  - omnibus weekday difference is not significant in the current strict slice
  - planned Tuesday-vs-rest contrast is also weak (`p ≈ 0.069`)

Interpretation:
- the strongest public directional claims are no longer only visual impressions
- the Tuesday observation remains a useful descriptive note, but not a validated headline result

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
- `restingHeartRate`

On the current 109-row test split, the selected sparse L1 logistic model lands around:
- balanced accuracy: `~0.68`
- ROC-AUC: `~0.71`
- PR-AUC: `~0.60`
- F1: `~0.62`

This is not a strong production model, but it is a real predictive signal and a defensible portfolio result on noisy single-subject wearable data.

### Nonlinear benchmark

`HistGradientBoostingClassifier` remains useful as a benchmark, but the refreshed run does not make it the headline result. The best manual gradient-boosting screen for the `<75` task is around:
- balanced accuracy: `~0.64`
- ROC-AUC: `~0.64`
- PR-AUC: `~0.47`

The sparse logistic result is both stronger on the selected test metrics and easier to explain.

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
The selected features emphasize:
- awake stress level
- resting heart-rate context

That is directionally consistent with the Stage 2 carryover story.

## Limited Result: Numeric Regression Is Still Weak

The current regression tasks remain weaker than classification. Tree models show small positive `R^2` on the test split for:
- `avgSleepStress` (`R^2 ~0.13`)
- `sleepRecoveryScore` (`R^2 ~0.10`)

But exact score prediction is still not reliable, and the other score targets stay near or below a simple median baseline:
- `sleepOverallScore`
- `sleepQualityScore`

This is an important result, not a failure to hide:
- day-level awake aggregates appear sufficient for coarse risk classification
- the same feature layer is not sufficient for reliable numeric next-night prediction

Likely reasons:
- small single-subject dataset
- noisy or composite Garmin-derived scores
- bounded / ceiling-heavy targets, especially recovery
- missing lag and recent-history context

## Current Takeaway

At this stage, the project can support a careful public claim:

> Daytime Garmin-derived signals contain moderate predictive information about the risk of low next-night recovery, especially via awake stress and resting heart-rate context, but they do not yet support reliable prediction of exact next-night score values.

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
3. Expand validation only if it materially strengthens the public narrative; avoid broad hypothesis sprawl
