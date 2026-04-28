"""Utilities for reading Control IOC configuration from TOML."""

import socket
import tomllib

from pydantic import BaseModel, ValidationError


class ControlConfig(BaseModel):
    """Configuration parameters for Kafka DAE control."""

    board_ip: str
    """IP address of the streaming control board"""

    pv_prefix: str
    """PV prefix of all PVs in this IOC"""

    broker: str
    """Kafka broker to use"""

    runinfo_topic: str = f"{socket.gethostname()}_runInfo"
    """Run info topic to push run starts/stops to"""

    local_ip: str
    """Local IP to set the control board IP register to"""


def load_config(config_path: str) -> ControlConfig:
    """Validate and load a config file at the specified path."""
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    try:
        return ControlConfig.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Unable to load config from '{config_path}':\n{e}") from e
