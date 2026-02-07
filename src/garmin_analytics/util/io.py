from __future__ import annotations

import os
from pathlib import Path

import orjson
from dotenv import load_dotenv

load_dotenv()


def get_repo_root() -> Path:
    """Return repository root based on this file location."""
    return Path(__file__).resolve().parents[3]


def get_data_dir() -> Path:
    """Return the data directory path."""
    return get_repo_root() / "data"


def get_interim_dir() -> Path:
    """Return the interim data directory path."""
    return get_data_dir() / "interim"


def get_processed_dir() -> Path:
    """Return the processed data directory path."""
    return get_data_dir() / "processed"


def get_export_dir() -> Path:
    """Return the Garmin export directory, honoring GARMIN_EXPORT_DIR."""
    default_dir = get_data_dir() / "raw" / "DI_CONNECT"
    return Path(os.getenv("GARMIN_EXPORT_DIR", str(default_dir)))


def ensure_dir(path: Path) -> None:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def list_uds_files(export_dir: Path | None = None) -> list[Path]:
    """List UDSFile_*.json under the export directory."""
    base = (export_dir or get_export_dir()) / "DI-Connect-Aggregator"
    return sorted(base.glob("UDSFile_*.json"))


def list_sleep_files(export_dir: Path | None = None) -> list[Path]:
    """List *_sleepData.json under the export directory."""
    base = (export_dir or get_export_dir()) / "DI-Connect-Wellness"
    return sorted(base.glob("*_sleepData.json"))


def read_json(path: Path) -> object:
    """Read a JSON file using orjson."""
    return orjson.loads(path.read_bytes())
