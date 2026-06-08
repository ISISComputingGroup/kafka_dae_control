import ipaddress
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from kafka_dae_control.config import ControlConfig, load_config


def test_config_loading():
    m = mock_open(
        read_data=b"""
board_ip = "192.168.1.250"
instrument_name = "TESTMACHINE"
pv_prefix = "TE:TESTMACHINE:KDAECTRL:"
runinfo_topic = "somemachine_runInfo"
# a comment

board_xml = "test.xml"

local_ip = "192.168.1.17"

state_file = "./state1.json"

sample_env_topic = "sample-env-topic"
events_topic = "events-topic"
[kafka_producer]
"bootstrap.servers" = "mybroker:9092"

"""
    )

    with patch("kafka_dae_control.config.open", m):
        config = load_config("")

    assert config.instrument_name == "TESTMACHINE"
    assert config.board_ip == ipaddress.IPv4Address("192.168.1.250")
    assert config.runinfo_topic == "somemachine_runInfo"
    assert config.pv_prefix == "TE:TESTMACHINE:KDAECTRL:"
    assert config.local_ip == ipaddress.IPv4Address("192.168.1.17")
    assert config.kafka_producer.get("bootstrap.servers") == "mybroker:9092"
    assert config.state_file == Path("./state1.json")
    assert config.sample_env_topic == "sample-env-topic"
    assert config.events_topic == "events-topic"


def test_invalid_config_loading():
    m = mock_open(
        read_data=b"""
pv_prefix = 2
# Lots of missing keys
"""
    )

    with (
        patch("kafka_dae_control.config.open", m),
        pytest.raises(ValueError, match=r"Unable to load config .*"),
    ):
        load_config("")


@patch("kafka_dae_control.config.parse_register_map")
def test_register_map_calls_parse_register_map(mock_register_map):  # pyright: ignore reportMissingParameterType
    cfg = ControlConfig(
        board_ip=ipaddress.IPv4Address(
            "192.168.1.1",
        ),
        pv_prefix="",
        local_ip=ipaddress.IPv4Address(
            "192.168.1.2",
        ),
        kafka_producer={},
        instrument_name="TEST",
        runinfo_topic="run-info-topic",
        board_xml=Path("test1.xml"),
        sample_env_topic="sample-env-topic",
        events_topic="events-topic",
    )
    assert cfg.register_map == mock_register_map.return_value
    mock_register_map.assert_called_once_with(Path("test1.xml"))
