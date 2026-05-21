"""Data class containing the state of the program."""

import logging
import socket
from typing import TypeVar

from pydantic import BaseModel, Field

from kafka_dae_control.defaults import FrameSyncSelect

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

    title: str = ""
    """Run title"""

    users: str = ""
    """Run users"""

    job_id: str = ""
    """Run's job_id, used to tie starts and stops together"""

    run_number: int = 0
    """Run number"""

    blocks: list[str] = Field(default_factory=list)
    """List of blocks to be inserted in the run start nexus structure.
     These are prefixed with the instrument and block server prefixes"""

    instrument_name: str = Field(default_factory=socket.gethostname)
    """The name of the instrument"""
