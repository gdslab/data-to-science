"""Date parsing utilities for handling various date formats."""

from datetime import datetime, date
from typing import Union


def parse_date(date_str: Union[str, datetime, date]) -> datetime:
    """Parse a date string into a datetime object, handling various formats.

    Args:
        date_str: Date string or datetime/date object to parse

    Returns:
        datetime: Parsed datetime object

    Raises:
        ValueError: If date string cannot be parsed
    """
    if isinstance(date_str, (datetime, date)):
        return (
            date_str
            if isinstance(date_str, datetime)
            else datetime.combine(date_str, datetime.min.time())
        )

    # Try common date formats
    formats = [
        "%Y-%m-%d %H:%M:%S",  # 2024-01-17 14:30:00
        "%Y-%m-%d",  # 2024-01-17
        "%m/%d/%Y",  # 1/17/2024
        "%m/%d/%Y %H:%M:%S",  # 1/17/2024 14:30:00
        "%d/%m/%Y",  # 17/1/2024
        "%d/%m/%Y %H:%M:%S",  # 17/1/2024 14:30:00
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Could not parse date string: {date_str}")
