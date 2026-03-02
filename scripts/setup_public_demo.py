from __future__ import annotations

import argparse
from pathlib import Path

from garmin_analytics.demo import write_public_demo_dataset
from garmin_analytics.util.io import get_processed_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install the committed public demo sample into data/processed."
    )
    parser.add_argument(
        "--sample-csv",
        type=Path,
        default=None,
        help="Optional override for the public demo CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=get_processed_dir(),
        help="Directory where daily_sanitized.parquet should be written.",
    )
    args = parser.parse_args()

    output_path = write_public_demo_dataset(
        sample_csv_path=args.sample_csv,
        output_dir=args.output_dir,
    )
    print(f"Wrote public demo dataset: {output_path}")


if __name__ == "__main__":
    main()
