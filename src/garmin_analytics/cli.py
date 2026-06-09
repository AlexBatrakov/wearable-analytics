from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console

from .ingest.sleep import parse_sleep_files
from .ingest.uds import parse_uds_files
from .monitoring import (
    build_monitoring_analysis_windows,
    build_monitoring_core_features,
    build_monitoring_core_features_summary_markdown,
    build_monitoring_feature_catalog,
    build_monitoring_feature_catalog_markdown,
    build_monitoring_features_full,
    build_monitoring_features_full_summary_markdown,
    build_monitoring_daily_features,
    build_monitoring_foundation_summary_markdown,
    build_monitoring_quality_index,
    build_monitoring_quality_summary_markdown,
    build_monitoring_quality_windows,
    build_semantic_sleep_windows,
    materialize_monitoring_fit,
    select_monitoring_core_features,
)
from .modeling.stage4 import (
    Stage4ModelingFrameConfig,
    build_stage4_feature_set_catalog,
    build_stage4_feature_sets_markdown,
    build_stage4_modeling_frame_summary_markdown,
    build_stage4_sleep_modeling_frame,
    split_summary,
)
from .quality.quality import (
    QualityConfig,
    apply_quality_labels,
    build_quality_summary_markdown,
    build_suspicious_days,
    build_suspicious_days_artifacts,
    write_quality_outputs,
)
from .reports.data_dictionary import DictionaryOptions, build_data_dictionary, write_dictionary_reports
from .sanitize import sanitize_parquet_file, write_sanitize_report
from .sql import build_sql_mart, run_sql_directory
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


def _pick_existing_path(*candidates: Path) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return None


def _normalize_and_validate_calendar_date(df: pd.DataFrame, *, label: str) -> None:
    """Normalize and validate the calendarDate column in-place."""
    if "calendarDate" not in df.columns:
        _info(f"{label} is missing required column: calendarDate")
        raise typer.Exit(code=1)

    normalized = pd.to_datetime(df["calendarDate"], errors="coerce").dt.normalize()
    invalid = int(normalized.isna().sum())
    if invalid > 0:
        _info(f"{label} has {invalid} invalid calendarDate values after parsing")
        raise typer.Exit(code=1)

    df["calendarDate"] = normalized


def _assert_unique_calendar_date(df: pd.DataFrame, *, label: str) -> None:
    """Fail fast if calendarDate is not unique before merge."""
    duplicate_mask = df["calendarDate"].duplicated(keep=False)
    if not bool(duplicate_mask.any()):
        return

    dup_rows = int(duplicate_mask.sum())
    dup_dates = (
        pd.to_datetime(df.loc[duplicate_mask, "calendarDate"], errors="coerce")
        .dropna()
        .drop_duplicates()
        .sort_values()
    )
    examples = [str(ts.date()) for ts in dup_dates[:5]]
    _info(
        f"{label} has duplicate calendarDate rows ({dup_rows} rows across {len(dup_dates)} dates). "
        f"Examples: {examples}"
    )
    raise typer.Exit(code=1)


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


@app.command("ingest-monitoring-fit")
def ingest_monitoring_fit(
    input_dir: Path = typer.Option(
        None,
        "--input-dir",
        help="Directory containing Garmin Uploaded Files FIT exports (default: data/raw/DI_CONNECT/DI-Connect-Uploaded-Files)",
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        help="Output directory for monitoring parquets (default: data/processed)",
    ),
) -> None:
    """Decode monitoring FIT heart-rate and stress tables."""
    export_dir = get_export_dir()
    resolved_input_dir = input_dir or (export_dir / "DI-Connect-Uploaded-Files")
    resolved_output_dir = output_dir or get_processed_dir()

    if not resolved_input_dir.exists():
        _info(f"Missing input directory: {resolved_input_dir}")
        raise typer.Exit(code=1)

    try:
        summary = materialize_monitoring_fit(
            input_dir=resolved_input_dir,
            output_dir=resolved_output_dir,
        )
    except ModuleNotFoundError as err:
        _info(str(err))
        raise typer.Exit(code=1) from err

    _info(f"FIT files seen: {summary.fit_files_seen}")
    _info(f"Monitoring files decoded: {summary.monitoring_files_decoded}")
    _info(f"Decode errors skipped: {summary.decode_errors}")
    _info(f"Heart-rate rows: {summary.heart_rate_rows}")
    _info(f"Stress rows: {summary.stress_rows}")
    _info(f"Wrote {summary.heart_rate_output_path}")
    _info(f"Wrote {summary.stress_output_path}")


