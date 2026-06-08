"""Utilities for reading Control IOC configuration from TOML."""

import ipaddress
import tomllib
from pathlib import Path

from pydantic import BaseModel, ValidationError

from kafka_dae_control.defaults import FLUSH_TIMEOUT_S, READ_PORT, WRITE_PORT


class ControlConfig(BaseModel):
    """Configuration parameters for Kafka DAE control."""

    board_ip: ipaddress.IPv4Address
    """IP address of the streaming control board"""

    pv_prefix: str
    """PV prefix of all PVs in this IOC"""

    instrument_name: str
    """Name of the instrument"""

    runinfo_topic: str
    """Run info topic to push run starts/stops to"""

    local_ip: ipaddress.IPv4Address
    """Local IP to set the control board IP register to"""

    poll_interval_s: float = 1.0
    """How often to poll the streaming control board"""

    kafka_producer: dict[str, str]
    """Kafka producer configuration"""

    state_file: Path = Path("state.json")  # this is a Path as the file doesn't need to exist
    """Path to the file to save/restore state to"""

    pv_update_interval_s: float = 0.1
    """How often to update the PVs"""

    read_port: int = READ_PORT
    """The read port to use for reading from the streaming control board"""

    write_port: int = WRITE_PORT
    """The write port to use for writing to the streaming control board"""

    flush_timeout_s: int = FLUSH_TIMEOUT_S
    """The timeout for a flush after producing run info messages"""


def load_config(config_path: str) -> ControlConfig:
    """Validate and load a config file at the specified path."""
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    try:
        return ControlConfig.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Unable to load config from '{config_path}':\n{e}") from e
