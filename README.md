# Garmin Wearable Analytics

Ingest Garmin export data from a local folder and produce normalized parquet tables for daily summaries and sleep metrics.

## Privacy & data safety
- Raw Garmin exports stay local and are **never committed**.
- The data folders are ignored via .gitignore.
- Use the `sanitize` command before analysis or sharing.
- See the pre-commit hook instructions below for an extra safety net.

## Project structure
- Source code: src/garmin_analytics
- Raw data (local only): data/raw/DI_CONNECT
- Intermediate outputs (ignored): data/interim
- Processed outputs (ignored): data/processed

## Setup (macOS, Python 3.11+)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Optional dev/EDA dependencies:
```bash
pip install -r requirements-dev.txt
```

Environment configuration:
- Copy .env.example to .env (optional) and set `GARMIN_EXPORT_DIR`.
- Or export `GARMIN_EXPORT_DIR` in your shell.

Set the export directory (optional):
```bash
export GARMIN_EXPORT_DIR="data/raw/DI_CONNECT"
```
If GARMIN_EXPORT_DIR is not set, the default is data/raw/DI_CONNECT.

Check CLI help:
```bash
PYTHONPATH=src python -m garmin_analytics --help
```

Run the CLI (module mode):
```bash
PYTHONPATH=src python -m garmin_analytics discover
PYTHONPATH=src python -m garmin_analytics ingest-uds
PYTHONPATH=src python -m garmin_analytics ingest-sleep
PYTHONPATH=src python -m garmin_analytics build-daily
```

Run the CLI (console script):
```bash
garmin-analytics discover
garmin-analytics ingest-uds
garmin-analytics ingest-sleep
garmin-analytics build-daily
```

## Outputs
- data/processed/daily_uds.parquet
- data/processed/sleep.parquet
- data/processed/daily.parquet

## Sanitized outputs (safe for analysis/sharing)
The processed parquet tables may contain personal identifier columns and GUID-like values.

Use the `sanitize` command to create "safe" copies with identifier columns removed:
```bash
PYTHONPATH=src python -m garmin_analytics sanitize
```

This writes (if inputs exist):
- data/processed/daily_sanitized.parquet
- data/processed/daily_uds_sanitized.parquet
- data/processed/sleep_sanitized.parquet
- data/processed/sanitize_report.json

For analysis notebooks and sharing derived results, prefer the `*_sanitized.parquet` tables.

## Developer notes
- Run tests: `python -m pytest` (requires requirements-dev.txt)
- Add a new data source: create a parser under src/garmin_analytics/ingest and wire it into cli.py

## Scripts
Helper utilities for schema exploration and previews live under scripts/. They are optional and write only to data/interim (ignored by git). See scripts/README.md.

## Stage 1: Data dictionary
Generate a column-level data dictionary (CSV + Markdown) from the aggregated daily table:
```bash
PYTHONPATH=src python -m garmin_analytics data-dictionary
```

## Stage 1.2: Data quality
Label days as good/partial/bad with strict and loose thresholds, and export suspicious-day diagnostics:
```bash
PYTHONPATH=src python -m garmin_analytics quality
```

Defaults:
- strict valid day: `quality_score >= 4`
- loose valid day: `quality_score >= 3`

Outputs:
- `reports/quality_summary.md`
- `reports/suspicious_days.csv`
- `data/processed/daily_quality.parquet` (optional; disable with `--no-parquet`)

## Stage 1 Results
Stage 1 (data inventory + data quality) is complete.

Headline metrics from current reports:
- dataset rows: 580
- date range: 2023-05-26 to 2026-02-05
- strict labels: good 90.52%, partial 3.79%, bad 5.69%
- loose labels: good 93.45%, partial 0.86%, bad 5.69%
- corrupted stress-only days: 21 (3.62%)

Interpretation note:
- `corrupted_stress_only_day` marks artifact-like days with near-24h stress duration and no HR/sleep/body battery/steps signals; these are forced to `bad`.

Reproducible commands:
```bash
PYTHONPATH=src python -m garmin_analytics data-dictionary
PYTHONPATH=src python -m garmin_analytics quality
```

Local output note:
- parquet outputs under `data/processed` are local and gitignored.

## Data safety hook
See docs/precommit_hook.md for local pre-commit hook instructions.

## CLI commands and expected output
### discover
```text
Export dir: data/raw/DI_CONNECT
Found UDS files: <N>
Found sleep files: <M>
Wrote inventory: data/interim/inventory.csv
```

### ingest-uds
```text
Wrote <N> rows to data/processed/daily_uds.parquet
```

### ingest-sleep
```text
Wrote <N> rows to data/processed/sleep.parquet
```

### build-daily
```text
Wrote <N> rows to data/processed/daily.parquet
```

### sanitize
```text
Sanitized daily: <rows> rows, <before> → <after> cols (dropped <k>)
Sanitized daily_uds: ...
Sanitized sleep: ...
Wrote report: data/processed/sanitize_report.json
```

## Pre-commit hook (extra safety)
Create a local git pre-commit hook to block committing Garmin exports:

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh

if git diff --cached --name-only | grep -E '^(data/raw/|.*DI_CONNECT/)' >/dev/null; then
	echo "Error: Garmin export data cannot be committed. Remove files from staging."
	exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

Note: git hooks are not versioned by default. Each collaborator should create this hook locally.