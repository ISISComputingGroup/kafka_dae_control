"""Worker event class for the worker thread to action."""

import logging
import socket
import threading
from abc import ABC
from dataclasses import dataclass

from confluent_kafka import Producer

from kafka_dae_control.comms import set_board_response_ip
from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.event_with_value import EventWithValue
from kafka_dae_control.save_restore import save_file
from kafka_dae_control.worker_event_handlers import handle_begin, handle_end

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
class WorkerEventWithValue[T](ABC):
    """A worker event with a value field."""

    value: T


@dataclass
class HardwareUpdate:
    """a dataclass which contains the updated state of the hardware."""

    hw_running: bool


@dataclass
class HardwareUpdateEvent(WorkerEventWithValue[HardwareUpdate]):
    """An event signalling a hardware update."""


@dataclass
class BlocksUpdateEvent(WorkerEventWithValue[list[str]]):
    """An event signalling a blocks update."""


@dataclass
class UsersUpdateEvent(WorkerEventWithValue[str]):
    """An event signalling a users update."""


@dataclass
class TitleUpdateEvent(WorkerEventWithValue[str]):
    """An event signalling a title update."""


WorkerEvent = (
    SetIPEvent
    | BeginEvent
    | EndEvent
    | TitleUpdateEvent
    | UsersUpdateEvent
    | HardwareUpdateEvent
    | BlocksUpdateEvent
)


def process_worker_event(  # noqa: PLR0917, PLR0913
    worker_event: WorkerEvent,
    config: ControlConfig,
    data: Data,
    producer: Producer,
    sock: socket.SocketType,
    sock_lock: threading.RLock,
) -> None:
    """Process a worker event.

    This is the only part of the program which can mutate the data class.
    It is responsible for filtering the type of worker event and acting on it accordingly.

    Args:
        worker_event: the worker event to process
        config: the program's configuration options
        data: the data class containing the program's state
        producer: the Kafka producer
        sock: the socket instance
        sock_lock: the lock to use when using the socket instance

    """
    try:
        match worker_event:
            case HardwareUpdateEvent(value=value):
                data.running = value.hw_running
            case BlocksUpdateEvent(value):
                data.blocks = value
            case BeginEvent(done_event=done_event):
                handle_begin(config, data, producer, sock, sock_lock, done_event)
            case EndEvent(done_event=done_event):
                handle_end(config, data, producer, sock, sock_lock, done_event)
            case TitleUpdateEvent(value=value):
                data.title = value
                save_file(data, state_file=config.state_file)
            case UsersUpdateEvent(value=value):
                data.users = value
                save_file(data, state_file=config.state_file)
            case SetIPEvent():
                set_board_response_ip(config, sock, sock_lock)
            case _:
                logger.error("Unknown event type: %s", worker_event)
    except Exception:
        logger.exception("Unhandled exception in handler thread: ")
