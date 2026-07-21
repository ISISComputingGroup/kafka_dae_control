import pytest

from kafka_dae_control.utils import or_two_int_lists


def test_all_vetoes():
    x = [0, 1, 0, 1]
    y = [1, 0, 1, 0]

    assert or_two_int_lists(x, y) == 0b1111


def test_lists_with_different_lengths_raises():
    x = [0, 1, 0]
    y = [0, 1]

    with pytest.raises(ValueError):  # ruff:ignore[pytest-raises-too-broad], this is really testing zip()'s assertion gets propagated.
        or_two_int_lists(x, y)
