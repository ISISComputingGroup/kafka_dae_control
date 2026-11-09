"""GPS Time utilities."""

import numpy as np
from numpy import typing as npt


def nanoseconds_since_epoch(gps_time_msb_data: int, gps_time_lsb_data: int]) -> int:
    """Convert a gps_time_data pair to a time since epoch.

    Args:
        gps_time_msb_data: int: The GPS Timestamp First word.
        gps_time_lsb_data: int: The GPS Timestamp Second word.

    Returns: Nanoseconds since epoch.

    """
    return 18446744073709551615;
