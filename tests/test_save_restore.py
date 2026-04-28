import json
from unittest.mock import mock_open, patch

from kafka_dae_control.data import Data
from kafka_dae_control.save_restore import load_data, save_file


def test_save_restore_takes_data_and_saves_relevant_fields():
    d = Data(job_id="1234", run_number=2345, title="atitle", users="someusers")
    m = mock_open()
    # with patch()
    with patch("builtins.open", m):
        save_file(d)

    handle = m()

    written = json.loads("".join(call.args[0] for call in handle.write.mock_calls))

    assert written == {
        "job_id": "1234",
        "run_number": 2345,
        "title": "atitle",
        "users": "someusers",
    }


def test_save_restore_loads_data_then_can_be_used_for_constructing_dataclass():
    m = mock_open(
        read_data="""{
  "job_id": "e1bf4e61-9e3d-418b-988d-b50c63056ef8",
  "run_number": 1,
  "title": "atitle",
  "users": "someusers"
}"""
    )
    with patch("builtins.open", m):
        pd = load_data()
    d = Data(**pd)

    assert d.title.value == "atitle"
    assert d.users.value == "someusers"
    assert d.job_id.value == "e1bf4e61-9e3d-418b-988d-b50c63056ef8"
    assert d.run_number.value == 1


def test_save_restore_file_not_found_defaults_correct():
    pass


def test_load_invalid_file():
    pass
