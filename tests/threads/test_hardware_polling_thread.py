from queue import Queue
from threading import RLock
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.defaults import (
    FrameSyncSelect,
    RunRegister,
)
from kafka_dae_control.threads.hardware_polling_thread import hardware_poll_thread
from kafka_dae_control.worker_event import HardwareUpdate


@patch("kafka_dae_control.threads.hardware_polling_thread.sleep", side_effect=Exception)
@patch(
    "kafka_dae_control.threads.hardware_polling_thread.read",
    side_effect=[RunRegister.STATUS_RUNNING, 0x1],
)
def test_reads_work_and_put_event_on_queue(mock_read: Mock, mock_sleep: Mock, conf: ControlConfig):
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    queue = Queue()
    with pytest.raises(Exception):  # noqa: B017, PT011
        hardware_poll_thread(conf, queue, sock, sock_lock)

    mock_read.assert_has_calls(
        calls=[
            call(
                sock,
                conf.board_ip,
                0,
                port=conf.read_port,
            ),
            call(
                sock,
                conf.board_ip,
                4,
                port=conf.read_port,
            ),
        ]
    )
    assert sock_lock.__enter__.called
    assert queue.qsize() == 1
    assert queue.get().value == HardwareUpdate(
        hw_running=True, frame_sync_select=FrameSyncSelect(1)
    )


@patch("kafka_dae_control.threads.hardware_polling_thread.sleep", side_effect=Exception)
@patch(
    "kafka_dae_control.threads.hardware_polling_thread.read",
    side_effect=[RunRegister.STATUS_RUNNING, 1234],
)
def test_read_frame_sync_select_invalid_sets_invalid(
    mock_read: Mock, mock_sleep: Mock, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    queue = Queue()
    with pytest.raises(Exception):  # noqa: B017, PT011
        hardware_poll_thread(conf, queue, sock, sock_lock)

    assert sock_lock.__enter__.called
    assert queue.qsize() == 1
    assert queue.get().value == HardwareUpdate(
        hw_running=True, frame_sync_select=FrameSyncSelect.UNKNOWN
    )


@patch("kafka_dae_control.threads.hardware_polling_thread.sleep", side_effect=Exception)
@patch("kafka_dae_control.threads.hardware_polling_thread.read", side_effect=Exception)
def test_read_throws_exception_logs(
    mock_read: Mock, mock_sleep: Mock, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    queue = Queue()

    with pytest.raises(Exception):  # noqa: B017, PT011
        hardware_poll_thread(conf, queue, sock, sock_lock)

    assert "Error occurred when polling hardware: " in caplog.text
