# Scripts

Helper utilities for schema exploration and data previews. These are optional and not required for the ingestion pipeline.

## Notes
- Scripts write outputs only to data/interim, which is ignored by git.
- Preview scripts scrub identifier-like fields (uuid, userProfilePk/userProfilePK, deviceId).
- Some older preview files may be stale and may need regeneration.
- `make_*_previews.py` scripts import `garmin_analytics`, so run them with `PYTHONPATH=src` or after `pip install -e .`.

## Script types

### Preview generators (human-readable pretty JSON)

- `make_uds_previews.py`: create scrubbed UDS record previews under `data/interim/uds_previews`
- `make_sleep_previews.py`: create scrubbed sleep record previews under `data/interim/sleep_previews`

Examples:

```bash
PYTHONPATH=src .venv/bin/python scripts/make_uds_previews.py
PYTHONPATH=src .venv/bin/python scripts/make_sleep_previews.py
```

Both scripts write:
- a single-record preview (`*_first_record.pretty.json`)
- a multi-record preview (`*_first_3_records.pretty.json` by default)

### Schema inspector (console summary, no preview files)

- `inspect_uds_schema.py`: summarizes UDS top-level keys, nested dict subkeys, and nested list item schemas to help design/validate ingestion flattening

Example:

```bash
python3 scripts/inspect_uds_schema.py --top 30
```

## Why keep `inspect_uds_schema.py` if preview scripts exist?

Preview files help you read a few example records manually.

`inspect_uds_schema.py` solves a different problem:
- aggregate schema coverage across *all* UDS files
- field presence frequencies (`% rows`)
- nested list item key inventory (e.g. `allDayStress.aggregatorList`)
- quick detection of schema drift or unexpected keys

In practice:
- use `make_*_previews.py` for human inspection of example records
- use `inspect_uds_schema.py` for parser design/audits and coverage checks
