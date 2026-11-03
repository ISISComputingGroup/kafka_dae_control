"""Bit-wise utilities."""

import numpy as np
from numpy import typing as npt


def array_to_mask(array: npt.NDArray[np.uint8]) -> int:
    """Convert a numpy array of boolean values to a bit mask.

    Args:
        array: The array to convert. Element `N` of this array corresponds
            to the output bit position masked by `(1 << N)`.

    Returns: A bit mask.

    """
    return int.from_bytes(np.packbits(array[::-1], bitorder="big"), "big")