@app.command("build-semantic-windows")
def build_semantic_windows_command(
    sleep_path: Path = typer.Option(
        None,
        "--sleep-path",
        help="Sleep parquet source (default: data/processed/sleep.parquet)",
    ),
    daily_path: Path = typer.Option(
        None,
        "--daily-path",
        help="Daily aggregate parquet with Garmin local/GMT wellness timestamps (default: daily_uds.parquet, fallback: daily.parquet)",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        help="Semantic windows parquet (default: data/processed/semantic_sleep_windows.parquet)",
    ),
) -> None:
    """Build sleep-aware semantic day windows from the sleep table."""
    processed_dir = get_processed_dir()
    resolved_sleep_path = sleep_path or (processed_dir / "sleep.parquet")
    resolved_daily_path = daily_path or _pick_existing_path(
        processed_dir / "daily_uds.parquet",
        processed_dir / "daily.parquet",
    )
    resolved_output = output or (processed_dir / "semantic_sleep_windows.parquet")

    if not resolved_sleep_path.exists():
        _info(f"Missing input: {resolved_sleep_path}")
        raise typer.Exit(code=1)
    if daily_path is not None and not daily_path.exists():
        _info(f"Missing input: {daily_path}")
        raise typer.Exit(code=1)

    try:
        sleep_df = pd.read_parquet(resolved_sleep_path)
        daily_df = pd.read_parquet(resolved_daily_path) if resolved_daily_path is not None else None
        windows_df = build_semantic_sleep_windows(sleep_df, daily_df=daily_df)
    except ValueError as err:
        _info(str(err))
        raise typer.Exit(code=1) from err

    ensure_dir(resolved_output.parent)
    windows_df.to_parquet(resolved_output, index=False, engine="pyarrow")
    _info(f"Wrote {len(windows_df)} rows to {resolved_output}")
    _info(f"Daily offset source: {resolved_daily_path or 'none'}")
    if "local_utc_offset_minutes" in windows_df.columns:
        offset_rows = int(pd.to_numeric(windows_df["local_utc_offset_minutes"], errors="coerce").notna().sum())
        _info(f"Rows with local UTC offset: {offset_rows}")


@app.command("build-monitoring-features")
def build_monitoring_features_command(
    heart_rate_path: Path = typer.Option(
        None,
        "--heart-rate-path",
        help="Monitoring heart-rate parquet (default: data/processed/monitoring_heart_rate.parquet)",
    ),
    stress_path: Path = typer.Option(
        None,
        "--stress-path",
        help="Monitoring stress parquet (default: data/processed/monitoring_stress.parquet)",
    ),
    windows_path: Path = typer.Option(
        None,
        "--windows-path",
        help="Semantic windows parquet (default: data/processed/semantic_sleep_windows.parquet)",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        help="Monitoring feature parquet (default: data/processed/monitoring_daily_features.parquet)",
    ),
    report: Path = typer.Option(
        None,
        "--report",
        help="Aggregate markdown summary (default: reports/monitoring_foundation_summary.md)",
    ),
) -> None:
    """Build minimal baseline sleep/wake monitoring features."""
    repo_root = get_repo_root()
    processed_dir = get_processed_dir()
    resolved_hr_path = heart_rate_path or (processed_dir / "monitoring_heart_rate.parquet")
    resolved_stress_path = stress_path or (processed_dir / "monitoring_stress.parquet")
    resolved_windows_path = windows_path or (processed_dir / "semantic_sleep_windows.parquet")
    resolved_output = output or (processed_dir / "monitoring_daily_features.parquet")
    resolved_report = report or (repo_root / "reports" / "monitoring_foundation_summary.md")

    for path in [resolved_hr_path, resolved_stress_path, resolved_windows_path]:
        if not path.exists():
            _info(f"Missing input: {path}")
            raise typer.Exit(code=1)

    heart_rate_df = pd.read_parquet(resolved_hr_path)
    stress_df = pd.read_parquet(resolved_stress_path)
    windows_df = pd.read_parquet(resolved_windows_path)
    feature_df = build_monitoring_daily_features(heart_rate_df, stress_df, windows_df)

    ensure_dir(resolved_output.parent)
    feature_df.to_parquet(resolved_output, index=False, engine="pyarrow")

    ensure_dir(resolved_report.parent)
    resolved_report.write_text(
        build_monitoring_foundation_summary_markdown(
            heart_rate_df=heart_rate_df,
            stress_df=stress_df,
            semantic_windows_df=windows_df,
            feature_df=feature_df,
        ),
        encoding="utf-8",
    )

    _info(f"Wrote {len(feature_df)} rows to {resolved_output}")
    _info(f"Wrote {resolved_report}")


