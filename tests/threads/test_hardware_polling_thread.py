import logging
from queue import PriorityQueue
from threading import RLock
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.defaults import (
    FrameSyncSelect,
    PeriodControlFlags,
    PeriodMode,
    Registers,
    RunRegister,
)
from kafka_dae_control.queue_utils import QueueItem
from kafka_dae_control.threads.hardware_polling_thread import hardware_poll_thread
from kafka_dae_control.worker_event_types import HardwareUpdate, SetIPEvent
from tests.conftest import (
    PERIOD_COMP_CURRENT_ADDRESS,
    PERIOD_CONTROL_ADDRESS,
    PERIOD_NUMBER_LIMIT_ADDRESS,
)


@patch("kafka_dae_control.threads.hardware_polling_thread.sleep", side_effect=Exception)
@patch(
    "kafka_dae_control.threads.hardware_polling_thread.read",
    side_effect=[
        RunRegister.STATUS_RUNNING,
        0x1,
        0b0001,
        2,
        3,
        PeriodControlFlags.END_RUN_AT_END_OF_PERIOD_SEQUENCE | PeriodControlFlags.MODE_EXTERNAL,
    ],
)
def test_reads_work_and_put_event_on_queue(mock_read: Mock, mock_sleep: Mock, conf: ControlConfig):
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    queue = PriorityQueue[QueueItem]()
    with pytest.raises(Exception):  # ruff:ignore[assert-raises-exception, pytest-raises-too-broad]
        hardware_poll_thread(conf, queue, sock, sock_lock)

    mock_read.assert_has_calls(
        calls=[
            call(
                sock,
                conf.board_ip,
                address=conf.register_map[Registers.RUNNING_REGISTER],
                port=conf.read_port,
            ),
            call(
                sock,
                conf.board_ip,
                address=conf.register_map[Registers.FRAME_SYNC_SEL_REGISTER],
                port=conf.read_port,
            ),
            call(
                sock,
                conf.board_ip,
                address=conf.register_map[Registers.VETO_CONTROL_REGISTER],
                port=conf.read_port,
            ),
            call(sock, conf.board_ip, address=PERIOD_COMP_CURRENT_ADDRESS, port=conf.read_port),
            call(sock, conf.board_ip, address=PERIOD_NUMBER_LIMIT_ADDRESS, port=conf.read_port),
            call(sock, conf.board_ip, address=PERIOD_CONTROL_ADDRESS, port=conf.read_port),
        ]
    )
    assert sock_lock.__enter__.called
    assert queue.qsize() == 1
    assert queue.get().item.value == HardwareUpdate(  # pyright: ignore reportAttributeAccessIssue
        hw_running=True,
        frame_sync_select=FrameSyncSelect(1),
        hard_vetoes=1,
        period_comp_current=2,
        period_number_limit=3,
        period_mode=PeriodMode.EXTERNAL,
    )


@patch("kafka_dae_control.threads.hardware_polling_thread.sleep", side_effect=Exception)
@patch(
    "kafka_dae_control.threads.hardware_polling_thread.read",
    side_effect=[
        RunRegister.STATUS_RUNNING,
        1234,
        0b0001,
        0,
        0,
        0,
    ],
)
def test_read_frame_sync_select_invalid_sets_invalid(
    mock_read: Mock, mock_sleep: Mock, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    queue = PriorityQueue[QueueItem]()
    with pytest.raises(Exception):  # ruff:ignore[assert-raises-exception, pytest-raises-too-broad]
        hardware_poll_thread(conf, queue, sock, sock_lock)

    assert sock_lock.__enter__.called
    assert queue.qsize() == 1
    assert queue.get().item.value == HardwareUpdate(  # pyright: ignore reportAttributeAccessIssue
        hw_running=True,
        frame_sync_select=FrameSyncSelect.UNKNOWN,
        hard_vetoes=1,
        period_comp_current=0,
        period_mode=PeriodMode.COMPUTER,
        period_number_limit=0,
    )


@patch("kafka_dae_control.threads.hardware_polling_thread.sleep", side_effect=Exception)
@patch(
    "kafka_dae_control.threads.hardware_polling_thread.read",
    side_effect=[RunRegister.STATUS_RUNNING, FrameSyncSelect.UNKNOWN, 0, 0, 0, 9999999, 0],
)
def test_period_mode_invalid_sets_unknown(
    mock_read: Mock, mock_sleep: Mock, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    queue = PriorityQueue[QueueItem]()
    with pytest.raises(Exception):  # ruff:ignore[assert-raises-exception, pytest-raises-too-broad]
        hardware_poll_thread(conf, queue, sock, sock_lock)

    assert sock_lock.__enter__.called
    assert queue.qsize() == 1
    assert queue.get().item.value.period_mode == PeriodMode.UNKNOWN  # pyright: ignore reportAttributeAccessIssue


@patch("kafka_dae_control.threads.hardware_polling_thread.sleep", side_effect=Exception)
@patch("kafka_dae_control.threads.hardware_polling_thread.read", side_effect=Exception)
def test_read_throws_exception_logs(
    mock_read: Mock, mock_sleep: Mock, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    queue = PriorityQueue[QueueItem]()

    with pytest.raises(Exception):  # ruff:ignore[assert-raises-exception, pytest-raises-too-broad]
        hardware_poll_thread(conf, queue, sock, sock_lock)

    assert "Error occurred when polling hardware: " in caplog.text


@patch(
    "kafka_dae_control.threads.hardware_polling_thread.sleep",
    side_effect=[None, None, None, Exception],
)
@patch("kafka_dae_control.threads.hardware_polling_thread.poll_hardware", return_value=False)
def test_many_comms_errors_in_a_row_cause_ip_to_be_resent(
    mock_read: Mock, mock_sleep: Mock, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    conf.resend_ip_after_connection_failures = 3

    queue = PriorityQueue[QueueItem]()
    sock = MagicMock()
    sock_lock = MagicMock(spec=RLock())

    caplog.set_level(logging.DEBUG)

    with pytest.raises(Exception):  # ruff:ignore[assert-raises-exception, pytest-raises-too-broad]
        hardware_poll_thread(conf, queue, sock, sock_lock)

    assert "1 comms errors in a row while polling hardware" in caplog.text
    assert "2 comms errors in a row while polling hardware" in caplog.text
    assert "3 comms errors in a row while polling hardware" in caplog.text
    assert "Attempting to resend local IP to streaming control board to recover" in caplog.text

    assert isinstance(queue.get().item, SetIPEvent)
