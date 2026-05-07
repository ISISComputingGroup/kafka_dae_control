import ipaddress
from unittest.mock import mock_open, patch

import pytest

from kafka_dae_control.config import load_config


def test_config_loading():
    m = mock_open(
        read_data=b"""
board_ip = "192.168.1.250"
pv_prefix = "TE:TESTMACHINE:KDAECTRL:"
runinfo_topic = "somemachine_runInfo"
# a comment

local_ip = "192.168.1.17"

[kafka_producer]
"bootstrap.servers" = "mybroker:9092"

"""
    )

    with patch("kafka_dae_control.config.open", m):
        config = load_config("")

    assert config.board_ip == ipaddress.IPv4Address("192.168.1.250")
    assert config.runinfo_topic == "somemachine_runInfo"
    assert config.pv_prefix == "TE:TESTMACHINE:KDAECTRL:"
    assert config.local_ip == ipaddress.IPv4Address("192.168.1.17")
    assert config.kafka_producer.get("bootstrap.servers") == "mybroker:9092"


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
