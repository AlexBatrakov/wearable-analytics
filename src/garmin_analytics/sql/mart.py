from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Any


SLEEP_FALLBACK_COLUMNS: tuple[str, ...] = (
    "sleepStartTimestampGMT",
    "sleepEndTimestampGMT",
    "deepSleepSeconds",
    "lightSleepSeconds",
    "remSleepSeconds",
    "awakeSleepSeconds",
    "averageRespiration",
    "avgSleepStress",
    "sleepOverallScore",
    "sleepQualityScore",
    "sleepDurationScore",
    "sleepRecoveryScore",
    "sleepAverageStressLevel",
    "sleep_start_hour_local",
    "sleep_start_hour_local_wrapped",
    "sleep_opportunity_hours",
)

QUALITY_FALLBACK_COLUMNS: tuple[str, ...] = (
    "quality_score",
    "day_quality_label_strict",
    "day_quality_label_loose",
    "valid_day_strict",
    "valid_day_loose",
    "has_sleep",
    "corrupted_stress_only_day",
)


@dataclass(frozen=True)
class SqlMartBuildResult:
    """Summary of SQL mart build outputs."""

    db_path: Path
    daily_source: Path
    sleep_source: Path | None
    quality_source: Path | None
    fact_daily_rows: int
    fact_sleep_rows: int
    fact_quality_rows: int
    day_to_next_sleep_rows: int
    weekday_profile_rows: int


def _require_duckdb() -> Any:
    try:
        return importlib.import_module("duckdb")
    except ModuleNotFoundError as err:
        raise ModuleNotFoundError(
            "DuckDB is required for SQL mart commands. Install dependencies from requirements.txt."
        ) from err


