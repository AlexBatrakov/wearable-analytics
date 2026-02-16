# Scripts

Helper utilities for schema exploration and data previews. These are optional and not required for the ingestion pipeline.

## Notes
- Scripts write outputs only to data/interim, which is ignored by git.
- Preview outputs scrub identifier-like fields (uuid, userProfilePk, deviceId).

## Available scripts
- inspect_uds_schema.py: summarize top-level and nested fields in UDS exports.
- make_sleep_previews.py: create human-readable sleep previews under data/interim.
