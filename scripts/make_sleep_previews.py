from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from garmin_analytics.util.io import ensure_dir, get_export_dir, get_interim_dir, list_sleep_files, read_json


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ["sleepData", "dailySleep", "sleep"]:
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        # Some exports might store a single record as a dict
        if "calendarDate" in payload or "calendarDateStr" in payload:
            return [payload]
    return []


def _is_identifier_key(key: str) -> bool:
    lowered = key.lower()
    return "userprofilepk" in lowered or "uuid" in lowered or "deviceid" in lowered


def _sanitize_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            key: _sanitize_obj(value)
            for key, value in obj.items()
            if not _is_identifier_key(key)
        }
    if isinstance(obj, list):
        return [_sanitize_obj(item) for item in obj]
    return obj


def _write_pretty(path: Path, obj: Any) -> None:
    safe_obj = _sanitize_obj(obj)
    path.write_text(json.dumps(safe_obj, indent=2, sort_keys=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create human-readable previews for Garmin sleep exports")
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=None,
        help="Garmin export directory (defaults to GARMIN_EXPORT_DIR or data/raw/DI_CONNECT)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory for previews (default: data/interim/sleep_previews)",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=3,
        help="How many records to include in the multi-record preview (default: 3)",
    )
    args = parser.parse_args()

    export_dir = args.export_dir or get_export_dir()
    paths = list_sleep_files(export_dir)
    if not paths:
        raise SystemExit(f"No sleep files found under: {export_dir}")

    payload = read_json(paths[0])
    records = _extract_records(payload)
    if not records:
        raise SystemExit(f"No sleep records found inside: {paths[0]}")

    out_dir = args.out_dir or (get_interim_dir() / "sleep_previews")
    ensure_dir(out_dir)

    _write_pretty(out_dir / "sleep_first_record.pretty.json", records[0])
    _write_pretty(out_dir / f"sleep_first_{args.max_records}_records.pretty.json", records[: args.max_records])

    print(f"Input file: {paths[0]}")
    print(f"Records in file: {len(records)}")
    print(f"Wrote: {out_dir / 'sleep_first_record.pretty.json'}")
    print(f"Wrote: {out_dir / f'sleep_first_{args.max_records}_records.pretty.json'}")


if __name__ == "__main__":
    main()
