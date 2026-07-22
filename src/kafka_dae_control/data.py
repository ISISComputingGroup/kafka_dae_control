"""Data class containing the state of the program."""

import logging
from typing import TypeVar

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, Field

from kafka_dae_control.defaults import NUM_VETOES, FrameSyncSelect
from kafka_dae_control.utils import mask_to_array

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

    veto_names_array: list[str] = Field(default=[f"veto_{n}" for n in range(NUM_VETOES)])
    """
    Veto names, as a numpy array of strings.
    """

    soft_vetoes: int = 0xFFFF
    """Soft vetoes bit mask"""

    hard_vetoes_rbv: int = 0xFFFF
    """Hard vetoes bit mask"""

    hard_vetoes_sp: int = 0xFFFF
    """Hard vetoes setpoint"""

    @property
    def soft_vetoes_array(self) -> npt.NDArray[np.uint8]:
        """An array representation of the soft vetoes bit mask."""
        return mask_to_array(self.soft_vetoes)

    @property
    def hard_vetoes_array(self) -> npt.NDArray[np.uint8]:
        """An array representation of the hard vetoes bit mask."""
        return mask_to_array(self.hard_vetoes_rbv)

    @property
    def hard_vetoes_sp_array(self) -> npt.NDArray[np.uint8]:
        """An array representation of the hard vetoes bit mask."""
        return mask_to_array(self.hard_vetoes_sp)
