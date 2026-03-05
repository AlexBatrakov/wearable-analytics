# PostgreSQL Showcase

This folder is a compact "production-like" SQL mirror of the DuckDB analytics mart.
It is intentionally small: enough to demonstrate PostgreSQL modeling, views, and analytical queries in a portfolio.

## What it includes

- `docker-compose.yml`: local PostgreSQL 16 service
- `schema.sql`: `analytics.fact_*` tables
- `load.sql`: `\copy` load commands from local CSV extracts
- `views.sql`: `vw_day_to_next_sleep`, `vw_weekday_profiles`
- `queries.sql`: sample analytical SQL queries

## 1) Export CSV from parquet

From repo root:

```bash
PYTHONPATH=src .venv/bin/python scripts/export_postgres_showcase_csv.py
```

This writes files under:

- `data/interim/postgres_showcase/daily.csv`
- `data/interim/postgres_showcase/sleep.csv`
- `data/interim/postgres_showcase/quality.csv`

## 2) Start PostgreSQL

```bash
docker compose -f examples/postgres_showcase/docker-compose.yml up -d
```

## 3) Create schema and load data

```bash
docker compose -f examples/postgres_showcase/docker-compose.yml exec -T db \
  psql -U postgres -d wearable_analytics < examples/postgres_showcase/schema.sql

docker compose -f examples/postgres_showcase/docker-compose.yml exec -T db \
  psql -U postgres -d wearable_analytics < examples/postgres_showcase/load.sql

docker compose -f examples/postgres_showcase/docker-compose.yml exec -T db \
  psql -U postgres -d wearable_analytics < examples/postgres_showcase/views.sql
```

## 4) Run showcase queries

```bash
docker compose -f examples/postgres_showcase/docker-compose.yml exec -T db \
  psql -U postgres -d wearable_analytics < examples/postgres_showcase/queries.sql
```

## Notes

- This showcase is optional and does not change the main pipeline.
- It uses sanitized/quality-aware outputs only (no raw export files).
- For real deployment you'd add roles, migrations, and stricter types/constraints.
