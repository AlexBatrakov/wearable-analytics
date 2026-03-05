CREATE OR REPLACE VIEW analytics.vw_day_to_next_sleep AS
SELECT
    d.calendar_date AS day_date,
    d.total_steps AS day_total_steps,
    d.total_distance_meters AS day_total_distance_meters,
    d.active_kilocalories AS day_active_kilocalories,
    d.awake_average_stress_level AS day_awake_average_stress,
    d.max_heart_rate AS day_max_heart_rate,
    d.body_battery_lowest AS day_body_battery_lowest,
    q.day_quality_label_strict,
    q.valid_day_strict,
    q.corrupted_stress_only_day,
    s.calendar_date AS next_sleep_date,
    s.sleep_recovery_score AS nextsleep_recovery_score,
    s.sleep_overall_score AS nextsleep_overall_score,
    s.sleep_quality_score AS nextsleep_quality_score,
    s.avg_sleep_stress AS nextsleep_avg_sleep_stress
FROM analytics.fact_daily d
LEFT JOIN analytics.fact_quality q
    ON q.calendar_date = d.calendar_date
LEFT JOIN analytics.fact_sleep s
    ON s.calendar_date = d.calendar_date + INTERVAL '1 day';

CREATE OR REPLACE VIEW analytics.vw_weekday_profiles AS
SELECT
    EXTRACT(ISODOW FROM day_date)::INT AS iso_weekday,
    TO_CHAR(day_date, 'FMDay') AS weekday_name,
    COUNT(*) AS days_total,
    COUNT(*) FILTER (WHERE valid_day_strict IS TRUE) AS strict_good_days,
    AVG(day_total_steps) AS avg_steps,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY day_total_steps) AS median_steps,
    AVG(day_awake_average_stress) AS avg_awake_stress,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nextsleep_recovery_score) AS median_nextsleep_recovery
FROM analytics.vw_day_to_next_sleep
GROUP BY 1, 2
ORDER BY 1;
