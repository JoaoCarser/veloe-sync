from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict


def get_current_semester_period(reference: datetime | None = None) -> Dict[str, str]:
    today = reference or datetime.now()
    year = today.year
    month = today.month

    if month <= 6:
        start = datetime(year, 1, 1)
        semester = "1s"
    else:
        start = datetime(year, 7, 1)
        semester = "2s"

    yesterday = today - timedelta(days=1)

    return {
        "start_date": start.strftime("%d/%m/%Y"),
        "end_date": today.strftime("%d/%m/%Y"),
        "yesterday_date": yesterday.strftime("%d/%m/%Y"),
        "semester": semester,
        "current_year": str(year),
    }


def generate_date_windows(start_date: str, end_date: str, window_days: int) -> list[tuple[str, str]]:
    import pandas as pd

    start_ts = pd.to_datetime(start_date, dayfirst=True)
    end_ts = pd.to_datetime(end_date, dayfirst=True)
    windows: list[tuple[str, str]] = []

    current = start_ts
    while current <= end_ts:
        window_end = min(current + pd.Timedelta(days=window_days - 1), end_ts)
        windows.append((current.strftime("%d/%m/%Y"), window_end.strftime("%d/%m/%Y")))
        current = window_end + pd.Timedelta(days=1)

    return windows
