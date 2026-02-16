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
The processed parquet tables may contain personal identifiers (e.g. internal keys like `userProfilePK`, UUID/GUID-like values).

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