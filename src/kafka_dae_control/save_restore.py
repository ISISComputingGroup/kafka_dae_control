"""IO utilities for saving and loading data which should persist."""

import json
import logging
from pathlib import Path

from kafka_dae_control.data import Data

RUN_NUMBER_KEY = "run_number"
JOB_ID_KEY = "job_id"
RUNNING_KEY = "running"
VETOES_KEY = "vetoes"
LATEST_BOOT_TIME_MSB = "latest_boot_time_msb"
LATEST_BOOT_TIME_LSB = "latest_boot_time_lsb"
FRAME_SYNC_SEL = "frame_sync_select"
FRAME_SYNC_DELAY = "frame_sync_delay"
PERIOD_MODE = "period_mode"
CURRENT_PERIOD = "current_period"
MAX_NUM_PERIODS = "max_num_periods"

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
                RUN_NUMBER_KEY: data.run_number,
                JOB_ID_KEY: data.job_id,
                VETOES_KEY: data.vetoes,
                LATEST_BOOT_TIME_MSB: data.latest_boot_time_msb,
                LATEST_BOOT_TIME_LSB: data.latest_boot_time_lsb,
                FRAME_SYNC_SEL: data.frame_sync_select_rbv,
                FRAME_SYNC_DELAY: data.frame_sync_delay_rbv,
                PERIOD_MODE: data.period_mode_rbv,
                MAX_NUM_PERIODS: data.num_periods_rbv,
                CURRENT_PERIOD: data.current_period_rbv,
            },
            file,
            indent=2,
        )


def load_data(state_file: Path) -> Data:
    """Load persisted data from file."""
    if not state_file.exists():
        logger.warning("State file not found, using defaults")
        return Data()

    with state_file.open(encoding="utf-8") as f:
        logger.debug("State file found")
        raw = json.load(f)
        logger.debug("State file json: %s", raw)

        return Data.model_validate(raw)
