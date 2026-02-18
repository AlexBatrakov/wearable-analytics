# Garmin Wearable Analytics

Privacy-first Garmin data analytics pipeline for local exports.
It discovers raw files, ingests and builds parquet datasets, applies sanitization and data quality checks, and supports EDA with notebooks.
The focus is reproducible analytics without exposing personal identifiers.

## For recruiters: Skills demonstrated

- Python packaging + CLI workflows (`typer`, modular pipeline commands)
- Robust data ingestion from nested JSON exports (UDS + sleep)
- Parquet-first analytics tables (`daily_uds.parquet`, `sleep.parquet`, `daily.parquet`)
- Privacy gate via sanitization before analysis/sharing
- Data inventory and quality labeling (strict/loose quality rules)
- EDA design for time-series health signals (prepare + timeseries notebooks)
- Test-backed iteration across ingestion, sanitize, quality, and reporting

## If you have 60 seconds

- [Project overview](docs/overview.md)
- [Timeseries notebook](notebooks/02_eda_timeseries.ipynb)
- [Privacy rules](docs/privacy.md)

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

Primary CLI mode (console script):

```bash
garmin-analytics sanitize
garmin-analytics quality
```

Alternative module mode:

```bash
PYTHONPATH=src python -m garmin_analytics sanitize
PYTHONPATH=src python -m garmin_analytics quality
```

Open notebooks:

```bash
jupyter lab
```

## Results snapshot

- rows: **580**
- date range: **2023-05-26 to 2026-02-05**
- strict labels: **good 90.52%, partial 3.79%, bad 5.69%**
- loose labels: **good 93.45%, partial 0.86%, bad 5.69%**
- corrupted stress-only days: **21 (3.62%)**

## Docs

- [Overview](docs/overview.md)
- [Pipeline](docs/pipeline.md)
- [CLI](docs/cli.md)
- [EDA](docs/eda.md)
- [Stage 0](docs/stage0.md)
- [Stage 1](docs/stage1.md)
- [Stage 2](docs/stage2.md)
- [Privacy](docs/privacy.md)

## Privacy

Raw Garmin exports stay local and must never be committed; use sanitized outputs for analysis and sharing. See [docs/privacy.md](docs/privacy.md).