# Garmin Wearable Analytics (v1)

This project ingests Garmin export data from a local folder and produces normalized parquet tables for daily summaries and sleep metrics.

## Privacy & data safety
- Raw Garmin exports stay inside the repo for local convenience but are **never committed**.
- The data folder is ignored via .gitignore.
- See the pre-commit hook instructions below to add an extra safety net.

## Project structure
- Source code: src/garmin_analytics
- Raw data (local only): data/raw/DI_CONNECT
- Intermediate outputs (ignored): data/interim
- Processed outputs (ignored): data/processed

## Quickstart (macOS, Python 3.11+)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Set the export directory (optional):
```bash
export GARMIN_EXPORT_DIR="data/raw/DI_CONNECT"
```
If GARMIN_EXPORT_DIR is not set, the default is data/raw/DI_CONNECT.

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

## Developer notes
- Run tests: `pytest`
- Add a new data source: create a parser under src/garmin_analytics/ingest and wire it into cli.py

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