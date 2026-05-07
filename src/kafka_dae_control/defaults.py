"""Defaults for kafka_dae_control."""

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
