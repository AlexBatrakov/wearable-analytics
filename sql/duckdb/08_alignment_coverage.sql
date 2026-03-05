SELECT
    COUNT(*) AS day_rows,
    COUNT(next_sleep_date) AS rows_with_next_sleep,
    ROUND(100.0 * COUNT(next_sleep_date) / COUNT(*), 2) AS next_sleep_coverage_pct,
    COUNT(*) FILTER (WHERE valid_day_strict IS TRUE) AS strict_day_rows,
    COUNT(next_sleep_date) FILTER (WHERE valid_day_strict IS TRUE) AS strict_rows_with_next_sleep,
    ROUND(
        100.0 * COUNT(next_sleep_date) FILTER (WHERE valid_day_strict IS TRUE)
        / NULLIF(COUNT(*) FILTER (WHERE valid_day_strict IS TRUE), 0),
        2
    ) AS strict_next_sleep_coverage_pct
FROM vw_day_to_next_sleep;
