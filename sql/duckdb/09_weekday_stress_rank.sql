WITH ranked AS (
    SELECT
        iso_weekday,
        weekday_name,
        avg_awake_stress,
        DENSE_RANK() OVER (ORDER BY avg_awake_stress DESC) AS stress_rank_desc
    FROM vw_weekday_profiles
)
SELECT
    iso_weekday,
    weekday_name,
    ROUND(avg_awake_stress, 2) AS avg_awake_stress,
    stress_rank_desc
FROM ranked
ORDER BY stress_rank_desc, iso_weekday;
