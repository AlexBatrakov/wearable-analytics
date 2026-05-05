# Monitoring Core Features Summary

`monitoring_features_core_v0.parquet` is a compact starter subset derived from the cleaned full feature table.

## Outputs

- `data/processed/monitoring_features_core_v0.parquet`

## Shape

- Rows: `498`
- Columns: `93`
- Quality index rows: `498`
- Recovery modeling v0 eligible rows: `408`

## Core Feature Family Counts

- HR MHR zones: `7`
- distribution/shape: `20`
- identifier: `2`
- pre-sleep/recovery: `13`
- recovery/contrast: `13`
- relative quarters: `12`
- stress states: `10`
- trends: `8`
- variability: `8`

## Scope

- Core keeps a small set of whole sleep/wake summaries, simplified stress states, wake HR zones, trends, wake quarters, pre-sleep recovery, and sleep-wake contrasts.
- Core excludes quality/debug columns. Join `monitoring_quality_index.parquet` on `analysis_window_id` for filtering.
- Baseline recovery eligibility does not require `pre_sleep_4h_usable`; use that flag only for stricter pre-sleep sensitivity analyses.
- Baseline usable flags allow max gaps up to `360` minutes, while `*_max_gap_minutes <= 180` remains available as a stricter subset rule.
- Quality stress coverage counts raw `0..100` plus raw `-2` only when same-minute valid HR confirms activity; numeric stress features remain restricted to raw `0..100`.
- Anchored window zoo, endpoint diagnostics, raw status fractions, coverage metrics, and activation/spectral features are absent from core v0.

## Stress State Semantics

- `stress_frac_resting`: raw stress `0..25`.
- `stress_frac_low`: raw stress `26..50`.
- `stress_frac_medium`: raw stress `51..75`.
- `stress_frac_high`: raw stress `76..100`.
- `stress_frac_active`: raw stress `-2` with same-minute valid HR, retained as an active/large-motion proxy.
- The denominator excludes raw `-1`, raw `-2` without same-minute valid HR, and minutes with no stress row.
