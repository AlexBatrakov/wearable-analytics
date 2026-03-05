from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class QueryRunResult:
    """Metadata for one executed SQL query file."""

    query_path: Path
    output_csv_path: Path
    rows: int
    columns: int


def run_sql_directory(
    *,
    db_path: Path,
    query_dir: Path,
    output_dir: Path,
) -> list[QueryRunResult]:
    """Execute each .sql file against DuckDB and write CSV outputs."""
    if not db_path.exists():
        raise FileNotFoundError(f"Missing DuckDB file: {db_path}")
    if not query_dir.exists():
        raise FileNotFoundError(f"Missing query directory: {query_dir}")

    query_files = sorted(path for path in query_dir.glob("*.sql") if path.is_file())
    if not query_files:
        raise FileNotFoundError(f"No .sql files found under: {query_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    duckdb = _require_duckdb()
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        results: list[QueryRunResult] = []
        for query_path in query_files:
            query_text = query_path.read_text(encoding="utf-8")
            frame = connection.execute(query_text).df()
            csv_path = output_dir / f"{query_path.stem}.csv"
            frame.to_csv(csv_path, index=False)
            results.append(
                QueryRunResult(
                    query_path=query_path,
                    output_csv_path=csv_path,
                    rows=len(frame),
                    columns=len(frame.columns),
                )
            )
        return results
    finally:
        connection.close()


def _require_duckdb() -> Any:
    try:
        return importlib.import_module("duckdb")
    except ModuleNotFoundError as err:
        raise ModuleNotFoundError(
            "DuckDB is required for SQL portfolio commands. Install dependencies from requirements.txt."
        ) from err
