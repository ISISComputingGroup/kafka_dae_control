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
    Registers,
    RunRegister,
)
from kafka_dae_control.worker_event_types import (
    HardwareUpdate,
    HardwareUpdateEvent,
    SetIPEvent,
    WorkerEvent,
)

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
    consecutive_comms_errors = 0
    while True:
        success = poll_hardware(config, queue, sock, sock_lock)

        if success:
            consecutive_comms_errors = 0
        else:
            consecutive_comms_errors += 1
            logger.debug(
                "%s comms errors in a row while polling hardware", consecutive_comms_errors
            )

        if (
            consecutive_comms_errors > 0
            and consecutive_comms_errors % config.resend_ip_after_connection_failures == 0
        ):
            # We've failed to communicate with the board several times in a row.
            # Maybe it has been power cycled and lost IP to respond to.
            logger.error(
                "Hardware polling failed %s times in a row. "
                "Attempting to resend local IP to streaming control board to recover. "
                "If the connection does not recover, the streaming control board may be offline.",
                consecutive_comms_errors,
            )
            queue.put(SetIPEvent())

        sleep(config.poll_interval_s)


def poll_hardware(
    config: ControlConfig, queue: Queue[Any], sock: socket.SocketType, sock_lock: RLock
) -> bool:
    """Poll the hardware and send updates to the worker thread's queue.

    Args:
        config: the program's configuration
        queue: the worker thread queue to add updates to after polling hardware
        sock: the socket instance
        sock_lock: the lock to use when using the socket instance

    Returns:
        True if the hardware poll was successful, False otherwise

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

        queue.put(
            HardwareUpdateEvent(
                HardwareUpdate(
                    hw_running=running_register_readback & RunRegister.STATUS_RUNNING != 0,
                    frame_sync_select=FrameSyncSelect(frame_sync_select_readback),
                )
            )
        )
        return True

    except Exception:
        logger.exception("Error occurred when polling hardware: ")
        return False
