"""Worker event class for the worker thread to action."""

import logging
from abc import ABC
from dataclasses import dataclass

from kafka_dae_control.defaults import FrameSyncSelect, PeriodMode
from kafka_dae_control.event_with_value import EventWithValue

logger = logging.getLogger(__name__)


class SetIPEvent:
    """An event signalling to set the board's communication register to local IP."""


@dataclass
class BeginEvent:
    """An event signalling a begin."""

    done_event: EventWithValue[None]


@dataclass
class EndEvent:
    """An event signalling an end."""

    done_event: EventWithValue[None]


@dataclass
class FrameSyncSelectChangeEvent:
    """An event signalling a change in the frame sync select setpoint."""

    value: FrameSyncSelect
    done_event: EventWithValue[None]


@dataclass
class WorkerEventWithValue[T](ABC):
    """A worker event with a value field."""

    value: T


@dataclass
class HardwareUpdate:
    """a dataclass which contains the updated state of the hardware."""

    hw_running: bool
    frame_sync_select: FrameSyncSelect
    period_comp_current: int
    period_number_limit: int
    period_mode: PeriodMode


@dataclass
class HardwareUpdateEvent(WorkerEventWithValue[HardwareUpdate]):
    """An event signalling a hardware update."""


@dataclass
class BlocksUpdateEvent(WorkerEventWithValue[list[str]]):
    """An event signalling a blocks update."""


@dataclass
class CurrentPeriodSetEvent(WorkerEventWithValue[int]):
    """An event signalling a current period set."""

    done_event: EventWithValue[None]


@dataclass
class NumberOfPeriodsSetEvent(WorkerEventWithValue[int]):
    """An event signalling a number of periods set."""

    done_event: EventWithValue[None]


@dataclass
class PeriodModeSetEvent(WorkerEventWithValue[PeriodMode]):
    done_event: EventWithValue[None]


WorkerEvent = (
    SetIPEvent
    | BeginEvent
    | EndEvent
    | HardwareUpdateEvent
    | BlocksUpdateEvent
    | FrameSyncSelectChangeEvent
    | CurrentPeriodSetEvent
    | NumberOfPeriodsSetEvent
    | PeriodModeSetEvent
)
