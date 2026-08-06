"""Bit-wise utilities."""

import numpy as np
from numpy import typing as npt


def array_to_mask(array: npt.NDArray[np.uint8]) -> int:
    """Convert a numpy array of boolean values to a bit mask.

    Args:
        array: The array to convert.

    Returns: A bit mask.

    """
    return int.from_bytes(np.packbits(array, bitorder="big"), "big")
