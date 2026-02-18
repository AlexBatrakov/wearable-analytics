# Stage 2 — EDA

Stage 2 uses notebooks to analyze trends and prepare next analytical decisions.

## Notebook sequence

1. `notebooks/01_eda_prepare.ipynb` (Stage 2.0)
2. `notebooks/02_eda_timeseries.ipynb` (Stage 2.1)

## What Stage 2 contains

### 2.0 Prepare notebook

- Loads sanitized + quality-enriched daily data
- Constructs canonical slices for analysis (all, strict-valid, sleep-covered)
- Computes shared derived features for downstream plots

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

## What’s next

Next additions:
- Sleep phase composition plots (deep/light/rem/awake)
- Notebook 03 focused on distributions/outliers and targeted hypotheses
- Optional feature set formalization for modeling-ready datasets

See also:
- [EDA guide](eda.md)
- [Pipeline flow](pipeline.md)
- [Stage 1 gate](stage1.md)
