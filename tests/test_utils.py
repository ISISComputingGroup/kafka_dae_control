import numpy as np

from kafka_dae_control.utils import array_to_mask


def test_array_to_mask():
    array = np.asarray(
        [
            0,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
        ],
        dtype=np.uint8,
    )
    assert array_to_mask(array) == 0b0100_0000_0000_0000_0000_0000_0000_0001
