"""Defaults for kafka_dae_control."""

from enum import IntEnum, IntFlag, StrEnum

WRITE_PORT = 10002
READ_PORT = 10000
RECEIVE_BUFFER_SIZE = 1024
FLUSH_TIMEOUT_S = 1
REGISTER_SIZE_WORDS = 1
NUM_VETOES = 32

DISABLED_VETO_VALUE = 0
SOFT_VETO_VALUE = 1
HARD_VETO_VALUE = 2


PAUSE_VETO_TOGGLE_BIT = 5
RC_VETO_TOGGLE_BIT = 6


class Registers(StrEnum):
    """Register IDs on the streaming control board."""

    RUNNING_REGISTER = "run_register"
    FRAME_SYNC_SEL_REGISTER = "frame_sync_sel"
    VETO_CONTROL_REGISTER = "vetoes_mask"

    COMMS_REGISTER = "udp_core_control_0_dst_ip_addr"
    PERIOD_COMP_CURRENT = "period_comp_current"
    PERIOD_NUMBER_LIMIT = "period_number_limit"
    PERIOD_CONTROL = "period_control"
    VETO_TOGGLE = "vetoes_software"


class FrameSyncSelect(IntEnum):
    """Options for the `frame_sync_sel` register."""

    INTERNAL_TEST_CLOCK = 0
    SMP = 1
    ISIS = 2
    UNKNOWN = -1


class PeriodControlFlags(IntFlag):
    """Bit flags for the `period_mode` register."""

    MODE_COMPUTER = 0x00
    END_RUN_AT_END_OF_PERIOD_SEQUENCE = 0x02
    MODE_LOOK_UP_TABLE = 0x10
    MODE_NOT_USED = 0x20
    MODE_EXTERNAL = 0x30
    END_RUN_AFTER_LAST_PERIOD_SEQUENCE = 0x40


class PeriodMode(IntEnum):
    """Options for the `period_mode` register."""

    COMPUTER = PeriodControlFlags.MODE_COMPUTER
    LOOK_UP_TABLE = PeriodControlFlags.MODE_LOOK_UP_TABLE
    NOT_USED = PeriodControlFlags.MODE_NOT_USED
    EXTERNAL = PeriodControlFlags.MODE_EXTERNAL
    UNKNOWN = -1


class RunRegister(IntFlag):
    """Enum for bits in the run register."""

    ETHERNET_OVERRIDE = 0x01
    RUN_SIGNAL_ETH = 0x02
    RUN_SIGNAL_VXI = 0x04
    NO_FRAME_INC = 0x08
    STREAM_EMPTY_FRAMES = 0x10
    STATUS_RUNNING = 0x20
