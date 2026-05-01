"""IO utilities for saving and loading data which should persist."""

import json
import logging
from pathlib import Path

import cattrs
from attr import asdict
from attrs import define

from kafka_dae_control.data import Data

TITLE_KEY = "title"
USERS_KEY = "users"
RUN_NUMBER_KEY = "run_number"
JOB_ID_KEY = "job_id"

logger = logging.getLogger(__name__)


STATE_FILE = Path("state.json")
converter = cattrs.Converter()


@define
class PersistedData:
    """Persisted data and defaults to fall back to."""

    job_id: str
    run_number: int
    title: str
    users: str


def save_file(data: "Data", *_: int | str, state_file: Path = STATE_FILE) -> None:
    """Save relevant dataclass fields to a file.

    Args:
        data: the dataclass containing the state of the program
        *args: mandatory catch-all for hook signature.
        state_file: the file to save the state to.

    Returns: None

    """
    with state_file.open("w", encoding="utf-8") as file:
        persisted = PersistedData(
            job_id=data.job_id.value,
            run_number=data.run_number.value,
            title=data.title.value,
            users=data.users.value,
        )

        json.dump(converter.unstructure(persisted), file, indent=2)


def load_data(state_file: Path = STATE_FILE) -> Data:
    """Load persisted data from file."""
    if not state_file.exists():
        return Data(job_id="", run_number=0, title="", users="")

    with state_file.open(encoding="utf-8") as f:
        raw = json.load(f)

    persisted = converter.structure(raw, PersistedData)
    return Data(**asdict(persisted))
