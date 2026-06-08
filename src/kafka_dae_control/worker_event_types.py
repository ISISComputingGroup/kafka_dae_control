"""Worker event class for the worker thread to action."""

import logging
from abc import ABC
from dataclasses import dataclass

from kafka_dae_control.defaults import FrameSyncSelect
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


@dataclass
class HardwareUpdateEvent(WorkerEventWithValue[HardwareUpdate]):
    """An event signalling a hardware update."""


@dataclass
class BlocksUpdateEvent(WorkerEventWithValue[list[str]]):
    """An event signalling a blocks update."""


WorkerEvent = (
    SetIPEvent
    | BeginEvent
    | EndEvent
    | HardwareUpdateEvent
    | BlocksUpdateEvent
    | FrameSyncSelectChangeEvent
)
