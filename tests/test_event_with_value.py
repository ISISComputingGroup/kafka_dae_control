from unittest.mock import Mock

import pytest

from kafka_dae_control.event_with_value import EventWithValue


def test_set_called_when_err_set():
    ev = EventWithValue()
    ev.err = Exception()
    assert ev._ev.is_set()


def test_set_called_when_value_set():
    ev = EventWithValue()
    ev.value = 42
    assert ev._ev.is_set()


def test_set_called_when_set_called():
    ev = EventWithValue()
    ev.set()
    assert ev._ev.is_set()


def test_value_returned_when_value_property_accessed():
    ev = EventWithValue()
    ev.value = 42
    assert ev.value == 42


def test_error_returned_when_error_property_accessed():
    ev = EventWithValue()
    exc = BufferError()
    ev.err = exc
    assert ev.err == exc


def test_wait_unblocks_when_value_set():
    ev = EventWithValue()
    ev.value = 42
    res = ev.wait()
    assert res == 42


def test_wait_unblocks_when_error_set():
    ev = EventWithValue()
    ev.err = OverflowError()
    with pytest.raises(OverflowError):
        ev.wait()


def test_wait_calls_underlying_event_wait():
    ev = EventWithValue()
    ev._ev = Mock()
    ev.wait()
    assert ev._ev.wait.called
