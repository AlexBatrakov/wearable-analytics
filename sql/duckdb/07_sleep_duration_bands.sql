WITH banded AS (
    SELECT
        sleep_date,
        sleep_hours,
        sleep_overall_score,
        sleep_avg_stress,
        CASE
            WHEN sleep_hours < 6 THEN '<6h'
            WHEN sleep_hours < 7.5 THEN '6-7.5h'
            WHEN sleep_hours < 9 THEN '7.5-9h'
            ELSE '>=9h'
        END AS sleep_band
    FROM vw_sleep_nights
    WHERE sleep_hours > 0
)
SELECT
    sleep_band,
    COUNT(*) AS nights,
    ROUND(AVG(sleep_hours), 2) AS avg_sleep_hours,
    ROUND(MEDIAN(sleep_overall_score), 2) AS median_overall_score,
    ROUND(AVG(sleep_avg_stress), 2) AS avg_sleep_stress
FROM banded
GROUP BY sleep_band
ORDER BY
    CASE sleep_band
        WHEN '<6h' THEN 1
        WHEN '6-7.5h' THEN 2
        WHEN '7.5-9h' THEN 3
        ELSE 4
    END;
