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
- SQL query snapshots are exported locally to `reports/sql/duckdb/` and should not be committed.
- Monitoring parquet outputs are written under `data/processed/` and remain local.

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

Optional summary/full markdown modes:

```bash
garmin-analytics data-dictionary --markdown-mode both
```

Expected outputs:

- `reports/data_dictionary.csv`
- `reports/data_dictionary.md`
- `reports/data_dictionary_summary.md` (only in `summary`/`both` mode)

Expected output shape:

```text
Wrote reports/data_dictionary.csv
Wrote reports/data_dictionary.md
Wrote reports/data_dictionary_summary.md
```

### quality

Purpose: compute strict/loose day-quality labels and export diagnostics.

```bash
garmin-analytics quality
```

Expected outputs:

- `reports/quality_summary.md`
- `reports/suspicious_days.csv`
- `reports/suspicious_days_artifacts.csv`
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
Wrote reports/suspicious_days_artifacts.csv
Wrote data/processed/daily_quality.parquet
```

## Stage 1.5 commands (optional SQL layer)

### build-sql-mart

Purpose: materialize a local DuckDB analytics mart from Stage 1 outputs.

```bash
garmin-analytics build-sql-mart
```

Expected outputs:

- `data/processed/analytics.duckdb`
- tables: `fact_daily`, `fact_sleep`, `fact_quality`
- views: `vw_day_to_next_sleep`, `vw_weekday_profiles`, `vw_sleep_nights`

Expected output shape:

```text
DuckDB mart: data/processed/analytics.duckdb
Daily source: data/processed/daily_sanitized.parquet
Sleep source: data/processed/sleep_sanitized.parquet
Quality source: data/processed/daily_quality.parquet
Tables: fact_daily=<N>, fact_sleep=<N>, fact_quality=<N>
Views: vw_day_to_next_sleep=<N>, vw_weekday_profiles=<K>, vw_sleep_nights=<N>
```

### run-sql-portfolio

Purpose: execute portfolio SQL files under `sql/duckdb` and export CSV result snapshots.

```bash
garmin-analytics run-sql-portfolio
```

Expected outputs:

- `reports/sql/duckdb/*.csv`

Expected output shape:

```text
Executed SQL files: <M>
01_quality_mix.sql -> reports/sql/duckdb/01_quality_mix.csv (rows=<R>, cols=<C>)
...
```

## Stage 4 commands (optional monitoring extension)

### ingest-monitoring-fit

Purpose: decode Garmin monitoring FIT files into canonical minute-level heart-rate and stress parquet tables.

```bash
garmin-analytics ingest-monitoring-fit
```

Expected inputs:

- `data/raw/DI_CONNECT/DI-Connect-Uploaded-Files` by default
- override with `--input-dir`

Expected outputs:

- `data/processed/monitoring_heart_rate.parquet`
- `data/processed/monitoring_stress.parquet`

Current refreshed run shape:

```text
FIT files seen: 10,236
Monitoring files decoded: 3,562
Decode errors skipped: 0
Heart-rate rows: 675,325
Stress rows: 889,323
Wrote data/processed/monitoring_heart_rate.parquet
Wrote data/processed/monitoring_stress.parquet
```

### build-semantic-windows

Purpose: build sleep-aware semantic windows from the processed sleep table, with local UTC offset metadata from daily aggregate tables when available.

```bash
garmin-analytics build-semantic-windows
```

Expected inputs:

- `data/processed/sleep.parquet`
- `data/processed/daily_uds.parquet` by default, falling back to `data/processed/daily.parquet`

Expected outputs:

- `data/processed/semantic_sleep_windows.parquet`

Current refreshed run shape:

```text
Wrote 556 rows to data/processed/semantic_sleep_windows.parquet
Daily offset source: data/processed/daily_uds.parquet
Rows with local UTC offset: 556
```

### build-monitoring-features

Purpose: build the foundation sleep/wake monitoring feature table and aggregate summary report from minute-level HR/stress plus semantic windows.

```bash
garmin-analytics build-monitoring-features
```

Expected inputs:

- `data/processed/monitoring_heart_rate.parquet`
- `data/processed/monitoring_stress.parquet`
- `data/processed/semantic_sleep_windows.parquet`

Expected outputs:

- `data/processed/monitoring_daily_features.parquet`
- `reports/monitoring_foundation_summary.md`

Current refreshed run shape:

```text
Wrote 556 rows to data/processed/monitoring_daily_features.parquet
Wrote reports/monitoring_foundation_summary.md
```

### build-monitoring-datasets

Purpose: build the monitoring quality index, compact core feature table, cleaned full feature table, and feature catalog.

```bash
garmin-analytics build-monitoring-datasets
```

Expected inputs:

- `data/processed/monitoring_heart_rate.parquet`
- `data/processed/monitoring_stress.parquet`
- `data/processed/semantic_sleep_windows.parquet`

Expected outputs:

- `data/processed/monitoring_quality_index.parquet`
- `data/processed/monitoring_features_core_v0.parquet`
- `data/processed/monitoring_features_full_v0.parquet`
- `reports/monitoring_quality_summary.md`
- `reports/monitoring_core_features_summary.md`
- `reports/monitoring_features_full_summary.md`
- `reports/monitoring_features_full_catalog.csv`
- `reports/monitoring_features_full_catalog.md`

Current refreshed run shape:

```text
Wrote 589 quality rows to data/processed/monitoring_quality_index.parquet
Wrote 589 core rows and 93 columns to data/processed/monitoring_features_core_v0.parquet
Wrote 589 full rows and 243 columns to data/processed/monitoring_features_full_v0.parquet
Wrote reports/monitoring_quality_summary.md
Wrote reports/monitoring_core_features_summary.md
Wrote reports/monitoring_features_full_summary.md
Wrote reports/monitoring_features_full_catalog.csv
Wrote reports/monitoring_features_full_catalog.md
```

Notes:

- Join `monitoring_quality_index.parquet` to feature tables on `analysis_window_id` before modeling.
- `modeling_recovery_v0_eligible` is the baseline recovery-modeling eligibility flag.
- Numeric stress features use raw Garmin stress `0..100`; HR-confirmed raw `-2` contributes only to active/status semantics.

### build-stage4-modeling-frame

Purpose: build the shared Stage 4 `day D -> next sleep` modeling frame, feature-set catalog, and audit summary before model-specific notebooks run.

```bash
garmin-analytics build-stage4-modeling-frame
```

Expected inputs:

- `data/processed/monitoring_quality_index.parquet`
- `data/processed/monitoring_features_core_v0.parquet`
- `data/processed/monitoring_features_full_v0.parquet`
- `reports/monitoring_features_full_catalog.csv`
- `data/processed/sleep_sanitized.parquet` or `data/processed/sleep.parquet`
- `data/processed/daily_sanitized.parquet` or `data/processed/daily.parquet`
- `data/processed/daily_quality.parquet`

Expected outputs:

- `data/processed/stage4_sleep_modeling_frame.parquet`
- `reports/stage4_sleep_modeling_frame_summary.md`
- `reports/stage4_sleep_modeling_feature_sets.csv`
- `reports/stage4_sleep_modeling_feature_sets.md`

Current refreshed run shape:

```text
Wrote 589 rows and 295 columns to data/processed/stage4_sleep_modeling_frame.parquet
Split train: rows=330 eligible=330 primary_target=330
Split valid: rows=71 eligible=71 primary_target=71
Split test: rows=71 eligible=71 primary_target=71
Split not_eligible_or_missing_target: rows=117 eligible=0 primary_target=52
Feature set aggregate_stage3_baseline: 33 columns
Feature set monitoring_core_wake_pre_sleep: 56 columns
Feature set monitoring_full_wake_pre_sleep: 123 columns
Feature set aggregate_plus_monitoring_full: 138 columns
```

Notes:

- The primary continuous target is next-sleep `avgSleepStress`.
- The default split is `past_random_valid_future_test`: future test block, random train/validation split inside earlier history.
- The command builds the modeling contract only; model fitting happens in later notebooks.

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
7. `garmin-analytics ingest-monitoring-fit` (optional Stage 4)
8. `garmin-analytics build-semantic-windows` (optional Stage 4)
9. `garmin-analytics build-monitoring-features` (optional Stage 4)
10. `garmin-analytics build-monitoring-datasets` (optional Stage 4)
11. `garmin-analytics build-stage4-modeling-frame` (optional Stage 4)
12. `garmin-analytics build-sql-mart` (optional SQL layer)
13. `garmin-analytics run-sql-portfolio` (optional SQL layer)
14. Open notebooks (`jupyter lab`)
