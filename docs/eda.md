# EDA

EDA is Stage 2 of this project and is notebook-driven.
Use sanitized + quality-enriched datasets to keep analysis privacy-safe and interpretable.

For a concise portfolio narrative that summarizes the notebook outputs, start with [the case study](case_study.md). Treat the notebooks below as the evidence layer and technical depth.

## Notebook 01: prepare

- File: `notebooks/01_eda_prepare.ipynb`
- Purpose: build canonical analysis slices from `daily_sanitized.parquet` + `daily_quality.parquet`
- Typical outputs in-session: joined table checks, derived features, readiness summary, coverage-aware overview visuals (including a daily calendar heatmap)

Questions answered:
- Is the analysis table complete enough to proceed?
- Which records should be excluded (`corrupted_stress_only_day`, invalid days)?
- Are derived features (stress hours, sleep composition, etc.) ready for timeseries work?

## Notebook 02: timeseries

- File: `notebooks/02_eda_timeseries.ipynb`
- Purpose: inspect trends, seasonality, anomalies, and feature interactions over time
- Includes a dedicated "Sleep timeseries" section (sleep start time, duration, stage fractions, respiration, scores, avg sleep stress)

Questions answered:
- How do key health and activity signals evolve over the date range?
- Where do quality flags align with visible artifacts?
- Which features should drive next-stage modeling or summaries?

## Figure export behavior

The timeseries workflow supports a `SAVE_FIGS` toggle to export figures during notebook runs.
Exported figures for Notebook 02 land under `reports/figures/timeseries/`.
Treat these as local, generated artifacts; they are intended to stay out of normal commits (`reports/figures/` is gitignored).
Notebook 02 exports sleep-timeseries figures via the same toggle/mechanism when `SAVE_FIGS=True`.

## Notebook 03: distributions + segmented patterns

- File: `notebooks/03_eda_distributions.ipynb`
- Purpose: characterize metric distributions and segmented behavior before relationship analysis
- Covers:
  - distribution shape checks (hist + box + ECDF)
  - weekday/weekend segmentation
  - day-of-week segmentation (including sleep-onset anchored weekday for sleep metrics)
  - sleep-quality-bucket segmentation (Garmin thresholds)

Questions answered:
- Which metrics are heavy-tailed, clipped, or bounded by device/model logic?
- Which behavioral differences appear only after segmentation (not in global distributions)?
- Which stable segmented patterns should be carried into directional relationship checks?

## Notebook 04: relationships + correlations + artifacts

- File: `notebooks/04_eda_relationships.ipynb`
- Purpose: directional interaction analysis, matrix screening, artifact review, and final Stage 2 synthesis
- Covers:
  - `D -> D` (sleep morning context vs same-day daytime outcomes)
  - `D -> D+1` (daytime stress/activity vs next-night sleep outcomes)
  - grouped correlation screening (`core` / `extended`)
  - targeted validation plots for strongest matrix observations
  - lightweight artifact/anomaly review
  - final findings / hypotheses / limitations for Stage 2

Questions answered:
- Which pairwise associations remain stable after explicit temporal alignment?
- Which matrix findings survive targeted distribution-level validation?
- Which suspicious days are likely artifacts versus plausible edge cases?
- Which hypotheses are strong enough to move into final showcase narrative?

See also:
- [Case study](case_study.md)
- [Stage 2 details](stage2.md)
- [Pipeline flow](pipeline.md)
