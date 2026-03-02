# Changelog

## Unreleased

- Showcase packaging for applications:
  - rewrote `README.md` into a recruiter-facing landing page
  - added `docs/case_study.md` as a concise portfolio narrative
  - curated showcase figures under `docs/img/` for coverage, weekly behavior, and day-to-night recovery
  - repositioned technical docs as second-layer depth behind the case study
- Stage 2 (EDA) completed:
  - split analysis into `03_eda_distributions.ipynb` and `04_eda_relationships.ipynb`
  - finalized relationship analysis, artifact review, and Stage 2 synthesis
- Stage 2 (EDA): strengthened `notebooks/01_eda_prepare.ipynb` as a quality-aware entry point:
  - explicit analysis contract (grain, slice semantics, quality-filter usage)
  - canonical slice definitions and narrative guidance for downstream notebooks
  - coverage-aware overview visuals (retention, strict vs loose labels, monthly key-signal coverage)
  - GitHub-style day-level coverage/quality calendar heatmap with artifact highlighting
- Docs: synced Stage 2 public docs/README with current Block A+B status and hybrid EDA workflow.

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
