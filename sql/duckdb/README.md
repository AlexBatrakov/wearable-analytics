# DuckDB Portfolio Queries

This folder contains reproducible SQL examples for portfolio signaling.
They run against `data/processed/analytics.duckdb` and export result snapshots to `reports/sql/duckdb`.

Run via CLI:

```bash
garmin-analytics run-sql-portfolio
```

Run via script:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_duckdb_portfolio_queries.py
```

Query themes:

- quality label mix
- weekday profiles
- top stress days
- stress quartiles vs next-night recovery
- rolling recovery trend
- low-recovery risk flags
- sleep duration bands
- D->D+1 alignment coverage
- weekday stress rank
- Stage 3-ready feature extract
