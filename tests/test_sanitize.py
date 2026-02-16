from __future__ import annotations

import pandas as pd

from garmin_analytics.sanitize import sanitize_dataframe


def test_sanitize_drops_identifiers_and_metadata() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-15"],
            "totalSteps": [12345],
            "uuid": ["99e8b35af9c44d238186246e83e97d65"],
            "userProfilePK": [113615659],
            "allDayStress_userProfilePK": [113615659],
            "version": [85140002],
            "source": [0],
            "someGuidLike": ["e765803f-76ee-4466-a7a2-70f767b2e0e7"],
        }
    )

    out, report = sanitize_dataframe(df)

    assert "calendarDate" in out.columns
    assert "totalSteps" in out.columns
    for col in [
        "uuid",
        "userProfilePK",
        "allDayStress_userProfilePK",
        "version",
        "source",
        "someGuidLike",
    ]:
        assert col not in out.columns
        assert col in report["dropped_columns"]


def test_keep_allows_metadata_but_not_identifiers() -> None:
    df = pd.DataFrame(
        {
            "calendarDate": ["2025-01-15"],
            "totalSteps": [12345],
            "uuid": ["99e8b35af9c44d238186246e83e97d65"],
            "source": [0],
        }
    )

    out, _report = sanitize_dataframe(df, keep=["source", "uuid"])
    assert "calendarDate" in out.columns
    assert "totalSteps" in out.columns
    assert "source" in out.columns
    assert "uuid" not in out.columns
