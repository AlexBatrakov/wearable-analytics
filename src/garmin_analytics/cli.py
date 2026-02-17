from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console

from .ingest.sleep import parse_sleep_files
from .ingest.uds import parse_uds_files
from .quality.quality import (
    QualityConfig,
    apply_quality_labels,
    build_quality_summary_markdown,
    build_suspicious_days,
    write_quality_outputs,
)
from .reports.data_dictionary import DictionaryOptions, build_data_dictionary, write_dictionary_reports
from .sanitize import sanitize_parquet_file, write_sanitize_report
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


@app.command("sanitize")
def sanitize(
    input: Path = typer.Option(
        None,
        "--input",
        help="Primary input parquet (default: data/processed/daily.parquet)",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        help="Primary output parquet (default: data/processed/daily_sanitized.parquet)",
    ),
    report: Path = typer.Option(
        None,
        "--report",
        help="Write aggregated sanitize report JSON (default: data/processed/sanitize_report.json)",
    ),
    inplace: bool = typer.Option(
        False,
        "--inplace",
        help="Replace input files in-place (overwrites the processed parquets)",
    ),
    allow_identifiers: bool = typer.Option(
        False,
        "--allow-identifiers",
        help="Dangerous: allow identifier-like columns to remain (not recommended)",
    ),
) -> None:
    """Create sanitized parquet outputs without personal identifiers."""
    processed_dir = get_processed_dir()

    default_daily_in = processed_dir / "daily.parquet"
    default_daily_out = processed_dir / "daily_sanitized.parquet"
    default_report = processed_dir / "sanitize_report.json"

    primary_in = input or default_daily_in
    if not primary_in.exists():
        _info(f"Missing input: {primary_in}")
        raise typer.Exit(code=1)

    primary_out = primary_in if inplace else (output or default_daily_out)
    report_path = report or default_report

    # Always try to sanitize the standard processed tables if they exist.
    candidates: list[tuple[str, Path, Path]] = []
    seen_inputs: set[Path] = set()

    def _add(label: str, in_path: Path, out_path: Path) -> None:
        if in_path in seen_inputs:
            return
        seen_inputs.add(in_path)
        candidates.append((label, in_path, out_path))

    _add("daily", primary_in, primary_out)

    uds_in = processed_dir / "daily_uds.parquet"
    sleep_in = processed_dir / "sleep.parquet"
    if uds_in.exists():
        uds_out = uds_in if inplace else processed_dir / "daily_uds_sanitized.parquet"
        _add("daily_uds", uds_in, uds_out)
    if sleep_in.exists():
        sleep_out = sleep_in if inplace else processed_dir / "sleep_sanitized.parquet"
        _add("sleep", sleep_in, sleep_out)

    aggregated: dict[str, object] = {"files": {}}

    for label, in_path, out_path in candidates:
        df = pd.read_parquet(in_path)
        before_cols = df.shape[1]
        before_rows = len(df)
        file_report = sanitize_parquet_file(
            in_path,
            out_path,
            allow_identifiers=allow_identifiers,
        )
        after_cols = file_report.get("cols_after", before_cols)
        dropped = before_cols - int(after_cols)
        _info(
            f"Sanitized {label}: {before_rows} rows, {before_cols} → {after_cols} cols (dropped {dropped})"
        )
        aggregated["files"][label] = file_report

    write_sanitize_report(report_path, aggregated)
    _info(f"Wrote report: {report_path}")


@app.command("data-dictionary")
def data_dictionary(
    input: Path = typer.Option(
        None,
        "--input",
        help="Input parquet (default: daily_sanitized.parquet, fallback: daily.parquet)",
    ),
    out_dir: Path = typer.Option(
        None,
        "--out-dir",
        help="Output directory for reports (default: reports)",
    ),
    max_sample_values: int = typer.Option(
        5,
        "--max-sample-values",
        help="Max distinct example values per column",
    ),
) -> None:
    """Generate a data dictionary report for the aggregated dataset."""
    processed_dir = get_processed_dir()
    default_in = processed_dir / "daily_sanitized.parquet"
    fallback_in = processed_dir / "daily.parquet"
    input_path = input or (default_in if default_in.exists() else fallback_in)

    if not input_path.exists():
        _info(f"Missing input: {input_path}")
        raise typer.Exit(code=1)

    output_dir = out_dir or (get_repo_root() / "reports")

    df = pd.read_parquet(input_path)

    def _log_ts_counts(label: str, frame: pd.DataFrame) -> None:
        for col in ["sleepStartTimestampGMT", "sleepEndTimestampGMT"]:
            if col in frame.columns:
                _info(f"{label} {col} non-null: {int(frame[col].notna().sum())}")

    _log_ts_counts("input", df)

    if input is None and input_path == default_in and fallback_in.exists():
        _log_ts_counts("daily_sanitized", df)
        if all(
            col in df.columns and int(df[col].notna().sum()) == 0
            for col in ["sleepStartTimestampGMT", "sleepEndTimestampGMT"]
        ):
            daily_df = pd.read_parquet(fallback_in)
            _log_ts_counts("daily", daily_df)
            if any(
                col in daily_df.columns and int(daily_df[col].notna().sum()) > 0
                for col in ["sleepStartTimestampGMT", "sleepEndTimestampGMT"]
            ):
                _info(
                    "Warning: daily_sanitized appears stale; using daily.parquet instead."
                )
                df = daily_df
                input_path = fallback_in

    if fallback_in.exists() and fallback_in != input_path:
        daily_df = pd.read_parquet(fallback_in)
        _log_ts_counts("daily", daily_df)

    sleep_path = processed_dir / "sleep.parquet"
    if sleep_path.exists():
        sleep_df = pd.read_parquet(sleep_path)
        _log_ts_counts("sleep", sleep_df)
    dictionary_df = build_data_dictionary(df, max_sample_values=max_sample_values)
    csv_path, md_path = write_dictionary_reports(
        dictionary_df,
        df,
        output_dir,
        options=DictionaryOptions(max_sample_values=max_sample_values),
    )
    _info(f"Wrote {csv_path}")
    _info(f"Wrote {md_path}")


