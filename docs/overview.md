# Overview

Garmin Wearable Analytics is a privacy-first local pipeline for Garmin exports.
It turns raw files into curated parquet datasets, applies sanitization and quality checks, and supports reproducible EDA.

Raw exports and `data/` artifacts are local-only.
Sanitized outputs are the default boundary for analysis and sharing.

## Stage map

- [Stage 0](stage0.md): raw discovery + ingestion + build parquet outputs
- [Stage 1](stage1.md): sanitize + data dictionary + quality labeling
- [Stage 2](stage2.md): EDA notebooks and interpretation

## Documentation map

- [Pipeline flow](pipeline.md)
- [CLI commands](cli.md)
- [EDA guide](eda.md)
- [Privacy rules](privacy.md)
- [Stage 0 details](stage0.md)
- [Stage 1 details](stage1.md)
- [Stage 2 details](stage2.md)

## Outputs at a glance

- **Core parquet (Stage 0)**
	- `data/processed/daily_uds.parquet`
	- `data/processed/sleep.parquet`
	- `data/processed/daily.parquet`
- **Sanitized parquet (Stage 1)**
	- `data/processed/daily_sanitized.parquet`
	- `data/processed/daily_uds_sanitized.parquet`
	- `data/processed/sleep_sanitized.parquet`
	- `data/processed/sanitize_report.json`
- **Reports / diagnostics (Stage 1)**
	- `reports/data_dictionary.md`
	- `reports/data_dictionary_summary.md` (optional summary mode)
	- `reports/quality_summary.md`
	- `reports/suspicious_days_artifacts.csv`
	- `reports/suspicious_days.csv`
- **Notebooks (Stage 2)**
	- `notebooks/01_eda_prepare.ipynb`
	- `notebooks/02_eda_timeseries.ipynb`
	- `notebooks/03_eda_distributions.ipynb` (in progress: distributions + relationships + artifact review + findings)

## Quick run

```bash
garmin-analytics discover
garmin-analytics ingest-uds && garmin-analytics ingest-sleep && garmin-analytics build-daily
garmin-analytics sanitize && garmin-analytics quality
jupyter lab
```

For command flags/options and detailed output shapes, see [CLI commands](cli.md).
