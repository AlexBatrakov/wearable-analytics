WITH aligned AS (
    SELECT
        day_date,
        day_awake_average_stress,
        nextsleep_recovery_score
    FROM vw_day_to_next_sleep
    WHERE valid_day_strict IS TRUE
      AND corrupted_stress_only_day IS NOT TRUE
      AND day_awake_average_stress IS NOT NULL
      AND nextsleep_recovery_score IS NOT NULL
),
ranked AS (
    SELECT
        day_date,
        day_awake_average_stress,
        nextsleep_recovery_score,
        NTILE(4) OVER (ORDER BY day_awake_average_stress) AS stress_quartile
    FROM aligned
)
SELECT
    stress_quartile,
    COUNT(*) AS days,
    ROUND(AVG(day_awake_average_stress), 2) AS avg_awake_stress,
    ROUND(AVG(nextsleep_recovery_score), 2) AS avg_next_recovery,
    ROUND(MEDIAN(nextsleep_recovery_score), 2) AS median_next_recovery
FROM ranked
GROUP BY stress_quartile
ORDER BY stress_quartile;
