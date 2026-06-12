"""Utilities for parsing the register map XML file."""

from pathlib import Path
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from kafka_dae_control.defaults import Registers


def parse_register_map(xml_path: Path) -> dict[str, int]:
    """Parse the register XML file to get a mapping of register names to addresses.

    Args:
        xml_path: the path to the XML file.

    Returns: a dict containing a mapping between register names and addresses.

    """
    root = ElementTree.parse(xml_path).getroot()

    mapping = _map_register_addresses(root)

    _assert_keys_in_mapping(mapping)

    return mapping


def _map_register_addresses(root: Element) -> dict[str, int]:
    mapping = {}
    # iterate over nodes with a depth of 3,
    # ignoring outer (register groups) and inner (bits within registers) nodes
    for elem in root.findall("./*/*"):
        if (register_name := elem.attrib.get("id")) is not None and (
            address := elem.attrib.get("absolute_offset")
        ) is not None:
            mapping[register_name] = int(address, 16)
    return mapping


class BadFirmwareXMLError(Exception):
    """Exception for an invalid firmware XML file."""


def _assert_keys_in_mapping(mapping: dict[str, int]) -> None:
    if registers_not_present := [r for r in Registers if r not in mapping]:
        raise BadFirmwareXMLError(f"Invalid firmware xml - not present: {registers_not_present}")
