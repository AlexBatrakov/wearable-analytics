# Stage 1 — Sanitize, Data Dictionary, and Quality

Stage 1 is the privacy and data-quality gate between ingestion and EDA.

## Commands

```bash
garmin-analytics sanitize
garmin-analytics data-dictionary
garmin-analytics quality
```

Alternative module mode:

```bash
PYTHONPATH=src python -m garmin_analytics sanitize
PYTHONPATH=src python -m garmin_analytics data-dictionary
PYTHONPATH=src python -m garmin_analytics quality
```

## Outputs

Sanitize:
- `data/processed/daily_sanitized.parquet`
- `data/processed/daily_uds_sanitized.parquet`
- `data/processed/sleep_sanitized.parquet`
- `data/processed/sanitize_report.json`

Data dictionary:
- `reports/data_dictionary.csv`
- `reports/data_dictionary.md`

Quality:
- `reports/quality_summary.md`
- `reports/suspicious_days.csv`
- `data/processed/daily_quality.parquet` (written by default; disable with `--no-parquet`)

## Current Stage 1 metrics

- rows: **580**
- date range: **2023-05-26 to 2026-02-05**
- strict labels: **good 90.52%, partial 3.79%, bad 5.69%**
- loose labels: **good 93.45%, partial 0.86%, bad 5.69%**
- corrupted stress-only days: **21 (3.62%)**

## Interpretation

- Strict labels emphasize robust day completeness.
- Loose labels allow borderline but still usable days.
- `corrupted_stress_only_day` flags artifact-like records with near-full-day stress but missing corroborating signals; these are forced to `bad`.

## Exit criteria

Proceed to Stage 2 after:
- sanitize outputs are generated,
- dictionary reports are available,
- quality summary and suspicious-day diagnostics are reviewed.

For command options and thresholds, see [CLI](cli.md).
