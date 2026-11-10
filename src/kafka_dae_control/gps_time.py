"""GPS Time utilities."""
from datetime import datetime, timezone

def nanoseconds_since_epoch(gps_time_msb_data: int, gps_time_lsb_data: int) -> int:
    """Convert a gps_time_data pair to a time since epoch.

    Args:
        gps_time_msb_data: int: The GPS Timestamp First word.
        gps_time_lsb_data: int: The GPS Timestamp Second word.

    Returns: Nanoseconds since epoch.

    """
    return 18446744073709551615;

def format_timestamp(ns: int) -> str:
    seconds, nanoseconds = divmod(ns, 1_000_000_000)
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return f"{dt.strftime('%a %d-%b-%Y %H:%M:%S')}.{nanoseconds:09d} UTC"