def _table_columns(connection: Any, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    # PRAGMA table_info returns tuples where index 1 is column name.
    return {str(row[1]) for row in rows}


def _optional_select(
    columns: set[str],
    *,
    alias: str,
    column: str,
    sql_type: str,
    as_name: str | None = None,
) -> str:
    out_name = as_name or column
    if column in columns:
        return f"{alias}.{column} AS {out_name}"
    return f"CAST(NULL AS {sql_type}) AS {out_name}"


def _optional_value(
    columns: set[str],
    *,
    alias: str,
    column: str,
    sql_type: str,
) -> str:
    if column in columns:
        return f"{alias}.{column}"
    return f"CAST(NULL AS {sql_type})"


def _coalesced_optional(
    columns: set[str],
    *,
    alias: str,
    candidates: tuple[str, ...],
    sql_type: str,
    as_name: str,
) -> str:
    present = [f"{alias}.{column}" for column in candidates if column in columns]
    if not present:
        return f"CAST(NULL AS {sql_type}) AS {as_name}"
    if len(present) == 1:
        return f"{present[0]} AS {as_name}"
    return f"COALESCE({', '.join(present)}) AS {as_name}"


def _coalesced_value(
    columns: set[str],
    *,
    alias: str,
    candidates: tuple[str, ...],
    sql_type: str,
) -> str:
    present = [f"{alias}.{column}" for column in candidates if column in columns]
    if not present:
        return f"CAST(NULL AS {sql_type})"
    if len(present) == 1:
        return present[0]
    return f"COALESCE({', '.join(present)})"


def _create_fact_table_from_parquet(
    connection: Any,
    *,
    table_name: str,
    parquet_path: Path,
) -> None:
    connection.execute(
        f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT
            CAST(calendarDate AS DATE) AS calendarDate,
            * EXCLUDE (calendarDate)
        FROM read_parquet(?)
        """,
        [str(parquet_path)],
    )


def _create_sleep_fallback_from_daily(connection: Any) -> None:
    daily_columns = _table_columns(connection, "fact_daily")
    fallback_cols = [col for col in SLEEP_FALLBACK_COLUMNS if col in daily_columns]
    projection = ",\n            ".join(["calendarDate", *fallback_cols])
    connection.execute(
        f"""
        CREATE OR REPLACE TABLE fact_sleep AS
        SELECT
            {projection}
        FROM fact_daily
        """
    )


def _create_quality_fallback_from_daily(connection: Any) -> None:
    daily_columns = _table_columns(connection, "fact_daily")
    fallback_cols = [col for col in QUALITY_FALLBACK_COLUMNS if col in daily_columns]
    projection = ",\n            ".join(["calendarDate", *fallback_cols])
    connection.execute(
        f"""
        CREATE OR REPLACE TABLE fact_quality AS
        SELECT
            {projection}
        FROM fact_daily
        """
    )


def _create_views(connection: Any) -> None:
    daily_cols = _table_columns(connection, "fact_daily")
    sleep_cols = _table_columns(connection, "fact_sleep")
    quality_cols = _table_columns(connection, "fact_quality")

    quality_label_expr = _optional_select(
        quality_cols,
        alias="q",
        column="day_quality_label_strict",
        sql_type="VARCHAR",
        as_name="day_quality_label_strict",
    )
    valid_day_expr = _optional_select(
        quality_cols,
        alias="q",
        column="valid_day_strict",
        sql_type="BOOLEAN",
        as_name="valid_day_strict",
    )
    corrupted_expr = _optional_select(
        quality_cols,
        alias="q",
        column="corrupted_stress_only_day",
        sql_type="BOOLEAN",
        as_name="corrupted_stress_only_day",
    )
    sleep_avg_stress_expr = _coalesced_optional(
        sleep_cols,
        alias="s",
        candidates=("avgSleepStress", "sleepAverageStressLevel"),
        sql_type="DOUBLE",
        as_name="nextsleep_avg_sleep_stress",
    )

    connection.execute(
        f"""
        CREATE OR REPLACE VIEW vw_day_to_next_sleep AS
        SELECT
            d.calendarDate AS day_date,
            {_optional_select(daily_cols, alias='d', column='totalSteps', sql_type='DOUBLE', as_name='day_total_steps')},
            {_optional_select(daily_cols, alias='d', column='totalDistanceMeters', sql_type='DOUBLE', as_name='day_total_distance_meters')},
            {_optional_select(daily_cols, alias='d', column='activeKilocalories', sql_type='DOUBLE', as_name='day_active_kilocalories')},
            {_coalesced_optional(
                daily_cols,
                alias='d',
                candidates=('awakeAverageStressLevel', 'allDayStress_AWAKE_averageStressLevel'),
                sql_type='DOUBLE',
                as_name='day_awake_average_stress',
            )},
            {_optional_select(daily_cols, alias='d', column='maxHeartRate', sql_type='DOUBLE', as_name='day_max_heart_rate')},
            {_optional_select(daily_cols, alias='d', column='bodyBatteryLowest', sql_type='DOUBLE', as_name='day_body_battery_lowest')},
            {quality_label_expr},
            {valid_day_expr},
            {corrupted_expr},
            s.calendarDate AS next_sleep_date,
            {_optional_select(sleep_cols, alias='s', column='sleepRecoveryScore', sql_type='DOUBLE', as_name='nextsleep_recovery_score')},
            {_optional_select(sleep_cols, alias='s', column='sleepOverallScore', sql_type='DOUBLE', as_name='nextsleep_overall_score')},
            {_optional_select(sleep_cols, alias='s', column='sleepQualityScore', sql_type='DOUBLE', as_name='nextsleep_quality_score')},
            {sleep_avg_stress_expr},
            {_optional_select(sleep_cols, alias='s', column='sleepStartTimestampGMT', sql_type='DOUBLE', as_name='nextsleep_start_ts_gmt')},
            {_optional_select(sleep_cols, alias='s', column='sleepEndTimestampGMT', sql_type='DOUBLE', as_name='nextsleep_end_ts_gmt')}
        FROM fact_daily AS d
        LEFT JOIN fact_quality AS q
            ON q.calendarDate = d.calendarDate
        LEFT JOIN fact_sleep AS s
            ON s.calendarDate = d.calendarDate + INTERVAL 1 DAY
        ORDER BY d.calendarDate
        """
    )

    sleep_start_expr = _coalesced_value(
        sleep_cols,
        alias="s",
        candidates=("sleepStartTimestampGMT",),
        sql_type="DOUBLE",
    )
    sleep_end_expr = _coalesced_value(
        sleep_cols,
        alias="s",
        candidates=("sleepEndTimestampGMT",),
        sql_type="DOUBLE",
    )
    sleep_overall_expr = _optional_value(
        sleep_cols,
        alias="s",
        column="sleepOverallScore",
        sql_type="DOUBLE",
    )
    sleep_quality_expr = _optional_value(
        sleep_cols,
        alias="s",
        column="sleepQualityScore",
        sql_type="DOUBLE",
    )
    sleep_stress_expr = _coalesced_value(
        sleep_cols,
        alias="s",
        candidates=("avgSleepStress", "sleepAverageStressLevel"),
        sql_type="DOUBLE",
    )
    sleep_recovery_expr = _optional_value(
        sleep_cols,
        alias="s",
        column="sleepRecoveryScore",
        sql_type="DOUBLE",
    )

    stage_candidates = ("deepSleepSeconds", "lightSleepSeconds", "remSleepSeconds", "awakeSleepSeconds")
    stage_terms = [
        f"COALESCE({_optional_value(sleep_cols, alias='s', column=column, sql_type='DOUBLE')}, 0)"
        for column in stage_candidates
    ]
    any_stage_present = any(column in sleep_cols for column in stage_candidates)
    if any_stage_present:
        stage_hours_expr = f"({' + '.join(stage_terms)}) / 3600.0"
    else:
        stage_hours_expr = "CAST(NULL AS DOUBLE)"

    connection.execute(
        f"""
        CREATE OR REPLACE VIEW vw_sleep_nights AS
        SELECT
            s.calendarDate AS sleep_date,
            {sleep_start_expr} AS sleep_start_ts_gmt,
            {sleep_end_expr} AS sleep_end_ts_gmt,
            {sleep_overall_expr} AS sleep_overall_score,
            {sleep_quality_expr} AS sleep_quality_score,
            {sleep_stress_expr} AS sleep_avg_stress,
            {sleep_recovery_expr} AS sleep_recovery_score,
            CASE
                WHEN {sleep_end_expr} IS NOT NULL
                    AND {sleep_start_expr} IS NOT NULL
                    AND {sleep_end_expr} > {sleep_start_expr}
                THEN ({sleep_end_expr} - {sleep_start_expr}) / 3600.0
                ELSE {stage_hours_expr}
            END AS sleep_hours
        FROM fact_sleep AS s
        ORDER BY s.calendarDate
        """
    )

    connection.execute(
        """
        CREATE OR REPLACE VIEW vw_weekday_profiles AS
        SELECT
            CAST(date_part('isodow', day_date) AS INTEGER) AS iso_weekday,
            dayname(day_date) AS weekday_name,
            COUNT(*) AS days_total,
            COUNT(*) FILTER (WHERE valid_day_strict IS TRUE) AS strict_good_days,
            AVG(day_total_steps) AS avg_steps,
            MEDIAN(day_total_steps) AS median_steps,
            AVG(day_awake_average_stress) AS avg_awake_stress,
            MEDIAN(nextsleep_recovery_score) AS median_nextsleep_recovery
        FROM vw_day_to_next_sleep
        GROUP BY 1, 2
        ORDER BY 1
        """
    )


def _count_rows(connection: Any, relation: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {relation}").fetchone()[0])


def build_sql_mart(
    *,
    db_path: Path,
    daily_path: Path,
    sleep_path: Path | None,
    quality_path: Path | None,
    overwrite: bool = True,
) -> SqlMartBuildResult:
    """Build a local DuckDB analytics mart from Stage 1 outputs."""
    if not daily_path.exists():
        raise FileNotFoundError(f"Missing daily parquet source: {daily_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite and db_path.exists():
        db_path.unlink()

    duckdb = _require_duckdb()
    connection = duckdb.connect(str(db_path))
    try:
        connection.execute("PRAGMA enable_progress_bar=false")

        _create_fact_table_from_parquet(connection, table_name="fact_daily", parquet_path=daily_path)

        sleep_source: Path | None = None
        if sleep_path is not None and sleep_path.exists():
            _create_fact_table_from_parquet(connection, table_name="fact_sleep", parquet_path=sleep_path)
            sleep_source = sleep_path
        else:
            _create_sleep_fallback_from_daily(connection)

        quality_source: Path | None = None
        if quality_path is not None and quality_path.exists():
            _create_fact_table_from_parquet(connection, table_name="fact_quality", parquet_path=quality_path)
            quality_source = quality_path
        else:
            _create_quality_fallback_from_daily(connection)

        connection.execute("CREATE INDEX IF NOT EXISTS idx_fact_daily_date ON fact_daily(calendarDate)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_fact_sleep_date ON fact_sleep(calendarDate)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_fact_quality_date ON fact_quality(calendarDate)")

        _create_views(connection)

        return SqlMartBuildResult(
            db_path=db_path,
            daily_source=daily_path,
            sleep_source=sleep_source,
            quality_source=quality_source,
            fact_daily_rows=_count_rows(connection, "fact_daily"),
            fact_sleep_rows=_count_rows(connection, "fact_sleep"),
            fact_quality_rows=_count_rows(connection, "fact_quality"),
            day_to_next_sleep_rows=_count_rows(connection, "vw_day_to_next_sleep"),
            weekday_profile_rows=_count_rows(connection, "vw_weekday_profiles"),
        )
    finally:
        connection.close()
