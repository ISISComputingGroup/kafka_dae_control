from queue import Queue
from threading import RLock
from unittest.mock import MagicMock, Mock, patch

import pytest
from _pytest.logging import LogCaptureFixture

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.defaults import RUNNING_REGISTER, RunRegister
from kafka_dae_control.threads.hardware_polling_thread import hardware_poll_thread
from kafka_dae_control.worker_event import HardwareUpdate


@patch("kafka_dae_control.threads.hardware_polling_thread.sleep", side_effect=Exception)
@patch(
    "kafka_dae_control.threads.hardware_polling_thread.read",
    return_value=RunRegister.STATUS_RUNNING,
)
def test_reads_work_and_put_event_on_queue(mock_read: Mock, mock_sleep: Mock, conf: ControlConfig):
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    queue = Queue()
    with pytest.raises(Exception):  # noqa: B017, PT011
        hardware_poll_thread(conf, queue, sock, sock_lock)
    mock_read.assert_called_once_with(
        sock,
        conf.board_ip,
        RUNNING_REGISTER.address,
        RUNNING_REGISTER.size,
        conf.read_port,
    )
    assert sock_lock.__enter__.called
    assert queue.qsize() == 1
    assert queue.get().value == HardwareUpdate(hw_running=True)


@patch("kafka_dae_control.threads.hardware_polling_thread.sleep", side_effect=Exception)
@patch("kafka_dae_control.threads.hardware_polling_thread.read", side_effect=Exception)
def test_read_throws_exception_logs(
    mock_read: Mock, mock_sleep: Mock, conf: ControlConfig, caplog: LogCaptureFixture
):
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    queue = Queue()

    with pytest.raises(Exception):  # noqa: B017, PT011
        hardware_poll_thread(conf, queue, sock, sock_lock)

    assert "Error occurred when polling hardware: " in caplog.text
