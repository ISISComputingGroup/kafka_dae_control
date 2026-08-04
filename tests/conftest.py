import ipaddress
from pathlib import Path

import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import NUM_VETOES, Registers


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
        sample_env_topic="sample-env-topic",
        events_topic="events-topic",
        vetoes_topic="vetoes-topic",
        veto_names=[f"veto_{n}" for n in range(NUM_VETOES)],
    )
    cc.register_map = {
        Registers.RUNNING_REGISTER: RUNNING_REGISTER_ADDRESS,
        Registers.FRAME_SYNC_SEL_REGISTER: FRAME_SYNC_SEL_ADDRESS,
        Registers.COMMS_REGISTER: COMMS_REGISTER_ADDRESS,
        Registers.PERIOD_CONTROL: PERIOD_CONTROL_ADDRESS,
        Registers.PERIOD_COMP_CURRENT: PERIOD_COMP_CURRENT_ADDRESS,
        Registers.PERIOD_NUMBER_LIMIT: PERIOD_NUMBER_LIMIT_ADDRESS,
        Registers.VETO_CONTROL_REGISTER: VETO_CONTROL_ADDRESS,
    }
    return cc


RUNNING_REGISTER_ADDRESS = 0
FRAME_SYNC_SEL_ADDRESS = 4
COMMS_REGISTER_ADDRESS = 268435492
PERIOD_CONTROL_ADDRESS = 1234
PERIOD_COMP_CURRENT_ADDRESS = 2345
PERIOD_NUMBER_LIMIT_ADDRESS = 3456
VETO_CONTROL_ADDRESS = 5678


@pytest.fixture
def data() -> Data:
    return Data(running=False)
