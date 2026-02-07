from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console

from .ingest.sleep import parse_sleep_files
from .ingest.uds import parse_uds_files
from .util.io import (
    ensure_dir,
    get_export_dir,
    get_interim_dir,
    get_processed_dir,
    get_repo_root,
    list_sleep_files,
    list_uds_files,
)

app = typer.Typer(add_completion=False)
console = Console()


def _safe_relpath(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _info(message: str) -> None:
    """Log an informational message."""
    console.print(message)


@app.command("discover")
def discover() -> None:
    """Discover available Garmin export files and write inventory CSV."""
    export_dir = get_export_dir()
    uds_files = list_uds_files(export_dir)
    sleep_files = list_sleep_files(export_dir)

    _info(f"Export dir: {export_dir}")
    _info(f"Found UDS files: {len(uds_files)}")
    _info(f"Found sleep files: {len(sleep_files)}")

    rows: list[dict[str, object]] = []
    repo_root = get_repo_root()
    for path in uds_files:
        stat = path.stat()
        rows.append(
            {
                "type": "uds",
                "path": _safe_relpath(path, repo_root),
                "size_bytes": stat.st_size,
                "modified_utc": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
            }
        )
    for path in sleep_files:
        stat = path.stat()
        rows.append(
            {
                "type": "sleep",
                "path": _safe_relpath(path, repo_root),
                "size_bytes": stat.st_size,
                "modified_utc": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
            }
        )

    inventory_path = get_interim_dir() / "inventory.csv"
    ensure_dir(inventory_path.parent)
    pd.DataFrame(rows).to_csv(inventory_path, index=False)
    _info(f"Wrote inventory: {inventory_path}")


@app.command("ingest-uds")
def ingest_uds() -> None:
    """Parse UDSFile_*.json and write daily_uds.parquet."""
    export_dir = get_export_dir()
    uds_files = list_uds_files(export_dir)
    if not uds_files:
        _info("No UDS files found.")
        raise typer.Exit(code=1)

    df = parse_uds_files(uds_files)
    output_path = get_processed_dir() / "daily_uds.parquet"
    ensure_dir(output_path.parent)
    df.to_parquet(output_path, index=False, engine="pyarrow")
    _info(f"Wrote {len(df)} rows to {output_path}")


@app.command("ingest-sleep")
def ingest_sleep() -> None:
    """Parse *_sleepData.json and write sleep.parquet."""
    export_dir = get_export_dir()
    sleep_files = list_sleep_files(export_dir)
    if not sleep_files:
        _info("No sleep files found.")
        raise typer.Exit(code=1)

    df = parse_sleep_files(sleep_files)
    output_path = get_processed_dir() / "sleep.parquet"
    ensure_dir(output_path.parent)
    df.to_parquet(output_path, index=False, engine="pyarrow")
    _info(f"Wrote {len(df)} rows to {output_path}")


@app.command("build-daily")
def build_daily() -> None:
    """Merge daily UDS and sleep tables on calendarDate."""
    processed_dir = get_processed_dir()
    uds_path = processed_dir / "daily_uds.parquet"
    sleep_path = processed_dir / "sleep.parquet"

    if not uds_path.exists():
        _info(f"Missing input: {uds_path}")
        raise typer.Exit(code=1)
    if not sleep_path.exists():
        _info(f"Missing input: {sleep_path}")
        raise typer.Exit(code=1)

    uds_df = pd.read_parquet(uds_path)
    sleep_df = pd.read_parquet(sleep_path)

    for df in (uds_df, sleep_df):
        if "calendarDate" in df.columns:
            df["calendarDate"] = pd.to_datetime(df["calendarDate"], errors="coerce").dt.normalize()

    daily = pd.merge(uds_df, sleep_df, on="calendarDate", how="left", suffixes=("", "_sleep"))
    output_path = processed_dir / "daily.parquet"
    daily.to_parquet(output_path, index=False, engine="pyarrow")
    _info(f"Wrote {len(daily)} rows to {output_path}")