@app.command("quality")
def quality(
    input: Path = typer.Option(
        None,
        "--input",
        help="Input parquet (default: daily_sanitized.parquet, fallback: daily.parquet)",
    ),
    out_dir: Path = typer.Option(
        None,
        "--out-dir",
        help="Output directory for reports (default: reports)",
    ),
    output_parquet: Path = typer.Option(
        None,
        "--output-parquet",
        help="Output parquet path (default: data/processed/daily_quality.parquet)",
    ),
    no_parquet: bool = typer.Option(
        False,
        "--no-parquet",
        help="Do not write parquet output",
    ),
    steps_min: int = typer.Option(50, "--steps-min", help="Minimum steps for has_steps"),
    stress_any_hours: float = typer.Option(6.0, "--stress-any-hours", help="Minimum stress hours for has_stress_duration"),
    stress_full_hours: float = typer.Option(20.0, "--stress-full-hours", help="Minimum stress hours for full_day_stress"),
    strict_min_score: int = typer.Option(4, "--strict-min-score", help="Strict good-day threshold"),
    loose_min_score: int = typer.Option(3, "--loose-min-score", help="Loose good-day threshold"),
    top_n: int = typer.Option(50, "--top-n", help="Number of suspicious days to export"),
) -> None:
    """Compute day quality labels and export quality reports."""
    processed_dir = get_processed_dir()
    default_in = processed_dir / "daily_sanitized.parquet"
    fallback_in = processed_dir / "daily.parquet"
    input_path = input or (default_in if default_in.exists() else fallback_in)

    if not input_path.exists():
        _info(f"Missing input: {input_path}")
        raise typer.Exit(code=1)

    out_path = out_dir or (get_repo_root() / "reports")
    parquet_path = output_parquet or (processed_dir / "daily_quality.parquet")

    config = QualityConfig(
        steps_min=steps_min,
        stress_any_min_seconds=int(stress_any_hours * 3600),
        stress_full_min_seconds=int(stress_full_hours * 3600),
        strict_min_score=strict_min_score,
        loose_min_score=loose_min_score,
        top_n=top_n,
    )

    df = pd.read_parquet(input_path)
    quality_df = apply_quality_labels(df, config)
    suspicious_df = build_suspicious_days(quality_df, top_n=config.top_n)
    summary_md = build_quality_summary_markdown(quality_df, input_path=input_path, config=config)

    summary_path, suspicious_path, maybe_parquet = write_quality_outputs(
        quality_df,
        suspicious_df,
        out_dir=out_path,
        summary_markdown=summary_md,
        output_parquet=parquet_path,
        write_parquet=not no_parquet,
    )

    strict_dist = quality_df["day_quality_label_strict"].value_counts(dropna=False)
    loose_dist = quality_df["day_quality_label_loose"].value_counts(dropna=False)
    total = len(quality_df) or 1

    def _pct(count: int) -> float:
        return count / total * 100.0

    _info(f"Input: {input_path}")
    _info(f"Total days: {len(quality_df)}")
    _info(
        "Strict labels: "
        f"good={_pct(int(strict_dist.get('good', 0))):.2f}% "
        f"partial={_pct(int(strict_dist.get('partial', 0))):.2f}% "
        f"bad={_pct(int(strict_dist.get('bad', 0))):.2f}%"
    )
    _info(
        "Loose labels: "
        f"good={_pct(int(loose_dist.get('good', 0))):.2f}% "
        f"partial={_pct(int(loose_dist.get('partial', 0))):.2f}% "
        f"bad={_pct(int(loose_dist.get('bad', 0))):.2f}%"
    )
    _info(f"Suspicious days exported: {len(suspicious_df)}")
    _info(f"Wrote {summary_path}")
    _info(f"Wrote {suspicious_path}")
    if maybe_parquet is not None:
        _info(f"Wrote {maybe_parquet}")
