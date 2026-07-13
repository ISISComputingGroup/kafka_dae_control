"""Data class containing the state of the program."""

import logging
from typing import TypeVar

from pydantic import BaseModel, Field

from kafka_dae_control.defaults import FrameSyncSelect, PeriodMode

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Data(BaseModel):
    """A mutable object describing the data being served by this IOC.

    This object is only ever mutated by the main worker thread. It is read by
    the main worker thread and the PV update thread.
    """

    running: bool = False
    """Whether the hardware is running or not"""

    frame_sync_select_rbv: FrameSyncSelect = FrameSyncSelect.UNKNOWN
    """The frame sync select value on the hardware"""

    frame_sync_select_sp: FrameSyncSelect = FrameSyncSelect.UNKNOWN
    """The frame sync select value setpoint"""

    job_id: str = ""
    """Run's job_id, used to tie starts and stops together"""

    run_number: int = 0
    """Run number"""

    blocks: list[str] = Field(default_factory=list)
    """List of blocks to be inserted in the run start nexus structure.
     These are prefixed with the instrument and block server prefixes"""

    num_periods_sp: int = 1
    """Number of periods (setpoint). This is 1-indexed for backwards compatibility reasons."""

    num_periods_rbv: int = 1
    """Number of periods (readback). This is 1-indexed for backwards compatibility reasons."""

    current_period_sp: int = 1
    """Current period number setpoint."""

    current_period_rbv: int = 1
    """Current period number readback."""

    period_mode_sp: PeriodMode = PeriodMode.UNKNOWN
    """The period mode setpoint."""

    period_mode_rbv: PeriodMode = PeriodMode.UNKNOWN
    """The period mode readback."""
