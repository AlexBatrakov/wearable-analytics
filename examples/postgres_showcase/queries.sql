-- 1) strict quality mix
SELECT
    day_quality_label_strict,
    COUNT(*) AS days,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_days
FROM analytics.fact_quality
GROUP BY 1
ORDER BY days DESC;

-- 2) weekday profile
SELECT
    iso_weekday,
    weekday_name,
    days_total,
    strict_good_days,
    ROUND(avg_steps::numeric, 1) AS avg_steps,
    ROUND(median_steps::numeric, 1) AS median_steps,
    ROUND(avg_awake_stress::numeric, 2) AS avg_awake_stress,
    ROUND(median_nextsleep_recovery::numeric, 2) AS median_nextsleep_recovery
FROM analytics.vw_weekday_profiles
ORDER BY iso_weekday;

-- 3) stress quartiles vs next-night recovery
WITH aligned AS (
    SELECT
        day_date,
        day_awake_average_stress,
        nextsleep_recovery_score
    FROM analytics.vw_day_to_next_sleep
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
    ROUND(AVG(day_awake_average_stress)::numeric, 2) AS avg_awake_stress,
    ROUND(AVG(nextsleep_recovery_score)::numeric, 2) AS avg_next_recovery
FROM ranked
GROUP BY 1
ORDER BY 1;

-- 4) rolling 7-day next-night recovery
SELECT
    day_date,
    nextsleep_recovery_score,
    ROUND(
        AVG(nextsleep_recovery_score) OVER (
            ORDER BY day_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::numeric,
        2
    ) AS next_recovery_7d_ma
FROM analytics.vw_day_to_next_sleep
WHERE valid_day_strict IS TRUE
  AND corrupted_stress_only_day IS NOT TRUE
  AND nextsleep_recovery_score IS NOT NULL
ORDER BY day_date;
