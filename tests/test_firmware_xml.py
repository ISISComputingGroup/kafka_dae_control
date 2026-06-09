from pathlib import Path
from unittest.mock import patch
from xml.etree.ElementTree import ElementTree, fromstring

import pytest

from kafka_dae_control.defaults import Registers
from kafka_dae_control.firmware_xml import BadFirmwareXMLError, parse_register_map
from tests.firmware_xml_for_tests import valid_xml_str


def test_parse_xml_sets_register_mapping_correctly():
    with patch("xml.etree.ElementTree.parse") as mock_parse:
        mock_parse.return_value.getroot.return_value = ElementTree(fromstring(valid_xml_str))

        mapping = parse_register_map(Path("whatever"))

    assert mapping[Registers.RUNNING_REGISTER] == 0x0


def test_parse_valid_xml_missing_register_raises():
    with patch("xml.etree.ElementTree.parse") as mock_parse:
        mock_parse.return_value.getroot.return_value = ElementTree(
            fromstring("<node><node><node></node></node></node>")
        )
        with pytest.raises(BadFirmwareXMLError):
            parse_register_map(Path("whaFtever"))
