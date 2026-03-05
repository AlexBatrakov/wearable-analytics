SELECT
    day_date,
    nextsleep_recovery_score,
    ROUND(
        AVG(nextsleep_recovery_score) OVER (
            ORDER BY day_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS next_recovery_7d_ma
FROM vw_day_to_next_sleep
WHERE valid_day_strict IS TRUE
  AND corrupted_stress_only_day IS NOT TRUE
  AND nextsleep_recovery_score IS NOT NULL
ORDER BY day_date;
