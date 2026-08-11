# ruff: file-ignore [pytest-fixture-param-without-value, pytest-raises-too-broad, assert-raises-exception ]
import ipaddress
from unittest.mock import patch

import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.serve import serve
from kafka_dae_control.worker_event_types import SetIPEvent

local_ip = ipaddress.IPv4Address("192.168.1.101")
board_ip = ipaddress.IPv4Address("192.168.1.102")


@patch("kafka_dae_control.serve.Producer")
@patch("kafka_dae_control.serve.load_data", return_value=Data(running=False))
@patch("kafka_dae_control.serve.socket")
@patch("kafka_dae_control.serve.process_worker_event", side_effect=Exception)
@patch("kafka_dae_control.serve.camonitor")
@patch("kafka_dae_control.serve.threading")
@patch("kafka_dae_control.serve.PriorityQueue")
def test_handshake_added_to_queue(
    mock_queue,  # pyright: ignore reportMissingParameterType
    mock_thread,  # pyright: ignore reportMissingParameterType
    mock_camonitor,  # pyright: ignore reportMissingParameterType
    _mock_process_worker_event,  # pyright: ignore reportMissingParameterType
    _mock_socket,  # pyright: ignore reportMissingParameterType
    mock_load_data,  # pyright: ignore reportMissingParameterType
    _mock_producer,  # pyright: ignore reportMissingParameterType
    conf: ControlConfig,
):
    # deliberately make process_worker_event() raise then catch it here to avoid while True loop
    conf.pv_prefix = "IN:TEST:"
    vn = [
        "v1",
        "v2",
        "v3",
        "v4",
        "v5",
        "v6",
        "v7",
        "v8",
        "v9",
        "v10",
        "v11",
        "v12",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
        "unused",
    ]
    conf.veto_names = vn

    with pytest.raises(Exception):
        serve(conf)

    assert isinstance(mock_queue.return_value.put.call_args[0][0].item, SetIPEvent)
    assert mock_thread.Thread.call_count == 2
    assert mock_camonitor.call_args_list[0].args == ("IN:TEST:CS:BLOCKSERVER:BLOCKNAMES",)
    assert mock_camonitor.call_args_list[1].args == ("IN:TEST:CS:RC:INRANGE",)
    assert mock_load_data.return_value.veto_names_array == vn


@patch("kafka_dae_control.serve.Producer")
@patch("kafka_dae_control.serve.load_data", return_value=Data(running=False))
@patch("kafka_dae_control.serve.socket")
@patch("kafka_dae_control.serve.process_worker_event", side_effect=Exception)
@patch("kafka_dae_control.serve.camonitor")
@patch("kafka_dae_control.serve.threading")
@patch("kafka_dae_control.serve.PriorityQueue")
def test_veto_names_defaulted_if_not_specified(
    _mock_queue,  # pyright: ignore reportMissingParameterType
    _mock_thread,  # pyright: ignore reportMissingParameterType
    _mock_camonitor,  # pyright: ignore reportMissingParameterType
    _mock_process_worker_event,  # pyright: ignore reportMissingParameterType
    _mock_socket,  # pyright: ignore reportMissingParameterType
    mock_load_data,  # pyright: ignore reportMissingParameterType
    _mock_producer,  # pyright: ignore reportMissingParameterType
    conf: ControlConfig,
):
    conf.veto_names = None

    with pytest.raises(Exception):
        serve(conf)
    assert mock_load_data.return_value.veto_names_array == [
        "veto_0",
        "veto_1",
        "veto_2",
        "veto_3",
        "veto_4",
        "veto_5",
        "veto_6",
        "veto_7",
        "veto_8",
        "veto_9",
        "veto_10",
        "veto_11",
        "veto_12",
        "veto_13",
        "veto_14",
        "veto_15",
        "veto_16",
        "veto_17",
        "veto_18",
        "veto_19",
        "veto_20",
        "veto_21",
        "veto_22",
        "veto_23",
        "veto_24",
        "veto_25",
        "veto_26",
        "veto_27",
        "veto_28",
        "veto_29",
        "veto_30",
        "veto_31",
    ]
