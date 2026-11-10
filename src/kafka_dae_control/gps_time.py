"""GPS Time utilities."""
import calendar
from datetime import datetime, timezone, timedelta

def nanoseconds_since_epoch(gps_time_msb_word: int, gps_time_lsb_word: int) -> int:
    """Convert a gps_time_data pair to a time since epoch.

    Args:
        gps_time_msb_word: int: The GPS Timestamp First word.
        gps_time_lsb_word: int: The GPS Timestamp Second word.

    Returns: Nanoseconds since epoch.

    """
    
    years_offset = (gps_time_msb_word >> 24) & 0xFF
    year = 2000 + years_offset

    day_of_year = (gps_time_msb_word >> 15) & 0x1FF
    hour = (gps_time_msb_word >> 10) & 0x1F
    minute = (gps_time_msb_word >> 4) & 0x3F
    sec_msb = gps_time_msb_word & 0x0F  # Bits 0..3

    sec_lsb = (gps_time_lsb_word >> 30) & 0x03  # Bits 30..31
    milliseconds = (gps_time_lsb_word >> 20) & 0x3FF
    microseconds = (gps_time_lsb_word >> 10) & 0x3FF
    nanoseconds = gps_time_lsb_word & 0x3FF  # Bits 0..9

    seconds = (sec_msb << 2) | sec_lsb

    max_day = 366 if calendar.isleap(year) else 365
    if not 1 <= day_of_year <= max_day:
        raise ValueError(f"Invalid day of year: {day_of_year} for {year}")
 
    if not 0 <= hour <= 23:
        raise ValueError(f"Invalid hour: {hour}")

    if not 0 <= minute <= 59:
        raise ValueError(f"Invalid minute: {minute}")

    if not 0 <= seconds <= 59:
        raise ValueError(f"Invalid second: {seconds}")

    for name, value in (
        ("milliseconds", milliseconds),
        ("microseconds", microseconds),
        ("nanoseconds", nanoseconds),
    ):
        if not 0 <= value <= 999:
            raise ValueError(f"Invalid {name}: {value}")        

    base_date = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(
        days=int(day_of_year) - 1
    )

    full_datetime = base_date + timedelta(
        hours=int(hour),
        minutes=int(minute),
        seconds=int(seconds),
        milliseconds=int(milliseconds),
        microseconds=int(microseconds),
    )

    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = full_datetime - epoch
    total_seconds = delta.days * 86400 + delta.seconds
    nanos = total_seconds * 1_000_000_000 + delta.microseconds * 1_000 + nanoseconds

    return nanos

def format_timestamp(ns: int) -> str:
    seconds, nanoseconds = divmod(ns, 1_000_000_000)
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return f"{dt.strftime('%a %d-%b-%Y %H:%M:%S')}.{nanoseconds:09d}"
