# ruff: noqa
import ipaddress
from unittest.mock import patch

import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.serve import serve
from kafka_dae_control.worker_event import SetIPEvent

local_ip = ipaddress.IPv4Address("192.168.1.101")
board_ip = ipaddress.IPv4Address("192.168.1.102")


@patch("kafka_dae_control.serve.Producer")
@patch("kafka_dae_control.serve.load_data", return_value=Data(running=False))
@patch("kafka_dae_control.serve.socket")
@patch("kafka_dae_control.serve.process_worker_event", side_effect=Exception)
@patch("kafka_dae_control.serve.camonitor")
@patch("kafka_dae_control.serve.threading")
@patch("kafka_dae_control.serve.Queue")
def test_handshake_added_to_queue(mock_queue, mock_thread, mock_camonitor, *_):  # pyright: ignore reportMissingParameterType
    # deliberately make process_worker_event() raise then catch it here to avoid while True loop

    with pytest.raises(Exception):
        serve(
            ControlConfig(
                board_ip=board_ip,
                pv_prefix="IN:TEST:",
                runinfo_topic="",
                local_ip=local_ip,
                kafka_producer={},
                instrument_name="TEST",
            )
        )

    assert isinstance(mock_queue.return_value.put.call_args[0][0], SetIPEvent)
    assert mock_thread.Thread.call_count == 2
    assert mock_camonitor.call_args.args == ("IN:TEST:CS:BLOCKSERVER:BLOCKNAMES",)


@patch("kafka_dae_control.serve.Producer")
@patch("kafka_dae_control.serve.load_data", return_value=Data(running=False))
@patch("kafka_dae_control.serve.socket")
@patch("kafka_dae_control.serve.process_worker_event", side_effect=Exception)
@patch("kafka_dae_control.serve.camonitor")
@patch("kafka_dae_control.serve.threading")
@patch("kafka_dae_control.serve.Queue")
def test_if_title_or_users_defined_camonitors_set_up(mock_queue, mock_thread, mock_camonitor, *_):  # pyright: ignore reportMissingParameterType
    # deliberately make process_worker_event() raise then catch it here to avoid while True loop

    with pytest.raises(Exception):
        serve(
            ControlConfig(
                board_ip=board_ip,
                pv_prefix="IN:TEST:",
                runinfo_topic="",
                local_ip=local_ip,
                kafka_producer={},
                instrument_name="TEST",
                title_pv="IN:TEST:TITLE",
                users_pv="IN:TEST:USERS",
            )
        )

    assert mock_camonitor.call_count == 3
