from unittest.mock import patch

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


@patch("kafka_dae_control.event_with_error.threading.Event.wait")
def test_wait_does_not_raise_when_no_error_set(mock_super_wait):
    ev = EventWithError()
    ev.err = None
    ev.wait()
    assert mock_super_wait.called
