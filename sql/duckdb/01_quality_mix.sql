SELECT
    day_quality_label_strict AS strict_label,
    COUNT(*) AS days,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_days
FROM fact_quality
GROUP BY 1
ORDER BY days DESC, strict_label;
