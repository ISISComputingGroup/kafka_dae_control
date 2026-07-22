"""Bitwise utilities."""

import numpy as np
from numpy import typing as npt


def mask_to_array(mask: int) -> npt.NDArray[np.uint8]:
    """Convert a bit mask to a numpy array of boolean values.

    Args:
        mask: The bitmask to convert.

    Returns: A numpy array of boolean bit values.

    """
    return np.unpackbits(np.frombuffer(mask.to_bytes(4, "big"), dtype=np.uint8), bitorder="big")


def array_to_mask(array: npt.NDArray[np.uint8]) -> int:
    """Convert a numpy array of booleans to a bit mask.

    Args:
        array: The array to convert.

    Returns: A bitmask.

    """
    return int.from_bytes(np.packbits(array, bitorder="big"), "big")
