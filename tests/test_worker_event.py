# pyright: ignore
from unittest.mock import Mock, patch

import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import FrameSyncSelect
from kafka_dae_control.worker_event import (
    BeginEvent,
    BlocksUpdateEvent,
    EndEvent,
    FrameSyncSelectChangeEvent,
    HardwareUpdate,
    HardwareUpdateEvent,
    SetIPEvent,
    TitleUpdateEvent,
    UsersUpdateEvent,
    process_worker_event,
)


@pytest.mark.parametrize(
    ("event", "value", "data_var"),
    [
        (UsersUpdateEvent, "Tony Hawk", "users"),
        (TitleUpdateEvent, "A title", "title"),
        (BlocksUpdateEvent, ["ABLOCK"], "blocks"),
    ],
)
def test_process_worker_event_with_basic_value_update(
    event: type[UsersUpdateEvent | TitleUpdateEvent | BlocksUpdateEvent],
    value: str | list[str],
    data_var: str,
    data: Data,
    conf: ControlConfig,
):

    process_worker_event(event(value), conf, data, Mock(), Mock(), Mock())  # pyright: ignore[reportArgumentType]

    assert getattr(data, data_var) == value


@patch("kafka_dae_control.worker_event.handle_begin")
def test_process_begin_calls_handle_begin(mock_handle_begin: Mock, conf: ControlConfig, data: Data):
    process_worker_event(BeginEvent(Mock()), conf, data, Mock(), Mock(), Mock())
    assert mock_handle_begin.called


@patch("kafka_dae_control.worker_event.handle_end")
def test_process_end_calls_handle_end(mock_handle_end: Mock, conf: ControlConfig, data: Data):
    process_worker_event(EndEvent(Mock()), conf, data, Mock(), Mock(), Mock())
    assert mock_handle_end.called


@patch("kafka_dae_control.worker_event.set_board_response_ip")
def test_process_set_ip_calls_set_board_response_ip(
    mock_set_board_response_ip: Mock, conf: ControlConfig, data: Data
):
    process_worker_event(SetIPEvent(), conf, data, Mock(), Mock(), Mock())
    assert mock_set_board_response_ip.called


def test_unknown_value_logs(conf: ControlConfig, data: Data, caplog: pytest.LogCaptureFixture):
    process_worker_event("blah", conf, data, Mock(), Mock(), Mock())  # pyright: ignore[reportArgumentType]
    assert "Unknown event type: blah" in caplog.text


@patch("kafka_dae_control.worker_event.set_board_response_ip", side_effect=IOError)
def test_exception_thrown_in_handler_logs(
    m: Mock, conf: ControlConfig, data: Data, caplog: pytest.LogCaptureFixture
):
    process_worker_event(SetIPEvent(), conf, data, Mock(), Mock(), Mock())
    assert "Unhandled exception in handler thread:" in caplog.text


def test_hardware_update_event_sets_data(conf: ControlConfig, data: Data):
    data.running = False
    process_worker_event(
        HardwareUpdateEvent(
            value=HardwareUpdate(
                hw_running=True, frame_sync_select=FrameSyncSelect.INTERNAL_TEST_CLOCK
            )
        ),
        conf,
        data,
        Mock(),
        Mock(),
        Mock(),
    )
    assert data.running
    assert data.frame_sync_select_rbv == FrameSyncSelect.INTERNAL_TEST_CLOCK


@patch("kafka_dae_control.worker_event.handle_frame_sync_sp_change")
def test_frame_sync_select_change_calls_handle_frame_sync_sp_change(
    mock_handle_frame_sync_sp_change: Mock,
    conf: ControlConfig,
    data: Data,
):
    process_worker_event(
        FrameSyncSelectChangeEvent(value=FrameSyncSelect.INTERNAL_TEST_CLOCK, done_event=Mock()),
        conf,
        data,
        Mock(),
        Mock(),
        Mock(),
    )
    assert mock_handle_frame_sync_sp_change.called
