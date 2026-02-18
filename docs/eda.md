# EDA

EDA is Stage 2 of this project and is notebook-driven.
Use sanitized + quality-enriched datasets to keep analysis privacy-safe and interpretable.

## Notebook 01: prepare

- File: `notebooks/01_eda_prepare.ipynb`
- Purpose: build canonical analysis slices from `daily_sanitized.parquet` + `daily_quality.parquet`
- Typical outputs in-session: joined table checks, derived features, readiness summary

Questions answered:
- Is the analysis table complete enough to proceed?
- Which records should be excluded (`corrupted_stress_only_day`, invalid days)?
- Are derived features (stress hours, sleep composition, etc.) ready for timeseries work?

## Notebook 02: timeseries

- File: `notebooks/02_eda_timeseries.ipynb`
- Purpose: inspect trends, seasonality, anomalies, and feature interactions over time

Questions answered:
- How do key health and activity signals evolve over the date range?
- Where do quality flags align with visible artifacts?
- Which features should drive next-stage modeling or summaries?

## Figure export behavior

The timeseries workflow supports a `SAVE_FIGS` toggle to export figures during notebook runs.
Exported figures land under `reports/figures/...`.
Treat these as local, generated artifacts; they are intended to stay out of normal commits (`reports/figures/` is gitignored).

## Planned notebook 03

Planned next step:
- `notebooks/03_eda_hypotheses.ipynb` (name may vary)
- Focus: targeted hypothesis checks, compact charts/tables, and decision-ready findings

See also:
- [Stage 2 details](stage2.md)
- [Pipeline flow](pipeline.md)
