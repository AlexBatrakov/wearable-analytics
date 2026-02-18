# Stage 0 — Discovery, Ingestion, and Parquet Build

Stage 0 transforms raw Garmin exports into core parquet analytics tables.

## Commands

```bash
garmin-analytics discover
garmin-analytics ingest-uds
garmin-analytics ingest-sleep
garmin-analytics build-daily
```

Alternative module mode:

```bash
PYTHONPATH=src python -m garmin_analytics discover
PYTHONPATH=src python -m garmin_analytics ingest-uds
PYTHONPATH=src python -m garmin_analytics ingest-sleep
PYTHONPATH=src python -m garmin_analytics build-daily
```

## Outputs

- Inventory: `data/interim/inventory.csv`
- Parsed UDS table: `data/processed/daily_uds.parquet`
- Parsed sleep table: `data/processed/sleep.parquet`
- Merged daily table: `data/processed/daily.parquet`

## Quick plausibility checks

- **Row counts:** UDS/sleep/daily row counts should be non-zero and in a plausible range for your export period.
- **Date range:** `daily.parquet` should span the expected calendar window for your data pull.
- **Missingness sanity:** core day-level fields should not be unexpectedly null across most rows.

## Interpretation

- `discover` is a visibility step: it tells you what source files are available.
- `ingest-*` creates source-specific normalized tables.
- `build-daily` creates the unified day-level base used by Stage 1.

## Exit criteria

Stage 0 is complete when all three parquet files exist and row counts look plausible for the expected date range.

For command options and overrides, see [CLI](cli.md).
