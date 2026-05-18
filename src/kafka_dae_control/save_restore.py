"""IO utilities for saving and loading data which should persist."""

import json
import logging
from pathlib import Path

from kafka_dae_control.data import Data

TITLE_KEY = "title"
USERS_KEY = "users"
RUN_NUMBER_KEY = "run_number"
JOB_ID_KEY = "job_id"
RUNNING_KEY = "running"

logger = logging.getLogger(__name__)


def save_file(data: "Data", *_: int | str, state_file: Path) -> None:
    """Save relevant dataclass fields to a file.

    Args:
        data: the dataclass containing the state of the program
        state_file: the file to save the state to.

    Returns: None

    """
    with state_file.open("w", encoding="utf-8") as file:
        json.dump(
            {
                TITLE_KEY: data.title,
                USERS_KEY: data.users,
                RUN_NUMBER_KEY: data.run_number,
                JOB_ID_KEY: data.job_id,
            },
            file,
            indent=2,
        )


def load_data(state_file: Path) -> Data:
    """Load persisted data from file."""
    if not state_file.exists():
        logger.warning("State file not found, using defaults")
        return Data(job_id="", run_number=0, title="", users="", running=False)

    with state_file.open(encoding="utf-8") as f:
        logger.debug("State file found")
        raw = json.load(f)
        logger.debug("State file json: %s", raw)

        return Data.model_validate(raw)
