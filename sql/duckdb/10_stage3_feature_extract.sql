SELECT
    day_date,
    day_awake_average_stress,
    day_max_heart_rate,
    day_body_battery_lowest,
    day_total_steps,
    nextsleep_recovery_score,
    CASE
        WHEN nextsleep_recovery_score < 75 THEN 1
        ELSE 0
    END AS target_low_recovery
FROM vw_day_to_next_sleep
WHERE valid_day_strict IS TRUE
  AND corrupted_stress_only_day IS NOT TRUE
  AND day_awake_average_stress IS NOT NULL
  AND day_max_heart_rate IS NOT NULL
  AND day_body_battery_lowest IS NOT NULL
  AND nextsleep_recovery_score IS NOT NULL
ORDER BY day_date;