@app.command("build-monitoring-datasets")
def build_monitoring_datasets_command(
    heart_rate_path: Path = typer.Option(
        None,
        "--heart-rate-path",
        help="Monitoring heart-rate parquet (default: data/processed/monitoring_heart_rate.parquet)",
    ),
    stress_path: Path = typer.Option(
        None,
        "--stress-path",
        help="Monitoring stress parquet (default: data/processed/monitoring_stress.parquet)",
    ),
    windows_path: Path = typer.Option(
        None,
        "--windows-path",
        help="Semantic windows parquet (default: data/processed/semantic_sleep_windows.parquet)",
    ),
    quality_index_output: Path = typer.Option(
        None,
        "--quality-index-output",
        help="Quality index parquet (default: data/processed/monitoring_quality_index.parquet)",
    ),
    core_output: Path = typer.Option(
        None,
        "--core-output",
        help="Core features parquet (default: data/processed/monitoring_features_core_v0.parquet)",
    ),
    full_output: Path = typer.Option(
        None,
        "--full-output",
        help="Full features parquet (default: data/processed/monitoring_features_full_v0.parquet)",
    ),
    quality_report: Path = typer.Option(
        None,
        "--quality-report",
        help="Quality markdown report (default: reports/monitoring_quality_summary.md)",
    ),
    core_report: Path = typer.Option(
        None,
        "--core-report",
        help="Core features markdown report (default: reports/monitoring_core_features_summary.md)",
    ),
    full_report: Path = typer.Option(
        None,
        "--full-report",
        help="Full features markdown report (default: reports/monitoring_features_full_summary.md)",
    ),
    full_catalog_csv: Path = typer.Option(
        None,
        "--full-catalog-csv",
        help="Full feature catalog CSV (default: reports/monitoring_features_full_catalog.csv)",
    ),
    full_catalog_md: Path = typer.Option(
        None,
        "--full-catalog-md",
        help="Full feature catalog markdown (default: reports/monitoring_features_full_catalog.md)",
    ),
) -> None:
    """Build the quality index plus compact and cleaned full monitoring feature tables."""
    repo_root = get_repo_root()
    processed_dir = get_processed_dir()
    resolved_hr_path = heart_rate_path or (processed_dir / "monitoring_heart_rate.parquet")
    resolved_stress_path = stress_path or (processed_dir / "monitoring_stress.parquet")
    resolved_windows_path = windows_path or (processed_dir / "semantic_sleep_windows.parquet")
    resolved_quality_index = quality_index_output or (processed_dir / "monitoring_quality_index.parquet")
    resolved_core_output = core_output or (processed_dir / "monitoring_features_core_v0.parquet")
    resolved_full_output = full_output or (processed_dir / "monitoring_features_full_v0.parquet")
    resolved_quality_report = quality_report or (repo_root / "reports" / "monitoring_quality_summary.md")
    resolved_core_report = core_report or (repo_root / "reports" / "monitoring_core_features_summary.md")
    resolved_full_report = full_report or (repo_root / "reports" / "monitoring_features_full_summary.md")
    resolved_full_catalog_csv = full_catalog_csv or (repo_root / "reports" / "monitoring_features_full_catalog.csv")
    resolved_full_catalog_md = full_catalog_md or (repo_root / "reports" / "monitoring_features_full_catalog.md")

    for path in [resolved_hr_path, resolved_stress_path, resolved_windows_path]:
        if not path.exists():
            _info(f"Missing input: {path}")
            raise typer.Exit(code=1)

    heart_rate_df = pd.read_parquet(resolved_hr_path)
    stress_df = pd.read_parquet(resolved_stress_path)
    windows_df = pd.read_parquet(resolved_windows_path)

    analysis_windows_df = build_monitoring_analysis_windows(
        windows_df,
        heart_rate_df=heart_rate_df,
        stress_df=stress_df,
    )
    quality_windows_df = build_monitoring_quality_windows(
        heart_rate_df,
        stress_df,
        analysis_windows_df,
    )
    quality_index_df = build_monitoring_quality_index(
        analysis_windows_df,
        quality_windows_df,
    )
    full_df = build_monitoring_features_full(
        heart_rate_df,
        stress_df,
        quality_index_df,
    )
    core_df = select_monitoring_core_features(full_df)
    full_catalog_df = build_monitoring_feature_catalog(full_df)

    for output_path, frame in [
        (resolved_quality_index, quality_index_df),
        (resolved_core_output, core_df),
        (resolved_full_output, full_df),
    ]:
        ensure_dir(output_path.parent)
        frame.to_parquet(output_path, index=False, engine="pyarrow")

    ensure_dir(resolved_quality_report.parent)
    resolved_quality_report.write_text(
        build_monitoring_quality_summary_markdown(quality_index_df, quality_windows_df),
        encoding="utf-8",
    )
    ensure_dir(resolved_core_report.parent)
    resolved_core_report.write_text(
        build_monitoring_core_features_summary_markdown(core_df, quality_index_df),
        encoding="utf-8",
    )
    ensure_dir(resolved_full_catalog_csv.parent)
    full_catalog_df.to_csv(resolved_full_catalog_csv, index=False)
    ensure_dir(resolved_full_catalog_md.parent)
    resolved_full_catalog_md.write_text(
        build_monitoring_feature_catalog_markdown(
            full_catalog_df,
            csv_path=_safe_relpath(resolved_full_catalog_csv, repo_root),
        ),
        encoding="utf-8",
    )
    ensure_dir(resolved_full_report.parent)
    resolved_full_report.write_text(
        build_monitoring_features_full_summary_markdown(
            full_df,
            max_hr_bpm=192.0,
            gap_break_minutes=2.0,
            min_valid_minutes=5,
            min_paired_minutes=10,
            catalog_df=full_catalog_df,
            catalog_csv_path=_safe_relpath(resolved_full_catalog_csv, repo_root),
            catalog_md_path=_safe_relpath(resolved_full_catalog_md, repo_root),
        ),
        encoding="utf-8",
    )

    _info(f"Wrote {len(quality_index_df)} quality rows to {resolved_quality_index}")
    _info(f"Wrote {len(core_df)} core rows and {core_df.shape[1]} columns to {resolved_core_output}")
    _info(f"Wrote {len(full_df)} full rows and {full_df.shape[1]} columns to {resolved_full_output}")
    _info(f"Wrote {resolved_quality_report}")
    _info(f"Wrote {resolved_core_report}")
    _info(f"Wrote {resolved_full_report}")
    _info(f"Wrote {resolved_full_catalog_csv}")
    _info(f"Wrote {resolved_full_catalog_md}")


