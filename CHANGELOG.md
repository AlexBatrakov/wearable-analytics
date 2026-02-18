# Changelog

## Unreleased

- Docs: polished overview, pipeline, CLI, privacy, and Stage 0/1/2 + EDA pages for consistent run flow, outputs, and interpretation guidance.

## Stage 0 (Discovery + Ingestion + Build)

- Implemented discovery and ingestion of Garmin exports:
  - discover → ingest-uds → ingest-sleep → build-daily
- Built core parquet tables:
  - data/processed/daily_uds.parquet
  - data/processed/sleep.parquet
  - data/processed/daily.parquet

## Stage 1 (Data Inventory + Data Quality)

- Added sleep/UDS ingestion hardening and expanded flattened metrics for analysis.
- Added sanitize pipeline and CLI command to produce safe processed outputs:
  - daily_sanitized.parquet
  - daily_uds_sanitized.parquet
  - sleep_sanitized.parquet
  - sanitize_report.json
- Implemented data dictionary generator and CLI command:
  - reports/data_dictionary.csv
  - reports/data_dictionary.md
- Implemented day quality labeling and CLI command:
  - strict/loose quality labels and validity flags
  - corrupted_stress_only_day override for artifact-like days
  - reports/quality_summary.md
  - reports/suspicious_days.csv
  - writes data/processed/daily_quality.parquet by default (disable via –no-parquet)
- Added synthetic tests for sanitize, data dictionary, and quality labeling.
- Updated README with Stage 1 usage and reproducibility commands.

## Stage 2 (EDA)

- Added EDA notebooks:
  - notebooks/01_eda_prepare.ipynb
  - notebooks/02_eda_timeseries.ipynb
- Added SAVE_FIGS toggle and local figure export to reports/figures (gitignored).
- Added basic EDA helpers / derived features for daily slices.