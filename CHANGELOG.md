# Changelog

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
  - optional data/processed/daily_quality.parquet
- Added synthetic tests for sanitize, data dictionary, and quality labeling.
- Updated README with Stage 1 usage and reproducibility commands.
