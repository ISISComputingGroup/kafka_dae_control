"""GPS Time utilities."""

import calendar
import unittest
from datetime import datetime, timedelta, timezone

import pytest

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


class TestCustomGPSTimestamp(unittest.TestCase):
    """Unit test to test the nanosecond to epoch conversion of GPS time."""

    def test_leap_year_day_60(self) -> None:
        """Test Day 60 in a leap year (2024) resolves to Feb 29."""
        # Year 2024 -> offset 24 (0x18). Day 60 -> 60 (0x03C).
        # word1 format: [Years:24-31][Days:15-23][Hours:10-14][Minutes:4-9][SecMSB:0-3]
        word1 = (24 << 24) | (60 << 15) | (0 << 10) | (0 << 4) | 0
        word2 = 0

        result_ns = nanoseconds_since_epoch(word1, word2)

        # Expected datetime: 2024-02-29 00:00:00 UTC
        expected_dt = datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc)
        expected_ns = int(
            (expected_dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()
            * 1_000_000_000
        )

        assert result_ns == expected_ns

    def test_non_leap_year_day_60(self) -> None:
        """Test Day 60 in a non-leap year (2023) resolves to March 1."""
        # Year 2023 -> offset 23 (0x17). Day 60 -> 60 (0x03C).
        word1 = (23 << 24) | (60 << 15) | (0 << 10) | (0 << 4) | 0
        word2 = 0

        result_ns = nanoseconds_since_epoch(word1, word2)

        # Expected datetime: 2023-03-01 00:00:00 UTC
        expected_dt = datetime(2023, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
        expected_ns = int(
            (expected_dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()
            * 1_000_000_000
        )

        assert result_ns == expected_ns

    def test_max_bitfield_values(self) -> None:
        """Test maximum allowable bitfield limits across all components."""
        # Year offset 255 -> 2255
        # Days 511 (max 9-bit)
        # Hours 31 (max 5-bit)
        # Minutes 63 (max 6-bit)
        # Sec MSB 15 (max 4-bit)
        # This should fail as max values are more than real life maximums.
        word1 = (0xFF << 24) | (0x1FF << 15) | (0x1F << 10) | (0x3F << 4) | 0x0F

        # Sec LSB 3 (max 2-bit -> total seconds = (15 << 2) | 3 = 63)
        # Milliseconds 1023 (max 10-bit)
        # Microseconds 1023 (max 10-bit)
        # Nanoseconds 1023 (max 10-bit)
        word2 = (0x3 << 30) | (0x3FF << 20) | (0x3FF << 10) | 0x3FF
        # Use context manager to assert ValueError is raised
        with pytest.raises(ValueError, match="Invalid day of year: 511 for 2255"):
            nanoseconds_since_epoch(word1, word2)

        word1 = (0xFF << 24) | (60 << 15) | (0x1F << 10) | (0x3F << 4) | 0x0F
        with pytest.raises(ValueError, match="Invalid hour: 31"):
            nanoseconds_since_epoch(word1, word2)

        word1 = (0xFF << 24) | (60 << 15) | (52 << 10) | (0x3F << 4) | 0x0F
        with pytest.raises(ValueError, match="Invalid minute: 63"):
            nanoseconds_since_epoch(word1, word2)


if __name__ == "__main__":
    unittest.main()
