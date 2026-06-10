"""Thread for polling the hardware and sending updates to the worker thread's queue."""

import logging
import socket
import threading
from queue import Queue
from threading import RLock
from time import sleep
from typing import Any, Never

from kafka_dae_control.comms import read
from kafka_dae_control.config import ControlConfig
from kafka_dae_control.defaults import (
    FrameSyncSelect,
    PeriodControlFlags,
    PeriodMode,
    Registers,
    RunRegister,
)
from kafka_dae_control.worker_event_types import HardwareUpdate, HardwareUpdateEvent, WorkerEvent

logger = logging.getLogger(__name__)


def hardware_poll_thread(
    config: ControlConfig,
    queue: Queue[WorkerEvent],
    sock: socket.SocketType,
    sock_lock: threading.RLock,
) -> Never:
    """Thread for polling the hardware and sending updates to the worker thread's queue.

    Args:
        config: the program's configuration
        queue: the worker thread queue to add updates to after polling hardware
        sock: the socket instance
        sock_lock: the lock to use when using the socket instance

    """
    while True:
        poll_hardware(config, queue, sock, sock_lock)
        sleep(config.poll_interval_s)


def poll_hardware(
    config: ControlConfig, queue: Queue[Any], sock: socket.SocketType, sock_lock: RLock
) -> None:
    """Poll the hardware and send updates to the worker thread's queue.

    Args:
        config: the program's configuration
        queue: the worker thread queue to add updates to after polling hardware
        sock: the socket instance
        sock_lock: the lock to use when using the socket instance

    """
    try:
        with sock_lock:
            running_register_readback = read(
                sock,
                config.board_ip,
                address=config.register_map[Registers.RUNNING_REGISTER],
                port=config.read_port,
            )

            frame_sync_select_raw_readback = read(
                sock,
                config.board_ip,
                address=config.register_map[Registers.FRAME_SYNC_SEL_REGISTER],
                port=config.read_port,
            )
            if frame_sync_select_raw_readback not in FrameSyncSelect:
                logger.error(
                    "Frame sync select not valid (%s), setting to unknown",
                    frame_sync_select_raw_readback,
                )
                frame_sync_select_readback = FrameSyncSelect.UNKNOWN
            else:
                frame_sync_select_readback = FrameSyncSelect(frame_sync_select_raw_readback)

            period_comp_current_readback = read(
                sock,
                config.board_ip,
                address=config.register_map[Registers.PERIOD_COMP_CURRENT],
                port=config.read_port,
            )

            period_number_limit_readback = read(
                sock,
                config.board_ip,
                address=config.register_map[Registers.PERIOD_NUMBER_LIMIT],
                port=config.read_port,
            )

            period_control_readback = read(
                sock,
                config.board_ip,
                address=config.register_map[Registers.PERIOD_CONTROL],
                port=config.read_port,
            )
            period_mode = PeriodMode(
                period_control_readback
                & ~int(
                    PeriodControlFlags.END_RUN_AT_END_OF_PERIOD_SEQUENCE
                    | PeriodControlFlags.END_RUN_AFTER_LAST_PERIOD_SEQUENCE
                )
            )

        queue.put(
            HardwareUpdateEvent(
                HardwareUpdate(
                    hw_running=running_register_readback & RunRegister.STATUS_RUNNING != 0,
                    frame_sync_select=FrameSyncSelect(frame_sync_select_readback),
                    period_comp_current=period_comp_current_readback,
                    period_number_limit=period_number_limit_readback,
                    period_mode=period_mode,
                )
            )
        )

    except Exception:
        logger.exception("Error occurred when polling hardware: ")
