"""Defaults for kafka_dae_control."""

from enum import Enum, IntFlag, StrEnum
from typing import NamedTuple

WRITE_PORT = 10002
READ_PORT = 10000
RECEIVE_BUFFER_SIZE = 1024
FLUSH_TIMEOUT_S = 1
REGISTER_SIZE_WORDS = 1


class Register(NamedTuple):
    """a register with associated size."""

    """Starting word address of the register"""
    address: int
    """Size in 32-bit words"""
    size: int


class Registers(StrEnum):
    """Register IDs on the streaming control board."""

    RUNNING_REGISTER = "run_register"
    FRAME_SYNC_SEL_REGISTER = "frame_sync_sel"

    COMMS_REGISTER = "udp_core_control_0_dst_ip_addr"


class FrameSyncSelect(Enum):
    """Options for the `frame_sync_sel` register."""

    INTERNAL_TEST_CLOCK = 0
    SMP = 1
    ISIS = 2
    UNKNOWN = -1


class RunRegister(IntFlag):
    """Enum for bits in the run register."""

    ETHERNET_OVERRIDE = 0x01
    RUN_SIGNAL_ETH = 0x02
    RUN_SIGNAL_VXI = 0x04
    NO_FRAME_INC = 0x08
    STREAM_EMPTY_FRAMES = 0x10
    STATUS_RUNNING = 0x20
