# Pipeline Sanity Notes

## Why some fields look duplicated

The Garmin source schema contains overlapping summaries that can appear duplicated after flattening:

- stressTotalDurationSeconds and allDayStress_TOTAL_totalDuration represent the same concept from two source branches.
- Flattened nested blocks can repeat structural fields (for example date/profile-related metadata in raw source objects).

## Validation result used in Stage 1

On the Stage 1 aggregated dataset (580 rows):

- stress_duration_matches_allDayStress_TOTAL: 100.00% true
- stress_awake_matches_allDayStress_AWAKE: 100.00% true

This confirms the stress duration duplicate mappings are internally consistent for current data.