@app.command("build-stage4-sleep-modeling-frame")
@app.command("build-stage4-modeling-frame")
def build_stage4_modeling_frame_command(
    monitoring_quality_path: Path = typer.Option(
        None,
        "--monitoring-quality-path",
        help="Monitoring quality index parquet (default: data/processed/monitoring_quality_index.parquet)",
    ),
    monitoring_core_path: Path = typer.Option(
        None,
        "--monitoring-core-path",
        help="Monitoring core feature parquet (default: data/processed/monitoring_features_core_v0.parquet)",
    ),
    monitoring_full_path: Path = typer.Option(
        None,
        "--monitoring-full-path",
        help="Monitoring full feature parquet (default: data/processed/monitoring_features_full_v0.parquet)",
    ),
    sleep_path: Path = typer.Option(
        None,
        "--sleep-path",
        help="Sleep parquet source (default: sleep_sanitized.parquet, fallback: sleep.parquet)",
    ),
    full_catalog_csv: Path = typer.Option(
        None,
        "--full-catalog-csv",
        help="Monitoring full catalog CSV (default: reports/monitoring_features_full_catalog.csv)",
    ),
    daily_path: Path = typer.Option(
        None,
        "--daily-path",
        help="Aggregate daily parquet (default: daily_sanitized.parquet, fallback: daily.parquet)",
    ),
    daily_quality_path: Path = typer.Option(
        None,
        "--daily-quality-path",
        help="Daily quality parquet (default: data/processed/daily_quality.parquet)",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        help="Stage 4 modeling frame parquet (default: data/processed/stage4_sleep_modeling_frame.parquet)",
    ),
    summary_report: Path = typer.Option(
        None,
        "--summary-report",
        help="Markdown summary report (default: reports/stage4_sleep_modeling_frame_summary.md)",
    ),
    feature_sets_csv: Path = typer.Option(
        None,
        "--feature-sets-csv",
        help="Feature-set catalog CSV (default: reports/stage4_sleep_modeling_feature_sets.csv)",
    ),
    feature_sets_md: Path = typer.Option(
        None,
        "--feature-sets-md",
        help="Feature-set markdown summary (default: reports/stage4_sleep_modeling_feature_sets.md)",
    ),
    random_state: int = typer.Option(
        42,
        "--random-state",
        help="Seed for random train/validation assignment inside the pre-test history",
    ),
) -> None:
    """Build the Stage 4 sleep outcome modeling frame and audit artifacts."""
    repo_root = get_repo_root()
    processed_dir = get_processed_dir()
    resolved_monitoring_quality = monitoring_quality_path or (processed_dir / "monitoring_quality_index.parquet")
    resolved_monitoring_core = monitoring_core_path or (processed_dir / "monitoring_features_core_v0.parquet")
    resolved_monitoring_full = monitoring_full_path or (processed_dir / "monitoring_features_full_v0.parquet")
    resolved_sleep = sleep_path or _pick_existing_path(
        processed_dir / "sleep_sanitized.parquet",
        processed_dir / "sleep.parquet",
    )
    resolved_full_catalog = full_catalog_csv or (repo_root / "reports" / "monitoring_features_full_catalog.csv")
    resolved_daily = daily_path or _pick_existing_path(
        processed_dir / "daily_sanitized.parquet",
        processed_dir / "daily.parquet",
    )
    resolved_daily_quality = daily_quality_path or (processed_dir / "daily_quality.parquet")
    resolved_output = output or (processed_dir / "stage4_sleep_modeling_frame.parquet")
    resolved_summary_report = summary_report or (repo_root / "reports" / "stage4_sleep_modeling_frame_summary.md")
    resolved_feature_sets_csv = feature_sets_csv or (repo_root / "reports" / "stage4_sleep_modeling_feature_sets.csv")
    resolved_feature_sets_md = feature_sets_md or (repo_root / "reports" / "stage4_sleep_modeling_feature_sets.md")

    required_paths = [
        resolved_monitoring_quality,
        resolved_monitoring_core,
        resolved_monitoring_full,
        resolved_full_catalog,
        resolved_daily_quality,
    ]
    if resolved_sleep is None:
        _info("Missing sleep parquet source. Expected sleep_sanitized.parquet or sleep.parquet.")
        raise typer.Exit(code=1)
    if resolved_daily is None:
        _info("Missing aggregate daily parquet source. Expected daily_sanitized.parquet or daily.parquet.")
        raise typer.Exit(code=1)
    required_paths.extend([resolved_sleep, resolved_daily])
    for path in required_paths:
        if not path.exists():
            _info(f"Missing input: {path}")
            raise typer.Exit(code=1)

    result = build_stage4_sleep_modeling_frame(
        monitoring_quality_df=pd.read_parquet(resolved_monitoring_quality),
        monitoring_core_df=pd.read_parquet(resolved_monitoring_core),
        monitoring_full_df=pd.read_parquet(resolved_monitoring_full),
        sleep_df=pd.read_parquet(resolved_sleep),
        full_catalog_df=pd.read_csv(resolved_full_catalog),
        daily_df=pd.read_parquet(resolved_daily),
        daily_quality_df=pd.read_parquet(resolved_daily_quality),
        config=Stage4ModelingFrameConfig(random_state=random_state),
    )
    feature_catalog_df = build_stage4_feature_set_catalog(
        result.frame,
        result.feature_sets,
        full_catalog_df=pd.read_csv(resolved_full_catalog),
        aggregate_candidate_review=result.aggregate_candidate_review,
    )

    ensure_dir(resolved_output.parent)
    result.frame.to_parquet(resolved_output, index=False, engine="pyarrow")

    ensure_dir(resolved_feature_sets_csv.parent)
    feature_catalog_df.to_csv(resolved_feature_sets_csv, index=False)

    ensure_dir(resolved_feature_sets_md.parent)
    resolved_feature_sets_md.write_text(
        build_stage4_feature_sets_markdown(
            result.frame,
            result.feature_sets,
            feature_catalog_df,
            result.aggregate_candidate_review,
        ),
        encoding="utf-8",
    )

    ensure_dir(resolved_summary_report.parent)
    resolved_summary_report.write_text(
        build_stage4_modeling_frame_summary_markdown(
            result,
            output_path=_safe_relpath(resolved_output, repo_root),
            feature_catalog_path=_safe_relpath(resolved_feature_sets_csv, repo_root),
            feature_sets_md_path=_safe_relpath(resolved_feature_sets_md, repo_root),
        ),
        encoding="utf-8",
    )

    _info(f"Wrote {len(result.frame)} rows and {result.frame.shape[1]} columns to {resolved_output}")
    for row in split_summary(result.frame).to_dict("records"):
        _info(
            f"Split {row['split']}: rows={row['rows']} "
            f"eligible={row['eligible_rows']} primary_target={row['primary_target_rows']}"
        )
    for name, feature_set in result.feature_sets.items():
        _info(f"Feature set {name}: {len(feature_set.columns)} columns")
    _info(f"Wrote {resolved_summary_report}")
    _info(f"Wrote {resolved_feature_sets_csv}")
    _info(f"Wrote {resolved_feature_sets_md}")

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

    _normalize_and_validate_calendar_date(uds_df, label="daily_uds.parquet")
    _normalize_and_validate_calendar_date(sleep_df, label="sleep.parquet")
    _assert_unique_calendar_date(uds_df, label="daily_uds.parquet")
    _assert_unique_calendar_date(sleep_df, label="sleep.parquet")

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
    markdown_mode: str = typer.Option(
        "full",
        "--markdown-mode",
        help="Markdown output mode: full, summary, or both",
    ),
) -> None:
    """Generate a data dictionary report for the aggregated dataset."""
    if markdown_mode not in {"full", "summary", "both"}:
        _info("Invalid --markdown-mode. Expected one of: full, summary, both")
        raise typer.Exit(code=1)

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
    csv_path, full_md_path, summary_md_path = write_dictionary_reports(
        dictionary_df,
        df,
        output_dir,
        options=DictionaryOptions(max_sample_values=max_sample_values),
        markdown_mode=markdown_mode,
    )
    _info(f"Wrote {csv_path}")
    if full_md_path is not None:
        _info(f"Wrote {full_md_path}")
    if summary_md_path is not None:
        _info(f"Wrote {summary_md_path}")


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
    suspicious_artifacts_df = build_suspicious_days_artifacts(quality_df, top_n=config.top_n)
    summary_md = build_quality_summary_markdown(quality_df, input_path=input_path, config=config)

    summary_path, suspicious_path, maybe_parquet, suspicious_artifacts_path = write_quality_outputs(
        quality_df,
        suspicious_df,
        suspicious_artifacts_df=suspicious_artifacts_df,
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
    if suspicious_artifacts_path is not None:
        _info(f"Wrote {suspicious_artifacts_path}")
    if maybe_parquet is not None:
        _info(f"Wrote {maybe_parquet}")


@app.command("build-sql-mart")
def build_sql_mart_command(
    db_path: Path = typer.Option(
        None,
        "--db-path",
        help="Output DuckDB path (default: data/processed/analytics.duckdb)",
    ),
    daily_path: Path = typer.Option(
        None,
        "--daily-path",
        help="Daily source parquet (default: daily_sanitized.parquet, fallback: daily.parquet)",
    ),
    sleep_path: Path = typer.Option(
        None,
        "--sleep-path",
        help="Sleep source parquet (default: sleep_sanitized.parquet, fallback: sleep.parquet)",
    ),
    quality_path: Path = typer.Option(
        None,
        "--quality-path",
        help="Quality source parquet (default: daily_quality.parquet if present)",
    ),
    overwrite: bool = typer.Option(
        True,
        "--overwrite/--no-overwrite",
        help="Overwrite existing DuckDB file if it already exists",
    ),
) -> None:
    """Build a local DuckDB mart from Stage 1 parquet outputs."""
    processed_dir = get_processed_dir()

    resolved_daily = daily_path or _pick_existing_path(
        processed_dir / "daily_sanitized.parquet",
        processed_dir / "daily.parquet",
    )
    if resolved_daily is None:
        _info(
            "Missing daily parquet source. Expected one of: "
            f"{processed_dir / 'daily_sanitized.parquet'} or {processed_dir / 'daily.parquet'}"
        )
        raise typer.Exit(code=1)

    resolved_sleep = sleep_path or _pick_existing_path(
        processed_dir / "sleep_sanitized.parquet",
        processed_dir / "sleep.parquet",
    )
    resolved_quality = quality_path or _pick_existing_path(processed_dir / "daily_quality.parquet")

    resolved_db_path = db_path or (processed_dir / "analytics.duckdb")
    try:
        summary = build_sql_mart(
            db_path=resolved_db_path,
            daily_path=resolved_daily,
            sleep_path=resolved_sleep,
            quality_path=resolved_quality,
            overwrite=overwrite,
        )
    except (FileNotFoundError, ModuleNotFoundError) as err:
        _info(str(err))
        raise typer.Exit(code=1) from err

    _info(f"DuckDB mart: {summary.db_path}")
    _info(f"Daily source: {summary.daily_source}")
    _info(f"Sleep source: {summary.sleep_source or 'fact_daily fallback'}")
    _info(f"Quality source: {summary.quality_source or 'fact_daily fallback'}")
    _info(
        "Tables: "
        f"fact_daily={summary.fact_daily_rows}, "
        f"fact_sleep={summary.fact_sleep_rows}, "
        f"fact_quality={summary.fact_quality_rows}"
    )
    _info(
        "Views: "
        f"vw_day_to_next_sleep={summary.day_to_next_sleep_rows}, "
        f"vw_weekday_profiles={summary.weekday_profile_rows}"
    )


@app.command("run-sql-portfolio")
def run_sql_portfolio(
    db_path: Path = typer.Option(
        None,
        "--db-path",
        help="DuckDB file (default: data/processed/analytics.duckdb)",
    ),
    query_dir: Path = typer.Option(
        None,
        "--query-dir",
        help="Directory with SQL query files (default: sql/duckdb)",
    ),
    out_dir: Path = typer.Option(
        None,
        "--out-dir",
        help="Directory for CSV outputs (default: reports/sql/duckdb)",
    ),
) -> None:
    """Run SQL showcase queries against the DuckDB mart and export CSV results."""
    repo_root = get_repo_root()
    processed_dir = get_processed_dir()

    resolved_db = db_path or (processed_dir / "analytics.duckdb")
    resolved_query_dir = query_dir or (repo_root / "sql" / "duckdb")
    resolved_out_dir = out_dir or (repo_root / "reports" / "sql" / "duckdb")

    try:
        results = run_sql_directory(
            db_path=resolved_db,
            query_dir=resolved_query_dir,
            output_dir=resolved_out_dir,
        )
    except (FileNotFoundError, ModuleNotFoundError) as err:
        _info(str(err))
        raise typer.Exit(code=1) from err

    _info(f"Executed SQL files: {len(results)}")
    for result in results:
        _info(
            f"{result.query_path.name} -> {result.output_csv_path} "
            f"(rows={result.rows}, cols={result.columns})"
        )
