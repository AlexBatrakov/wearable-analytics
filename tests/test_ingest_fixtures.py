from pathlib import Path

import pandas as pd

from garmin_analytics.ingest.sleep import COLUMNS as SLEEP_COLUMNS
from garmin_analytics.ingest.sleep import parse_sleep_files
from garmin_analytics.ingest.uds import COLUMNS as UDS_COLUMNS
from garmin_analytics.ingest.uds import parse_uds_files


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_parse_uds_fixture() -> None:
    df = parse_uds_files([FIXTURES / "uds_sample.json"])
    assert list(df.columns) == UDS_COLUMNS
    assert len(df) == 1
    assert pd.notna(df.loc[0, "calendarDate"])


def test_parse_sleep_fixture() -> None:
    df = parse_sleep_files([FIXTURES / "sleep_sample.json"])
    assert list(df.columns) == SLEEP_COLUMNS
    assert len(df) == 1
    assert pd.notna(df.loc[0, "calendarDate"])
