SELECT
    iso_weekday,
    weekday_name,
    days_total,
    strict_good_days,
    ROUND(avg_steps, 1) AS avg_steps,
    ROUND(median_steps, 1) AS median_steps,
    ROUND(avg_awake_stress, 2) AS avg_awake_stress,
    ROUND(median_nextsleep_recovery, 2) AS median_nextsleep_recovery
FROM vw_weekday_profiles
ORDER BY iso_weekday;
