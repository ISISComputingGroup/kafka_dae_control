"""Utilities for reading Control IOC configuration from TOML."""

import ipaddress
import socket
import tomllib
from pathlib import Path

from pydantic import BaseModel, ValidationError


class ControlConfig(BaseModel):
    """Configuration parameters for Kafka DAE control."""

    board_ip: ipaddress.IPv4Address
    """IP address of the streaming control board"""

    pv_prefix: str
    """PV prefix of all PVs in this IOC"""

    runinfo_topic: str = f"{socket.gethostname()}_runInfo"
    """Run info topic to push run starts/stops to"""

    local_ip: ipaddress.IPv4Address
    """Local IP to set the control board IP register to"""

    poll_interval_s: float = 1.0
    """How often to poll the streaming control board"""

    kafka_producer: dict[str, str]
    """Kafka producer configuration"""

    state_file: Path = Path("state.json")  # this is a Path as the file doesn't need to exist
    """Path to the file to save/restore state to"""


def load_config(config_path: str) -> ControlConfig:
    """Validate and load a config file at the specified path."""
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    try:
        return ControlConfig.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Unable to load config from '{config_path}':\n{e}") from e
