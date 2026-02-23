# Stage 2 — EDA

Stage 2 uses notebooks to analyze trends and prepare next analytical decisions.
Current working mode is hybrid: notebooks for interactive exploration + reusable helpers in `src/garmin_analytics/eda/` + curated docs figures later.

## Notebook sequence

1. `notebooks/01_eda_prepare.ipynb` (Stage 2.0)
2. `notebooks/02_eda_timeseries.ipynb` (Stage 2.1)
3. `notebooks/03_eda_distributions.ipynb` (Stage 2.2)

## Current status (2026-02-23)

- **Stage 2.0 / `01_eda_prepare.ipynb`**: analysis contract + canonical slices completed, with coverage-aware overview tables/visuals (including a GitHub-style daily coverage/quality calendar heatmap)
- **Stage 2.1 / `02_eda_timeseries.ipynb`**: substantial draft exists; visual audit/refinement next
- **Stage 2.2 / `03_eda_distributions.ipynb`**: notebook file exists but still early/incomplete

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

### 2.2 Distributions notebook (in progress)

- Builds numeric distributions for strict daily and sleep slices
- Uses histogram + boxplot views to inspect skew, spread, and outliers
- Will also cover relationships, artifact review, and Stage 2 findings/hypotheses (not only distributions)
- Reuses the same figure export policy (`SAVE_FIGS` + local `reports/figures/` outputs)

## What’s next

Next additions:
- Audit and refine `02_eda_timeseries.ipynb` (chart-by-chart rubric review)
- Complete notebook 03 (distributions + relationships + artifact review + findings)
- Curate 2-4 hero figures into `docs/img/` and summarize Stage 2 findings in docs/README
- Optional feature set formalization for modeling-ready datasets

See also:
- [EDA guide](eda.md)
- [Pipeline flow](pipeline.md)
- [Stage 1 gate](stage1.md)
