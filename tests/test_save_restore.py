# ruff: noqa PLC1901
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from kafka_dae_control.data import Data
from kafka_dae_control.save_restore import load_data, save_file


def test_save_restore_takes_data_and_saves_relevant_fields():
    d = Data(job_id="1234", run_number=2345, title="atitle", users="someusers", running=False)

    m = MagicMock(spec=Path)
    m.exists.return_value = True

    mock_file = MagicMock()

    m.open.return_value.__enter__.return_value = mock_file

    save_file(d, state_file=m)

    written = json.loads("".join(call.args[0] for call in mock_file.write.mock_calls))

    assert written == {
        "job_id": "1234",
        "run_number": 2345,
        "title": "atitle",
        "users": "someusers",
    }


def test_save_restore_loads_data_then_can_be_used_for_constructing_dataclass():
    m = MagicMock(spec=Path)
    m.exists.return_value = True

    mock_file = MagicMock()
    mock_file.read.return_value = """{
          "job_id": "e1bf4e61-9e3d-418b-988d-b50c63056ef8",
          "run_number": 1,
          "title": "atitle",
          "users": "someusers",
          "running": false
        }"""

    m.open.return_value.__enter__.return_value = mock_file

    d = load_data(m)

    assert d.title == "atitle"
    assert d.users == "someusers"
    assert d.job_id == "e1bf4e61-9e3d-418b-988d-b50c63056ef8"
    assert d.run_number == 1
    assert not d.running


def test_save_restore_file_not_found_defaults_correct():
    m = MagicMock(spec=Path)
    m.exists.return_value = False

    d = load_data(m)

    assert d.title == ""
    assert d.users == ""
    assert d.job_id == ""
    assert d.run_number == 0


def test_load_invalid_file_errors():
    m = MagicMock(spec=Path)
    m.exists.return_value = True

    mock_file = MagicMock()
    mock_file.read.return_value = """{
          "job_id": "e1bf4e61-9e3d-418b-988d-b50c63056ef8",
          "run_number": 1,
          "title": 1
        }"""  # wrong type for title

    m.open.return_value.__enter__.return_value = mock_file

    with pytest.raises(ValidationError):
        load_data(m)
