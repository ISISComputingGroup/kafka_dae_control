"""GPS Time utilities."""

import calendar
from datetime import datetime, timedelta, timezone

MAX_HOURS_IN_A_DAY = 24
MAX_MINUTES_IN_A_HOUR = 60
MAX_SECONDS_IN_A_MINUTE = 60
MAX_SUB_SECONDS = 999


def nanoseconds_since_epoch(gps_time_msb_word: int, gps_time_lsb_word: int) -> int:
    """Convert a gps_time_data pair to a time since epoch.

    Args:
        gps_time_msb_word: int: The GPS Timestamp First word.
        gps_time_lsb_word: int: The GPS Timestamp Second word.

    Returns: Nanoseconds since epoch.

    """
    year = 2000 + ((gps_time_msb_word >> 24) & 0xFF)

    day_of_year = (gps_time_msb_word >> 15) & 0x1FF
    hour = (gps_time_msb_word >> 10) & 0x1F
    minute = (gps_time_msb_word >> 4) & 0x3F
    seconds = ((gps_time_msb_word & 0x0F) << 2) | ((gps_time_lsb_word >> 30) & 0x03)
    milliseconds = (gps_time_lsb_word >> 20) & 0x3FF
    microseconds = (gps_time_lsb_word >> 10) & 0x3FF
    nanoseconds = gps_time_lsb_word & 0x3FF  # Bits 0..9

    max_day = 366 if calendar.isleap(year) else 365
    if not 1 <= day_of_year <= max_day:
        raise ValueError(f"Invalid day of year: {day_of_year} for {year}")

    if not 0 <= hour < MAX_HOURS_IN_A_DAY:
        raise ValueError(f"Invalid hour: {hour}")

    if not 0 <= minute < MAX_MINUTES_IN_A_HOUR:
        raise ValueError(f"Invalid minute: {minute}")

    if (
        not 0 <= seconds <= MAX_SECONDS_IN_A_MINUTE
    ):  # Generally 59, but 60 possible in the case of a leap second
        raise ValueError(f"Invalid second: {seconds}")

    for name, value in (
        ("milliseconds", milliseconds),
        ("microseconds", microseconds),
        ("nanoseconds", nanoseconds),
    ):
        if not 0 <= value <= MAX_SUB_SECONDS:
            raise ValueError(f"Invalid {name}: {value}")

    base_date = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(
        days=int(day_of_year) - 1,
        hours=int(hour),
        minutes=int(minute),
        seconds=int(seconds),
        milliseconds=int(milliseconds),
        microseconds=int(microseconds),
    )

    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = base_date - epoch
    total_seconds = delta.days * 86400 + delta.seconds
    nanos = total_seconds * 1_000_000_000 + delta.microseconds * 1_000 + nanoseconds

    return nanos


def format_timestamp(nanos_since_epoch: int) -> str:
    """Format a timestamp in nanoseconds to readable date and time.

    Args:
        nanos_since_epoch: int: The timestamp in nanoseconds.

    Returns: Human-readable date and time.

    """
    seconds, nanoseconds = divmod(nanos_since_epoch, 1_000_000_000)
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return f"{dt.strftime('%a %d-%b-%Y %H:%M:%S')}.{nanoseconds:09d}"
