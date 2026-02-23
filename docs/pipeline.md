# Pipeline

This project follows:
**discover → ingest → build → sanitize → quality → EDA**

## Inputs

Place Garmin export files locally under `data/raw/DI_CONNECT` (or set `GARMIN_EXPORT_DIR`).
Input JSON is nested; Stage 0 flattens and normalizes it into day-level parquet tables used by later stages.

## Why parquet

- Preserves dtypes and timestamps better than ad-hoc CSV workflows.
- Improves read/filter/join speed for quality checks and notebook EDA.

## Core parquet outputs (Stage 0)

- `data/processed/daily_uds.parquet`
- `data/processed/sleep.parquet`
- `data/processed/daily.parquet`

Build order:
1. `discover` inventories source files.
2. `ingest-uds` parses UDS records into `daily_uds.parquet`.
3. `ingest-sleep` parses sleep records into `sleep.parquet`.
4. `build-daily` merges daily UDS + sleep into `daily.parquet`.

Why this stage exists:
- Converts heterogeneous raw JSON into consistent analysis-ready tables.
- Provides clear file-level checkpoints before privacy/quality logic.
- Produces a stable baseline (`daily.parquet`) for Stage 1.

## Privacy gate and quality (Stage 1)

1. `sanitize` creates privacy-safe tables:
   - `data/processed/daily_sanitized.parquet`
   - `data/processed/daily_uds_sanitized.parquet`
   - `data/processed/sleep_sanitized.parquet`
   - `data/processed/sanitize_report.json`
2. `data-dictionary` writes column-level inventory reports:
   - `reports/data_dictionary.csv`
   - `reports/data_dictionary.md`
   - `reports/data_dictionary_summary.md` (optional summary mode)
3. `quality` writes quality diagnostics:
   - `reports/quality_summary.md`
   - `reports/suspicious_days.csv`
   - `reports/suspicious_days_artifacts.csv` (artifact-focused ranking)
   - `data/processed/daily_quality.parquet` (written by default; disable with `--no-parquet`)

Why this stage exists:
- Enforces a privacy-first boundary through sanitized outputs.
- Documents schema/semantics through data-dictionary reports.
- Quantifies day-level analysis readiness (signal coverage) via strict/loose quality labels.

## EDA flow (Stage 2)

- `notebooks/01_eda_prepare.ipynb` defines the Stage 2 analysis contract, builds canonical EDA slices, and provides a coverage-aware overview (retention, label distribution, monthly signal coverage, day-level calendar heatmap).
- `notebooks/02_eda_timeseries.ipynb` explores trends, anomalies, and time-series behavior.
- `notebooks/03_eda_distributions.ipynb` is the main in-progress notebook for distributions, relationships, artifact review, and findings/hypotheses.

Why this stage exists:
- Turns validated tables into interpretable patterns and decisions.
- Separates data prep concerns from exploratory plotting workflows.
- Produces candidate insights for follow-on analysis and reporting.

See stage pages for command-level detail:
- [Stage 0](stage0.md)
- [Stage 1](stage1.md)
- [Stage 2](stage2.md)
