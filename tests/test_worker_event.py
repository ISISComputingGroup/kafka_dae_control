# pyright: ignore
from queue import PriorityQueue
from unittest.mock import Mock, patch

import numpy as np
import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import NUM_VETOES, FrameSyncSelect, PeriodMode
from kafka_dae_control.process_worker_event import process_worker_event
from kafka_dae_control.queue_utils import QueueItem
from kafka_dae_control.worker_event_types import (
    BeginEvent,
    BlocksUpdateEvent,
    CurrentPeriodSetEvent,
    EndEvent,
    FrameSyncSelectChangeEvent,
    HardwareUpdate,
    HardwareUpdateEvent,
    NumberOfPeriodsSetEvent,
    PauseResumeEvent,
    PeriodModeSetEvent,
    RunControlUpdateEvent,
    SetIPEvent,
    VetoesUpdateEvent,
)


@pytest.mark.parametrize(
    ("event", "value", "data_var"),
    [
        (BlocksUpdateEvent, ["ABLOCK"], "blocks"),
    ],
)
def test_process_worker_event_with_basic_value_update(
    event: type[BlocksUpdateEvent],
    value: str | list[str],
    data_var: str,
    data: Data,
    conf: ControlConfig,
):

    process_worker_event(
        PriorityQueue[QueueItem](),
        event(value),  # pyright: ignore[reportArgumentType]
        conf,
        data,
        Mock(),
        Mock(),
        Mock(),
    )

    assert getattr(data, data_var) == value


@patch("kafka_dae_control.process_worker_event.handle_begin")
def test_process_begin_calls_handle_begin(mock_handle_begin: Mock, conf: ControlConfig, data: Data):
    process_worker_event(
        PriorityQueue[QueueItem](), BeginEvent(Mock()), conf, data, Mock(), Mock(), Mock()
    )
    assert mock_handle_begin.called


@patch("kafka_dae_control.process_worker_event.handle_end")
def test_process_end_calls_handle_end(mock_handle_end: Mock, conf: ControlConfig, data: Data):
    process_worker_event(
        PriorityQueue[QueueItem](), EndEvent(Mock()), conf, data, Mock(), Mock(), Mock()
    )
    assert mock_handle_end.called


@patch("kafka_dae_control.process_worker_event.set_board_response_ip")
def test_process_set_ip_calls_set_board_response_ip(
    mock_set_board_response_ip: Mock, conf: ControlConfig, data: Data
):
    process_worker_event(
        PriorityQueue[QueueItem](), SetIPEvent(), conf, data, Mock(), Mock(), Mock()
    )
    assert mock_set_board_response_ip.called


def test_unknown_value_logs(conf: ControlConfig, data: Data, caplog: pytest.LogCaptureFixture):
    process_worker_event(PriorityQueue[QueueItem](), "blah", conf, data, Mock(), Mock(), Mock())  # pyright: ignore[reportArgumentType]
    assert "Unknown event type: blah" in caplog.text


@patch("kafka_dae_control.process_worker_event.set_board_response_ip", side_effect=IOError)
def test_exception_thrown_in_handler_logs(
    m: Mock, conf: ControlConfig, data: Data, caplog: pytest.LogCaptureFixture
):
    process_worker_event(
        PriorityQueue[QueueItem](), SetIPEvent(), conf, data, Mock(), Mock(), Mock()
    )
    assert "Unhandled exception in handler thread:" in caplog.text


