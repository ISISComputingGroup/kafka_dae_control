import numpy as np

from kafka_dae_control.utils import array_to_mask, mask_to_array


def test_mask_to_array():
    mask = 0b1010_0000_0000_0000_0000_0000_0000_0101
    assert (
        mask_to_array(mask)
        == np.asarray(
            [
                1,
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
                1,
                0,
                1,
            ],
            dtype=np.bool,
        )
    ).all()


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
        dtype=np.bool,
    )
    assert array_to_mask(array) == 0b0100_0000_0000_0000_0000_0000_0000_0001
