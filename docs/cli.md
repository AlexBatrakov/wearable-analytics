# CLI

Primary mode uses the installed console script:

```bash
garmin-analytics --help
```

Alternative module mode:

```bash
PYTHONPATH=src python -m garmin_analytics --help
```

## Paths & conventions

- Raw Garmin exports are expected under `data/raw/DI_CONNECT` by default (`GARMIN_EXPORT_DIR` can override).
- Generated artifacts are written under `data/interim`, `data/processed`, and `reports`.
- `data/` is gitignored and must remain local.
- Timeseries figures are exported locally to `reports/figures/timeseries/` and should not be committed.

## Stage 0 commands

### discover

Purpose: discover available Garmin export files and write an inventory CSV.

```bash
garmin-analytics discover
```

Expected outputs:

- `data/interim/inventory.csv`

Expected output shape:

```text
Export dir: data/raw/DI_CONNECT
Found UDS files: <N>
Found sleep files: <M>
Wrote inventory: data/interim/inventory.csv
```

### ingest-uds

Purpose: parse UDS JSON exports into a normalized daily UDS parquet table.

```bash
garmin-analytics ingest-uds
```

Expected outputs:

- `data/processed/daily_uds.parquet`

Expected output shape:

```text
Wrote <N> rows to data/processed/daily_uds.parquet
```

### ingest-sleep

Purpose: parse sleep JSON exports into a normalized sleep parquet table.

```bash
garmin-analytics ingest-sleep
```

Expected outputs:

- `data/processed/sleep.parquet`

Expected output shape:

```text
Wrote <N> rows to data/processed/sleep.parquet
```

### build-daily

Purpose: merge UDS and sleep day-level tables on `calendarDate`.

```bash
garmin-analytics build-daily
```

Expected outputs:

- `data/processed/daily.parquet`

Expected output shape:

```text
Wrote <N> rows to data/processed/daily.parquet
```

## Stage 1 commands

### sanitize

Purpose: remove identifier-like fields and create privacy-safer parquet copies.

```bash
garmin-analytics sanitize
```

Expected outputs:

- `data/processed/daily_sanitized.parquet`
- `data/processed/daily_uds_sanitized.parquet` (if `daily_uds.parquet` exists)
- `data/processed/sleep_sanitized.parquet` (if `sleep.parquet` exists)
- `data/processed/sanitize_report.json`

Expected output shape:

```text
Sanitized daily: <rows> rows, <before> → <after> cols (dropped <k>)
Sanitized daily_uds: ...
Sanitized sleep: ...
Wrote report: data/processed/sanitize_report.json
```

### data-dictionary

Purpose: generate a column-level inventory report for the aggregated dataset.

```bash
garmin-analytics data-dictionary
```

Expected outputs:

- `reports/data_dictionary.csv`
- `reports/data_dictionary.md`

Expected output shape:

```text
Wrote reports/data_dictionary.csv
Wrote reports/data_dictionary.md
```

### quality

Purpose: compute strict/loose day-quality labels and export diagnostics.

```bash
garmin-analytics quality
```

Expected outputs:

- `reports/quality_summary.md`
- `reports/suspicious_days.csv`
- `data/processed/daily_quality.parquet` (written by default; disable with `--no-parquet`)

Expected output shape:

```text
Input: data/processed/daily_sanitized.parquet
Total days: <N>
Strict labels: good=<x>% partial=<y>% bad=<z>%
Loose labels: good=<x>% partial=<y>% bad=<z>%
Suspicious days exported: <K>
Wrote reports/quality_summary.md
Wrote reports/suspicious_days.csv
Wrote data/processed/daily_quality.parquet
```

## Module-mode equivalent

Replace `garmin-analytics <command>` with:

```bash
PYTHONPATH=src python -m garmin_analytics <command>
```

## Typical run order

1. `garmin-analytics discover`
2. `garmin-analytics ingest-uds`
3. `garmin-analytics ingest-sleep`
4. `garmin-analytics build-daily`
5. `garmin-analytics sanitize`
6. `garmin-analytics quality`
7. Open notebooks (`jupyter lab`)
