CREATE SCHEMA IF NOT EXISTS analytics;

DROP TABLE IF EXISTS analytics.fact_daily CASCADE;
DROP TABLE IF EXISTS analytics.fact_sleep CASCADE;
DROP TABLE IF EXISTS analytics.fact_quality CASCADE;

CREATE TABLE analytics.fact_daily (
    calendar_date DATE PRIMARY KEY,
    total_steps DOUBLE PRECISION,
    total_distance_meters DOUBLE PRECISION,
    active_kilocalories DOUBLE PRECISION,
    awake_average_stress_level DOUBLE PRECISION,
    max_heart_rate DOUBLE PRECISION,
    body_battery_lowest DOUBLE PRECISION
);

CREATE TABLE analytics.fact_sleep (
    calendar_date DATE PRIMARY KEY,
    sleep_recovery_score DOUBLE PRECISION,
    sleep_overall_score DOUBLE PRECISION,
    sleep_quality_score DOUBLE PRECISION,
    avg_sleep_stress DOUBLE PRECISION,
    sleep_start_ts_gmt BIGINT,
    sleep_end_ts_gmt BIGINT
);

CREATE TABLE analytics.fact_quality (
    calendar_date DATE PRIMARY KEY,
    day_quality_label_strict TEXT,
    valid_day_strict BOOLEAN,
    corrupted_stress_only_day BOOLEAN
);

CREATE INDEX idx_fact_daily_calendar_date ON analytics.fact_daily(calendar_date);
CREATE INDEX idx_fact_sleep_calendar_date ON analytics.fact_sleep(calendar_date);
CREATE INDEX idx_fact_quality_calendar_date ON analytics.fact_quality(calendar_date);
