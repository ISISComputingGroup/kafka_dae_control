import json

from kafka_dae_control.data import Data
from kafka_dae_control.run_start_nexus_structure import generate_nexus_structure


def test_run_start_nexus_structure_contains_blocks_and_events():
    d = Data(running=False)
    d.blocks = ["a", "b"]
    d.instrument_name = "MUSHROOM"

    g = generate_nexus_structure(d)
    j = json.loads(g)

    assert "a" == j["children"][0]["children"][1]["children"][0]["stream"]["source"]
    assert "b" == j["children"][0]["children"][1]["children"][1]["stream"]["source"]

    assert "MUSHROOM_sampleEnv" == j["children"][0]["children"][1]["children"][0]["stream"]["topic"]
    assert "MUSHROOM_sampleEnv" == j["children"][0]["children"][1]["children"][0]["stream"]["topic"]

    assert "MUSHROOM_events" == j["children"][0]["children"][0]["children"][0]["stream"]["topic"]
    assert "KDAECTRL" == j["children"][0]["children"][0]["children"][0]["stream"]["source"]
