"""Process worker events on the queue."""

import logging
import socket
import threading
from queue import Queue

from confluent_kafka import Producer

from kafka_dae_control.comms import set_board_response_ip
from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.worker_event_handlers import (
    handle_begin,
    handle_end,
    handle_frame_sync_sp_change,
    handle_hard_vetoes_change,
    handle_soft_vetoes_change,
)
from kafka_dae_control.worker_event_types import (
    BeginEvent,
    BlocksUpdateEvent,
    EndEvent,
    FrameSyncSelectChangeEvent,
    HardVetoesUpdateEvent,
    HardwareUpdateEvent,
    SetIPEvent,
    SoftVetoesUpdateEvent,
    WorkerEvent,
)

logger = logging.getLogger(__name__)


def process_worker_event(  # ruff:ignore[too-many-positional-arguments, too-many-arguments]
    queue: Queue[WorkerEvent],
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
        queue: the worker event queue which may be added to
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
                data.frame_sync_select_rbv = value.frame_sync_select
                data.hard_vetoes_array = value.hard_vetoes
            case BlocksUpdateEvent(value):
                data.blocks = value
            case BeginEvent(done_event=done_event):
                handle_begin(config, data, producer, sock, sock_lock, done_event, queue)
            case EndEvent(done_event=done_event):
                handle_end(config, data, producer, sock, sock_lock, done_event, queue)
            case FrameSyncSelectChangeEvent(value=value, done_event=done_event):
                handle_frame_sync_sp_change(value, config, data, sock, sock_lock, done_event)
            case SetIPEvent():
                set_board_response_ip(config, sock, sock_lock)
            case SoftVetoesUpdateEvent(value=value, done_event=done_event):
                handle_soft_vetoes_change(
                    value=value, config=config, data=data, producer=producer, done_event=done_event
                )
            case HardVetoesUpdateEvent(value=value, done_event=done_event):
                handle_hard_vetoes_change(
                    value=value,
                    config=config,
                    data=data,
                    producer=producer,
                    sock=sock,
                    sock_lock=sock_lock,
                    done_event=done_event,
                )
            case _:
                logger.error("Unknown event type: %s", worker_event)
    except Exception:
        logger.exception("Unhandled exception in handler thread: ")
