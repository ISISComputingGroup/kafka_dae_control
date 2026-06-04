"""Utilities for reading Control IOC configuration from TOML."""

import ipaddress
import tomllib
from functools import cached_property
from pathlib import Path
from xml.etree import ElementTree

from pydantic import BaseModel, ValidationError

from kafka_dae_control.defaults import FLUSH_TIMEOUT_S, READ_PORT, WRITE_PORT, Registers


class ControlConfig(BaseModel):
    """Configuration parameters for Kafka DAE control."""

    board_ip: ipaddress.IPv4Address
    """IP address of the streaming control board"""

    board_xml: Path
    """Path to the streaming control board's firmware-generated XML file"""

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

    @cached_property
    def register_map(self) -> dict[str, int]:
        """Parse the register XML file to get a mapping of register names to addresses."""
        return parse_register_map(self.board_xml)


def load_config(config_path: str) -> ControlConfig:
    """Validate and load a config file at the specified path."""
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    try:
        return ControlConfig.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Unable to load config from '{config_path}':\n{e}") from e


def parse_register_map(xml_path: Path) -> dict[str, int]:
    """Parse the register XML file to get a mapping of register names to addresses.

    Args:
        xml_path: the path to the XML file.

    Returns: a dict containing a mapping between register names and addresses.

    """
    root = ElementTree.parse(xml_path).getroot()

    mapping = {}
    # iterate over nodes with a depth of 3 - ignore outer (groups) and inner (bits within registers)
    for elem in root.findall("./*/*"):
        if (register_name := elem.attrib.get("id")) is not None and (
            address := elem.attrib.get("absolute_offset")
        ) is not None:
            mapping[register_name] = int(address, 16)

    _assert_keys_in_mapping(mapping)

    return mapping


def _assert_keys_in_mapping(mapping: dict[str, int]) -> None:
    for r in Registers:
        assert r.value in mapping, f"Register {r.value} not found in mapping"
