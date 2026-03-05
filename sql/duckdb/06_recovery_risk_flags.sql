SELECT
    day_date,
    day_awake_average_stress,
    day_max_heart_rate,
    day_body_battery_lowest,
    nextsleep_recovery_score,
    CASE
        WHEN day_awake_average_stress >= 60 THEN 'high_stress'
        WHEN day_awake_average_stress >= 50 THEN 'mid_stress'
        ELSE 'lower_stress'
    END AS stress_band,
    CASE
        WHEN nextsleep_recovery_score < 75 THEN 1
        ELSE 0
    END AS low_recovery_flag
FROM vw_day_to_next_sleep
WHERE valid_day_strict IS TRUE
  AND corrupted_stress_only_day IS NOT TRUE
  AND day_awake_average_stress IS NOT NULL
  AND nextsleep_recovery_score IS NOT NULL
ORDER BY day_date;
