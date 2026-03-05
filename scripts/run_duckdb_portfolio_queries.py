from __future__ import annotations

import argparse
from pathlib import Path

from garmin_analytics.sql import run_sql_directory
from garmin_analytics.util.io import get_processed_dir, get_repo_root


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run portfolio SQL queries against analytics.duckdb and export CSV files."
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=get_processed_dir() / "analytics.duckdb",
        help="DuckDB file to query.",
    )
    parser.add_argument(
        "--query-dir",
        type=Path,
        default=get_repo_root() / "sql" / "duckdb",
        help="Directory with .sql files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=get_repo_root() / "reports" / "sql" / "duckdb",
        help="Directory for CSV outputs.",
    )
    args = parser.parse_args()

    results = run_sql_directory(
        db_path=args.db_path,
        query_dir=args.query_dir,
        output_dir=args.output_dir,
    )

    print(f"Executed SQL files: {len(results)}")
    for result in results:
        print(
            f"{result.query_path.name} -> {result.output_csv_path} "
            f"(rows={result.rows}, cols={result.columns})"
        )


if __name__ == "__main__":
    main()
