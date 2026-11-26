from datetime import UTC, datetime

import pytest

from kafka_dae_control.gps_time import format_timestamp, nanoseconds_since_epoch


def test_when_msb_and_lsb_are_zero() -> None:
    """Test both words being 0 resolves to 0."""
    word1 = 0
    word2 = 0

    result_ns = nanoseconds_since_epoch(word1, word2)
    assert result_ns == 0


def test_leap_year_day_60() -> None:
    """Test Day 60 in a leap year (2024) resolves to Feb 29."""
    # Year 2024 -> offset 24 (0x18). Day 60 -> 60 (0x03C).
    # word1 format: [Years:24-31][Days:15-23][Hours:10-14][Minutes:4-9][SecMSB:0-3]
    word1 = (24 << 24) | (60 << 15) | (0 << 10) | (0 << 4) | 0
    word2 = 0

    result_ns = nanoseconds_since_epoch(word1, word2)

    # Expected datetime: 2024-02-29 00:00:00 UTC
    expected_dt = datetime(2024, 2, 29, 0, 0, 0, tzinfo=UTC)
    expected_ns = int(
        (expected_dt - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds() * 1_000_000_000
    )

    assert result_ns == expected_ns


def test_non_leap_year_day_60() -> None:
    """Test Day 60 in a non-leap year (2023) resolves to March 1."""
    # Year 2023 -> offset 23 (0x17). Day 60 -> 60 (0x03C).
    word1 = (23 << 24) | (60 << 15) | (0 << 10) | (0 << 4) | 0
    word2 = 0

    result_ns = nanoseconds_since_epoch(word1, word2)

    # Expected datetime: 2023-03-01 00:00:00 UTC
    expected_dt = datetime(2023, 3, 1, 0, 0, 0, tzinfo=UTC)
    expected_ns = int(
        (expected_dt - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds() * 1_000_000_000
    )

    assert result_ns == expected_ns


def test_max_bitfield_values() -> None:
    """Test maximum allowable bitfield limits across all components."""
    # Year offset 255 -> 2255
    # Days 511 (max 9-bit)
    # Hours 31 (max 5-bit)
    # Minutes 63 (max 6-bit)
    # Sec MSB 15 (max 4-bit)
    # This should fail as max values are more than real life maximums.
    word1 = (0xFF << 24) | (0x1FF << 15) | (0x1F << 10) | (0x3F << 4) | 0x0F
    word2 = (0x3 << 30) | (0x3FF << 20) | (0x3FF << 10) | 0x3FF

    # assert ValueError is raised
    with pytest.raises(ValueError, match="Invalid day of year: 511 for 2255"):
        nanoseconds_since_epoch(word1, word2)

    word1 = (0xFF << 24) | (60 << 15) | (0x1F << 10) | (0x3F << 4) | 0x0F
    with pytest.raises(ValueError, match="Invalid hour: 31"):
        nanoseconds_since_epoch(word1, word2)

    word1 = (0xFF << 24) | (60 << 15) | (12 << 10) | (0x3F << 4) | 0x0F
    with pytest.raises(ValueError, match="Invalid minute: 63"):
        nanoseconds_since_epoch(word1, word2)

    word1 = (0xFF << 24) | (60 << 15) | (12 << 10) | (0x2F << 4) | 0x0F
    word2 = (0x3 << 30) | (0x3FF << 20) | (0x3FF << 10) | 0x3FF
    with pytest.raises(ValueError, match="Invalid second: 63"):
        nanoseconds_since_epoch(word1, word2)

    word2 = (0x0 << 30) | (0x3FF << 20) | (0x3FF << 10) | 0x3FF
    with pytest.raises(ValueError, match="Invalid milliseconds: 1023"):
        nanoseconds_since_epoch(word1, word2)

    word2 = (0x0 << 30) | (0x2FF << 20) | (0x3FF << 10) | 0x3FF
    with pytest.raises(ValueError, match="Invalid microseconds: 1023"):
        nanoseconds_since_epoch(word1, word2)

    word2 = (0x0 << 30) | (0x2FF << 20) | (0x2FF << 10) | 0x3FF
    with pytest.raises(ValueError, match="Invalid nanoseconds: 1023"):
        nanoseconds_since_epoch(word1, word2)


def test_format_timestamp() -> None:
    """Test formatting nanoseconds since epoch into the expected readable string."""
    # 2024-01-01 00:00:00 UTC = 1704067200 seconds since epoch
    seconds = 1704067200
    nanos = 123
    total_nanos = (seconds * 1_000_000_000) + nanos
    result = format_timestamp(total_nanos)
    expected = "Mon 01-Jan-2024 00:00:00.000000123"

    assert result == expected
