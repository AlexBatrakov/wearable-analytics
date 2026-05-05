# Monitoring Full Features Summary

`monitoring_features_full_v0.parquet` is the cleaned Packet 03 feature table for the next feature-selection experiments.

## Outputs

- `data/processed/monitoring_features_full_v0.parquet`
- `reports/monitoring_features_full_catalog.csv`
- `reports/monitoring_features_full_catalog.md`

## Shape

- Rows: `498`
- Columns: `243`
- Calendar date range: `2023-05-27 to 2026-02-05`

## Build Parameters

- Maximum heart rate parameter: `192` bpm
- Gap break threshold: `2` minutes
- Minimum valid minutes: `5`
- Minimum paired HR/stress minutes: `10`

## Feature Family Counts

- distribution/shape: `60`
- relative windows: `56`
- episodes/state structure: `35`
- variability/gaps: `20`
- HR MHR zones: `14`
- recovery/deactivation: `14`
- trends: `12`
- HR/stress coupling: `12`
- stress state fractions: `10`
- sleep-wake contrast: `8`
- identity/window metadata: `2`

## Included Families

- Distribution/shape summaries for sleep and wake HR and valid numeric stress.
- Simplified stress state fractions, including `stress_frac_active` from raw stress `-2` only when same-minute valid HR confirms activity.
- HR maximum-heart-rate zone fractions for sleep and wake.
- Gap-aware variability without exposing gap counters as model features.
- A small curated episode set with explicit no-event zero semantics.
- Sleep/wake quarter summaries, linear trends, pre-sleep recovery, sleep-wake contrasts, and HR/stress coupling.

## Explicitly Excluded From Feature Tables

- `p05`, `p95`, and `trimmed_mean` distribution variants.
- `stress_frac_medium_or_high` and other rolled-up stress states.
- Anchored window families such as `first_30m_after_wake`, `first_2h_after_wake`, `last_2h_before_sleep`, and `last_4h_before_sleep`.
- Endpoint diagnostics and `end_minus_start` contrasts.
- Coverage fractions, valid counts, total counts, max-gap metrics, and boundary timing diagnostics.
- Raw `-1`/`-2` diagnostic fractions, except the curated HR-confirmed `stress_frac_active` feature.
- Activation scores/bands and spectral period/frequency features.

## Stress And Entropy Policy

- Numeric stress features use only valid raw stress `0..100`.
- `stress_frac_active` is raw stress `-2` with same-minute valid HR, retained as an active/large-motion proxy rather than high stress.
- Stress entropy uses fixed bins: `0..25`, `26..50`, `51..75`, and `76..100`.
- HR entropy uses fixed maximum-heart-rate zones derived from `max_hr_bpm`.

## Quality Join Policy

- Row-level filtering lives in `data/processed/monitoring_quality_index.parquet`.
- Join on `analysis_window_id` before modeling or interpreting window-heavy features.
- `modeling_recovery_v0_eligible` is a baseline row-level flag for plausible sleep-wake-next-sleep windows with usable sleep and whole-wake HR/stress.
- `pre_sleep_4h_usable` is optional for baseline eligibility; filter on it for stricter pre-sleep sensitivity analyses.
- Baseline usable flags allow max gaps up to `360` minutes; use `*_max_gap_minutes <= 180` for stricter gap sensitivity subsets.
- In the quality index, stress coverage and stress usable flags count raw `0..100` plus raw `-2` only when same-minute valid HR confirms activity.
- Numeric stress feature statistics in this table still use only raw `0..100` values.
- The cleaned feature tables intentionally avoid duplicating quality diagnostics as candidate predictors.
