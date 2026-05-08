import ipaddress

import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data


@pytest.fixture
def conf() -> ControlConfig:
    return ControlConfig(
        board_ip=ipaddress.IPv4Address(
            "192.168.1.1",
        ),
        pv_prefix="",
        local_ip=ipaddress.IPv4Address(
            "192.168.1.2",
        ),
        kafka_producer={},
    )


@pytest.fixture
def data() -> Data:
    return Data(running=False)
