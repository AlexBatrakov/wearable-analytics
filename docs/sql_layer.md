# SQL Layer (Stage 1.5)

Stage 1.5 adds an optional SQL analytics layer on top of existing parquet outputs.
It is designed for portfolio signaling (`DuckDB + PostgreSQL`) and does not replace the core Python pipeline.

Primary goal:
- show practical SQL skills (CTE, window functions, views, day-to-next-day alignment) on the same data model already used in Stage 2/3.

## Engines in this project

- **DuckDB (primary)**: local analytics mart for fast parquet-to-SQL workflows.
- **PostgreSQL (showcase)**: compact production-like mirror under `examples/postgres_showcase/`.

## SQL data contract

Default data boundary is privacy-safe Stage 1 outputs:

- `data/processed/daily_sanitized.parquet` (fallback: `daily.parquet`)
- `data/processed/sleep_sanitized.parquet` (fallback: `sleep.parquet`)
- `data/processed/daily_quality.parquet` (optional but recommended)

Canonical key:
- `calendarDate` as day-level key (materialized to SQL `DATE` in marts)

DuckDB mart objects:

- `fact_daily`
- `fact_sleep`
- `fact_quality`
- `vw_day_to_next_sleep` (`D -> D+1` join contract)
- `vw_weekday_profiles`
- `vw_sleep_nights` (canonical nightly sleep profile with alias-safe `sleep_avg_stress` and `sleep_hours`)

## Build DuckDB mart

```bash
garmin-analytics build-sql-mart
```

Optional overrides:

```bash
garmin-analytics build-sql-mart \
  --db-path data/processed/analytics.duckdb \
  --daily-path data/processed/daily_sanitized.parquet \
  --sleep-path data/processed/sleep_sanitized.parquet \
  --quality-path data/processed/daily_quality.parquet
```

Output:

- `data/processed/analytics.duckdb`

## Run portfolio SQL pack (DuckDB)

```bash
garmin-analytics run-sql-portfolio
```

Equivalent script mode:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_duckdb_portfolio_queries.py
```

Inputs:
- `sql/duckdb/*.sql`

Outputs:
- `reports/sql/duckdb/*.csv`

Privacy note:
- treat `reports/sql/duckdb/*.csv` as local generated artifacts from personal data; do not commit them.

## PostgreSQL showcase

Compact mirror files are under:

- `examples/postgres_showcase/README.md`
- `examples/postgres_showcase/schema.sql`
- `examples/postgres_showcase/load.sql`
- `examples/postgres_showcase/views.sql`
- `examples/postgres_showcase/queries.sql`

Flow:

1. Export CSV extracts:
   - `PYTHONPATH=src .venv/bin/python scripts/export_postgres_showcase_csv.py`
2. Start PostgreSQL via Docker Compose.
3. Apply schema/load/views SQL.
4. Run showcase queries.

## Why this stage exists

- Adds explicit SQL evidence to DS/DA portfolio story.
- Keeps one analytical narrative across Python + SQL instead of parallel disconnected analyses.
- Demonstrates both embedded analytics DB usage (DuckDB) and server-style relational modeling (PostgreSQL).
