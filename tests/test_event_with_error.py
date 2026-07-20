from unittest.mock import Mock

import pytest

from kafka_dae_control.event_with_error import EventWithError


def test_set_called_when_err_set():
    ev = EventWithError()
    ev.err = Exception()
    assert ev.is_set()


def test_error_returned_when_error_property_accessed():
    ev = EventWithError()
    exc = BufferError()
    ev.err = exc
    assert ev.err == exc


def test_wait_unblocks_when_error_set():
    ev = EventWithError()
    ev.err = OverflowError()
    with pytest.raises(OverflowError):
        ev.wait()
