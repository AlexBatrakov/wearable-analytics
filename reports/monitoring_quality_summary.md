# Monitoring Quality Summary

This report summarizes the compact quality layer used before feature selection. Processed parquet files remain local.

## Outputs

- `data/processed/monitoring_quality_index.parquet`

## Analysis Rows

- Analysis rows: `498`
- Rows with observed next sleep boundary: `446`
- Rows with synthetic split timestamp populated: `48`
- Unsupported multi-day gap rows: `27`
- Rows plausible under `2..16h` sleep and `6..30h` wake bounds: `446`
- Rows eligible for recovery modeling v0: `408`
- Max accepted/split wake duration: `26.87` hours
- Max raw observed wake duration: `3830.30` hours

## Next Sleep Status

- observed_within_cutoff: `421`
- missing_after_cutoff: `76`
- no_following_observed_sleep: `1`

## Boundary Confidence

- observed: `421`
- synthetic_split: `48`
- unsupported_multi_day_gap: `27`
- observed_late_within_duration: `1`
- missing_next_sleep: `1`

## Wake End Source

- observed_next_sleep: `421`
- unsupported_multi_day_gap: `27`
- synthetic_midpoint_split: `24`
- observed_next_sleep_after_split: `24`
- observed_next_sleep_after_cutoff_within_duration: `1`
- no_following_observed_sleep: `1`

## Usable Flags

- `sleep_hr_usable`: `471`
- `sleep_stress_usable`: `472`
- `wake_hr_usable`: `423`
- `wake_stress_usable`: `423`
- `pre_sleep_4h_usable`: `428`
- `wake_quarters_usable`: `391`

## Internal Quality Windows

Long-format quality-window diagnostics are computed internally and are not persisted by default.
- Internal rows evaluated: `6,540`
- Logical windows evaluated: `pre_sleep_4h, sleep, wake, wake_q1, wake_q2, wake_q3, wake_q4`

## Quality Policy

- Packet 02 accepts next sleep only before local noon on the day after wake starts.
- After-cutoff next sleeps with observed wake duration up to `30h` are retained as late-but-plausible observed wake boundaries.
- After-cutoff intervals from `30h` to `60h` may be split with an explicit synthetic midpoint when no real calendar-date collision would be created.
- Longer gaps are marked unsupported instead of being expanded into fake analysis days.
- Sleep duration plausibility uses `2..16` hours; wake duration plausibility uses `6..30` hours.
- Quality prioritizes coverage fraction, largest gap duration, boundary coverage, and known/missing boundaries.
- Baseline usable flags allow max gaps up to `360` minutes; analysts can still create stricter subsets such as `*_max_gap_minutes <= 180`.
- `modeling_recovery_v0_eligible` is a baseline row-level recovery modeling flag requiring plausible sleep/wake windows and usable whole sleep/wake HR/stress.
- `pre_sleep_4h_usable` remains an optional pre-sleep anchored-feature diagnostic and is not a hard baseline eligibility requirement.
- Stress quality coverage counts semantic stress observations: raw `0..100` plus raw `-2` only when same-minute valid HR confirms activity.
- Numeric stress feature statistics still use only raw `0..100` values.
- Raw stress `-1` and raw `-2` without same-minute valid HR remain unmeasurable for stress coverage.
- Raw stress `-2` is split into HR-confirmed active proxy and no-HR unmeasurable diagnostics; only same-minute valid HR confirms activity.
