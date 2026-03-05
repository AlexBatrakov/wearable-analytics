TRUNCATE TABLE analytics.fact_daily;
TRUNCATE TABLE analytics.fact_sleep;
TRUNCATE TABLE analytics.fact_quality;

\copy analytics.fact_daily FROM '/workspace/data/interim/postgres_showcase/daily.csv' WITH (FORMAT csv, HEADER true)
\copy analytics.fact_sleep FROM '/workspace/data/interim/postgres_showcase/sleep.csv' WITH (FORMAT csv, HEADER true)
\copy analytics.fact_quality FROM '/workspace/data/interim/postgres_showcase/quality.csv' WITH (FORMAT csv, HEADER true)
