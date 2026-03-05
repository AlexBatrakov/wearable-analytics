SELECT
    day_date,
    day_awake_average_stress,
    day_total_steps,
    nextsleep_recovery_score,
    day_quality_label_strict
FROM vw_day_to_next_sleep
WHERE valid_day_strict IS TRUE
  AND corrupted_stress_only_day IS NOT TRUE
  AND day_awake_average_stress IS NOT NULL
ORDER BY day_awake_average_stress DESC
LIMIT 20;
