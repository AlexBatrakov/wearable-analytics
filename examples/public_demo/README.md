# Public Demo Sample

This folder contains a tiny public demo dataset for the repository.

Important properties:
- it is schema-aligned with the sanitized daily table used in Stage 1
- it is safe to publish
- it is intentionally tiny and only meant to exercise the public workflow

What it is for:
- installing a runnable demo dataset into `data/processed/daily_sanitized.parquet`
- running `garmin-analytics data-dictionary`
- running `garmin-analytics quality`

What it is not for:
- full end-to-end raw Garmin ingestion
- serious EDA conclusions
- benchmark-quality modeling

Install it with:

```bash
PYTHONPATH=src .venv/bin/python scripts/setup_public_demo.py
```

Then run:

```bash
garmin-analytics data-dictionary --markdown-mode both
garmin-analytics quality
```
