# Stage 2 — EDA

Stage 2 uses notebooks to analyze trends and prepare next analytical decisions.
Current working mode is hybrid: notebooks for interactive exploration + reusable helpers in `src/garmin_analytics/eda/` + curated public figures in `docs/img/`.

For a concise portfolio narrative built from the final Stage 2 outputs, start with [the case study](case_study.md).

## Notebook sequence

1. `notebooks/01_eda_prepare.ipynb` (Stage 2.0)
2. `notebooks/02_eda_timeseries.ipynb` (Stage 2.1)
3. `notebooks/03_eda_distributions.ipynb` (Stage 2.2)
4. `notebooks/04_eda_relationships.ipynb` (Stage 2.3)

## Current status (2026-03-02)

- **Stage 2.0 / `01_eda_prepare.ipynb`**: analysis contract + canonical slices completed, with coverage-aware overview tables/visuals (including a GitHub-style daily coverage/quality calendar heatmap)
- **Stage 2.1 / `02_eda_timeseries.ipynb`**: curated subsystem timelines completed (activity, stress, heart, Body Battery, sleep timing/duration/stages, respiration, SpO2)
- **Stage 2.2 / `03_eda_distributions.ipynb`**: curated distributions + segmented comparisons (weekday/weekend, day-of-week, sleep quality buckets)
- **Stage 2.3 / `04_eda_relationships.ipynb`**: directional relationships (`D -> D`, `D -> D+1`), grouped correlation screening, targeted validation plots, lightweight artifact review, and final Stage 2 synthesis

### 2.0 Prepare notebook

- Loads sanitized + quality-enriched daily data
- Constructs canonical slices for analysis (all, strict-valid, sleep-covered)
- Computes shared derived features for downstream plots
- Defines the Stage 2 analysis contract (slice semantics, quality-filter usage, day/sleep alignment assumptions)
- Provides a coverage-aware overview before deeper plotting:
  - slice retention
  - strict vs loose label distribution
  - monthly key-signal coverage
  - GitHub-style day-level coverage/quality calendar

Coverage notes already visible in the Stage 2.0 calendar:
- long dark spans indicate no-wear / no corroborating-signal periods (coverage gaps, not behavioral evidence)
- partial/bad clusters often align with partial-day device coverage (e.g., watch battery depleted before day end)
- some short, isolated active streaks reflect temporary returns to wearing/charging cadence

### 2.1 Timeseries notebook

- Visualizes key signals over time
- Checks trend stability, outliers, and quality-flag interactions
- Surfaces candidate hypotheses for deeper analysis

Current plots include:
- steps
- stress coverage hours
- stacked stress shares
- resting HR
- min/max HR
- sleep start time-of-day (local)
- sleep duration (hours)
- sleep stage fractions (stacked)
- sleep respiration (lowest/average/highest)
- sleep scores (overall/quality/duration-or-recovery)
- avg sleep stress
- body battery high/low
- body battery range

### 2.2 Distributions notebook

- Builds numeric distributions for strict daily and sleep slices
- Uses histogram + boxplot views to inspect skew, spread, and outliers
- Reuses the same figure export policy (`SAVE_FIGS` + local `reports/figures/` outputs)

Current snapshot highlights:
- `totalSteps` is highly heterogeneous (p10≈821, median≈6389, p90≈14980), confirming mixed low-activity and active-day regimes.
- `step_length_m` centers around ~0.78 m/step with asymmetric tails, consistent with mostly walking plus smaller faster-gait periods.
- `floorsAscendedInMeters` shows a meaningful mass at `0` plus a broad main body around ~20–45 m, so climb activity is intermittent rather than smooth day-to-day.
- Day-of-week segmentation surfaces stable patterns:
  - Saturday is the most active day (`active_hours` median ≈1.35h; `totalSteps` median ≈8079).
  - Sunday median steps are markedly lower (~2822), and Sunday active time is also the lowest (`active_hours` median ≈0.50h).
  - Tuesday median awake stress is the highest (~58), consistent with known weekly context.
- Sleep duration by sleep-onset weekday is shortest on Monday onset (~7.88h) and longest on Saturday onset (~8.9h).
- Sleep-quality buckets show a coherent gradient:
  - median sleep duration rises from poor (~5.4h) to excellent (~8.9h),
  - median `avgSleepStress` declines from poor (~24.16) to excellent (~11.37).

### 2.3 Relationships notebook

- Focuses on relationship analysis and hypothesis generation:
  - sleep (morning) vs same-day daytime outcomes
  - daytime stress/activity vs next-night sleep outcomes
  - sleep-internal structural links
- Runs grouped `core` / `extended` correlation submatrices with reliability thresholds
- Adds targeted validation plots for strongest matrix observations
- Adds a lightweight artifact taxonomy over the union of suspicious-day exports
- Closes Stage 2 with final findings, hypotheses, and limitations

## What’s next

Current status after Stage 2 closeout:
- curated hero figures have been promoted into `docs/img/`
- Stage 2 findings have been summarized in the root `README.md`
- the recruiter-facing narrative now lives in [the case study](case_study.md)

Optional next additions:
- feature set formalization for modeling-ready datasets
- optional PCA-style appendix for dimensionality reduction / redundancy exploration
- follow-on analytical stages beyond EDA (only if they add real portfolio value)

See also:
- [EDA guide](eda.md)
- [Pipeline flow](pipeline.md)
- [Stage 1 gate](stage1.md)
