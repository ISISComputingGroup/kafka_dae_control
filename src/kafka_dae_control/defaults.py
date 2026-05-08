"""Defaults for kafka_dae_control."""

from enum import IntFlag
from typing import NamedTuple

WRITE_PORT = 10002
READ_PORT = 10000
RECEIVE_BUFFER_SIZE = 1024


class Register(NamedTuple):
    """a register with associated size."""

    """Starting word address of the register"""
    address: int
    """Size in 32-bit words"""
    size: int


RUNNING_REGISTER = Register(0x0, 1)
COMMS_REGISTER = Register(0x10000024, 1)


class RunRegister(IntFlag):
    """Enum for bits in the run register."""

    ETHERNET_OVERRIDE = 0x01
    RUN_SIGNAL_ETH = 0x02
    RUN_SIGNAL_VXI = 0x04
    NO_FRAME_INC = 0x08
    STREAM_EMPTY_FRAMES = 0x10
    STATUS_RUNNING = 0x20