def test_hardware_update_event_sets_data(conf: ControlConfig, data: Data):
    data.running = False
    process_worker_event(
        PriorityQueue[QueueItem](),
        HardwareUpdateEvent(
            value=HardwareUpdate(
                hw_running=True,
                frame_sync_select=FrameSyncSelect.INTERNAL_TEST_CLOCK,
                hard_vetoes=0b10001,
                period_comp_current=12,
                period_number_limit=13,
                period_mode=PeriodMode.COMPUTER,
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
    assert data.hard_vetoes_rbv == 0b10001
    assert data.period_mode_rbv == PeriodMode.COMPUTER
    assert data.current_period_rbv == 13
    assert data.num_periods_rbv == 13


@patch("kafka_dae_control.process_worker_event.set_num_periods")
def test_set_number_periods_event_calls_set_num_periods(
    mock_set_num_periods: Mock,
    conf: ControlConfig,
    data: Data,
):
    process_worker_event(
        PriorityQueue[QueueItem](),
        NumberOfPeriodsSetEvent(value=15, done_event=Mock()),
        conf,
        data,
        Mock(),
        Mock(),
        Mock(),
    )
    assert mock_set_num_periods.called
    assert mock_set_num_periods.call_args[0][0] == 15


@patch("kafka_dae_control.process_worker_event.set_current_period")
def test_set_current_period_event_calls_set_current_period(
    mock_set_current_period: Mock,
    conf: ControlConfig,
    data: Data,
):
    process_worker_event(
        PriorityQueue[QueueItem](),
        CurrentPeriodSetEvent(value=16, done_event=Mock()),
        conf,
        data,
        Mock(),
        Mock(),
        Mock(),
    )
    assert mock_set_current_period.called
    assert mock_set_current_period.call_args[0][0] == 16


@patch("kafka_dae_control.process_worker_event.set_period_mode")
def test_set_period_mode_sets_calls_set_period_mode(
    mock_set_period_mode: Mock, conf: ControlConfig, data: Data
):
    process_worker_event(
        PriorityQueue[QueueItem](),
        PeriodModeSetEvent(value=PeriodMode.LOOK_UP_TABLE, done_event=Mock()),
        conf,
        data,
        Mock(),
        Mock(),
        Mock(),
    )
    assert mock_set_period_mode.called
    assert mock_set_period_mode.call_args[0][0] == PeriodMode.LOOK_UP_TABLE


@patch("kafka_dae_control.process_worker_event.handle_frame_sync_sp_change")
def test_frame_sync_select_change_calls_handle_frame_sync_sp_change(
    mock_handle_frame_sync_sp_change: Mock,
    conf: ControlConfig,
    data: Data,
):
    process_worker_event(
        PriorityQueue[QueueItem](),
        FrameSyncSelectChangeEvent(value=FrameSyncSelect.INTERNAL_TEST_CLOCK, done_event=Mock()),
        conf,
        data,
        Mock(),
        Mock(),
        Mock(),
    )
    assert mock_handle_frame_sync_sp_change.called
    assert mock_handle_frame_sync_sp_change.call_args[0][0] == FrameSyncSelect.INTERNAL_TEST_CLOCK


@patch("kafka_dae_control.process_worker_event.handle_vetoes_change")
def test_soft_vetoes_change_calls_handle_soft_vetoes_change(
    mock_handle_vetoes_change: Mock, conf: ControlConfig, data: Data
):
    process_worker_event(
        PriorityQueue[QueueItem](),
        VetoesUpdateEvent(value=np.zeros(NUM_VETOES, dtype=np.uint8), done_event=Mock()),
        conf,
        data,
        Mock(),
        Mock(),
        Mock(),
    )
    assert mock_handle_vetoes_change.called


@patch("kafka_dae_control.process_worker_event.handle_run_control_update")
def test_run_control_change_calls_handle_run_control_update(
    mock_handle_run_control_update: Mock, conf: ControlConfig, data: Data
):
    process_worker_event(
        PriorityQueue[QueueItem](),
        RunControlUpdateEvent(value=False),
        conf,
        data,
        Mock(),
        Mock(),
        Mock(),
    )
    assert mock_handle_run_control_update.called


@patch("kafka_dae_control.process_worker_event.handle_pause_or_resume")
def test_pause_resume_calls_handle_pause_or_resume(
    mock_handle_pause_or_resume: Mock, conf: ControlConfig, data: Data
):
    process_worker_event(
        PriorityQueue[QueueItem](),
        PauseResumeEvent(value=False, done_event=Mock()),
        conf,
        data,
        Mock(),
        Mock(),
        Mock(),
    )
    assert mock_handle_pause_or_resume.called
