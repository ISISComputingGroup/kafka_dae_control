# ruff: noqa
import ipaddress
from unittest.mock import patch

import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import COMMS_REGISTER
from kafka_dae_control.run_state import RunRegister
from kafka_dae_control.serve import serve

local_ip = ipaddress.IPv4Address("192.168.1.101")
board_ip = ipaddress.IPv4Address("192.168.1.102")


@patch("kafka_dae_control.serve.camonitor")
@patch("kafka_dae_control.serve.Producer")
@patch("kafka_dae_control.serve.read")
@patch("kafka_dae_control.serve.sleep", side_effect=Exception)
@patch("kafka_dae_control.serve.load_data", return_value=Data())
@patch("kafka_dae_control.serve.socket")
@patch("kafka_dae_control.serve.write_verify")
def test_handshake_happens(mock_write_verify, *_):  # pyright: ignore reportMissingParameterType

    with pytest.raises(Exception):  # deliberately make sleep raise then catch it here
        serve(
            ControlConfig(
                board_ip=board_ip,
                pv_prefix="",
                runinfo_topic="",
                local_ip=local_ip,
                kafka_producer={},
            )
        )
    assert mock_write_verify.call_args.args[1] == board_ip
    assert mock_write_verify.call_args.args[2] == COMMS_REGISTER.address
    assert mock_write_verify.call_args.args[3] == 3232235877
    assert mock_write_verify.call_args.args[4] == COMMS_REGISTER.size


@patch("kafka_dae_control.serve.camonitor")
@patch("kafka_dae_control.serve.Producer")
@patch("kafka_dae_control.serve.sleep", side_effect=Exception)
@patch("kafka_dae_control.serve.socket")
@patch("kafka_dae_control.serve.write_verify")
@patch("kafka_dae_control.serve.read", return_value=RunRegister.STATUS_RUNNING)
@patch("kafka_dae_control.serve.load_data", return_value=Data())
def test_read_updates_running_status(load_data, *_):  # pyright: ignore reportMissingParameterType
    with pytest.raises(Exception):  # deliberately make sleep raise then catch it here
        serve(
            ControlConfig(
                board_ip=board_ip,
                pv_prefix="",
                runinfo_topic="",
                local_ip=local_ip,
                kafka_producer={},
            )
        )
    assert load_data.return_value.running.value


@patch("kafka_dae_control.serve.camonitor")
@patch("kafka_dae_control.serve.Producer")
@patch("kafka_dae_control.serve.sleep", side_effect=Exception)
@patch("kafka_dae_control.serve.socket")
@patch("kafka_dae_control.serve.write_verify")
@patch("kafka_dae_control.serve.read", return_value=0x0)
@patch("kafka_dae_control.serve.load_data", return_value=Data())
def test_read_updates_running_status(load_data, *_):  # pyright: ignore reportMissingParameterType
    with pytest.raises(Exception):  # deliberately make sleep raise then catch it here
        serve(
            ControlConfig(
                board_ip=board_ip,
                pv_prefix="",
                runinfo_topic="",
                local_ip=local_ip,
                kafka_producer={},
            )
        )
    assert not load_data.return_value.running.value


@patch("kafka_dae_control.serve.camonitor")
@patch("kafka_dae_control.serve.Producer")
@patch("kafka_dae_control.serve.sleep", side_effect=Exception)
@patch("kafka_dae_control.serve.load_data", return_value=Data())
@patch("kafka_dae_control.serve.socket")
@patch("kafka_dae_control.serve.write_verify")
@patch("kafka_dae_control.serve.read", side_effect=OSError("test"))
def test_read_which_throws_logs(mock_read, _, __, ___, ____, _____, ______, caplog):  # pyright: ignore reportMissingParameterType
    with pytest.raises(Exception):  # deliberately make sleep raise then catch it here
        serve(
            ControlConfig(
                board_ip=board_ip,
                pv_prefix="",
                runinfo_topic="",
                local_ip=local_ip,
                kafka_producer={},
            )
        )

    assert "Error reading from hardware: " in caplog.text
