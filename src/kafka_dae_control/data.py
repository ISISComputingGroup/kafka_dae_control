"""Data class containing the state of the program."""

import logging
from typing import TypeVar

from pydantic import BaseModel, Field

from kafka_dae_control.defaults import NUM_VETOES, FrameSyncSelect, PeriodMode

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Data(BaseModel):
    """A mutable object describing the data being served by this IOC.

    This object is only ever mutated by the main worker thread. It is read by
    the main worker thread and the PV update thread.
    """

    running: bool = False
    """Whether the hardware is running or not"""

    paused: bool = False
    """Whether the hardware is paused or not"""

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

    veto_names_array: list[str] = Field(default=[f"veto_{n}" for n in range(NUM_VETOES)])
    """
    Veto names, as a numpy array of strings. This is indexed so that 0 is veto 0.
    """

    vetoes: list[int] = Field(default=[0] * NUM_VETOES)
    """Vetoes array containing 0 for disabled, 1 for soft, 2 for hard.
     This is indexed so that item 0 is veto 0."""

    hard_vetoes_rbv: int = 0xFFFF
    """Hard vetoes readback bit mask"""
    num_periods_sp: int = 1
    """Number of periods (setpoint)."""

    num_periods_rbv: int = 1
    """Number of periods (readback)."""

    current_period_sp: int = 1
    """Current period number setpoint. This is 1-indexed for backwards compatibility reasons."""

    current_period_rbv: int = 1
    """Current period number readback. This is 1-indexed for backwards compatibility reasons."""

    period_mode_sp: PeriodMode = PeriodMode.UNKNOWN
    """The period mode setpoint."""

    period_mode_rbv: PeriodMode = PeriodMode.UNKNOWN
    """The period mode readback."""
