# Public Demo

This repository includes a tiny public demo sample so the Stage 1 workflow can be exercised without private Garmin exports.

The demo sample is:
- schema-aligned with the sanitized daily table
- safe to publish
- intentionally small and illustrative rather than analytically representative

## What the public demo covers

The public demo supports:
- installing a small `daily_sanitized.parquet`
- generating the data dictionary reports
- generating quality labels and suspicious-day reports

It does **not** try to reproduce the full local workflow:
- no raw Garmin export ingestion
- no private `data/raw/DI_CONNECT` dependency
- no claim that the tiny sample is suitable for notebook-driven findings

## Setup

Create the demo parquet under `data/processed/`:

```bash
PYTHONPATH=src .venv/bin/python scripts/setup_public_demo.py
```

This writes:
- `data/processed/daily_sanitized.parquet`

## Run the public Stage 1 slice

```bash
garmin-analytics data-dictionary --markdown-mode both
garmin-analytics quality
```

Expected outputs:
- `reports/data_dictionary.csv`
- `reports/data_dictionary.md`
- `reports/data_dictionary_summary.md`
- `reports/quality_summary.md`
- `reports/suspicious_days.csv`
- `reports/suspicious_days_artifacts.csv`
- `data/processed/daily_quality.parquet`

## Privacy note

The committed sample is a tiny public demo artifact, not a raw Garmin export and not a dump of the private local dataset. It exists only to make the repository runnable for external reviewers at a minimal level.
