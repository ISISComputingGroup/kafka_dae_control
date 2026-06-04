import ipaddress
from pathlib import Path

import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import Registers


@pytest.fixture
def conf() -> ControlConfig:
    cc = ControlConfig(
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
        board_xml=Path("blah.xml"),
    )
    cc.register_map = {
        Registers.RUNNING_REGISTER: 0,
        Registers.FRAME_SYNC_SEL_REGISTER: 4,
        Registers.COMMS_REGISTER: 268435492,
    }
    return cc


@pytest.fixture
def data() -> Data:
    return Data(running=False)
