"""Worker event class for the worker thread to action."""

import logging
from abc import ABC
from dataclasses import dataclass

import numpy as np
from numpy import typing as npt

from kafka_dae_control.defaults import FrameSyncSelect, PeriodMode
from kafka_dae_control.event_with_error import EventWithError

logger = logging.getLogger(__name__)


class SetIPEvent:
    """An event signalling to set the board's communication register to local IP."""


@dataclass
class DoneEvent:
    """A class containing an EventWithError instance."""

    done_event: EventWithError


@dataclass
class BeginEvent(DoneEvent):
    """An event signalling a begin."""


@dataclass
class EndEvent(DoneEvent):
    """An event signalling an end."""


@dataclass
class WorkerEventWithValue[T](ABC):
    """A worker event with a value field."""

    value: T


@dataclass
class FrameSyncSelectChangeEvent(WorkerEventWithValue[FrameSyncSelect], DoneEvent):
    """An event signalling a change in the frame sync select setpoint."""


@dataclass
class HardwareUpdate:
    """a dataclass which contains the updated state of the hardware."""

    hw_running: bool
    frame_sync_select: FrameSyncSelect
    hard_vetoes: int
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
class VetoesUpdateEvent(WorkerEventWithValue[npt.NDArray[np.uint8]], DoneEvent):
    """An event signalling the soft vetoes have been set."""


@dataclass
class CurrentPeriodSetEvent(WorkerEventWithValue[int], DoneEvent):
    """An event signalling the current period was set by a user."""


@dataclass
class NumberOfPeriodsSetEvent(WorkerEventWithValue[int], DoneEvent):
    """An event signalling the number of periods was set by a user."""


@dataclass
class PeriodModeSetEvent(WorkerEventWithValue[PeriodMode], DoneEvent):
    """An event signalling a period mode was set by a user."""


WorkerEvent = (
    SetIPEvent
    | BeginEvent
    | EndEvent
    | HardwareUpdateEvent
    | BlocksUpdateEvent
    | FrameSyncSelectChangeEvent
    | VetoesUpdateEvent
    | CurrentPeriodSetEvent
    | NumberOfPeriodsSetEvent
    | PeriodModeSetEvent
)
