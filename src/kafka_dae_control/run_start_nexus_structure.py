"""Tools for generating the nexus structure field of a pl72 run start message."""

import json
import typing

if typing.TYPE_CHECKING:
    from kafka_dae_control.data import Data


def generate_nexus_structure(data: "Data") -> str:
    """Generate the nexus structure for a run start using the data class.

    Args:
        data: The data class containing the state of the program

    Returns: a JSON-formatted string containing the nexus structure

    """
    return json.dumps(
        {
            "children": [
                {
                    "type": "group",
                    "name": "raw_data_1",
                    "children": [
                        {
                            "type": "group",
                            "name": "events",
                            "children": [
                                {
                                    "type": "stream",
                                    "stream": {
                                        "topic": f"{data.instrument_name}_events",
                                        "source": "KDAECTRL",
                                        "writer_module": "ev44",
                                    },
                                },
                            ],
                            "attributes": [{"name": "NX_class", "values": "NXentry"}],
                        },
                        {
                            "type": "group",
                            "name": "selog",
                            "children": [
                                {
                                    "type": "stream",
                                    "stream": {
                                        "topic": f"{data.instrument_name}_sampleEnv",
                                        "source": x,
                                        "writer_module": "f144",
                                    },
                                }
                                for x in data.blocks
                            ],
                        },
                    ],
                    "attributes": [{"name": "NX_class", "values": "NXentry"}],
                }
            ]
        }
    )
